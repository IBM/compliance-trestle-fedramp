# Copyright (c) 2024 IBM Corp. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
Read and prepare OSCAL SSP information for template.

The OSCAL SSP is stored in the FedRAMPControlDict in a way that
would be expected by the FedRAMP Template without knowledge of the
template structure.
Control ID -> Labels
Control Origination Property -> Control Origination String Value(s)
Control Implementation Description -> Dictionary of response for each part
"""

import pathlib
from dataclasses import dataclass
from typing import Dict, List, Optional

from trestle.common.common_types import TypeWithByComps
from trestle.common.const import CONTROL_ORIGINATION, IMPLEMENTATION_STATUS, NAMESPACE_FEDRAMP
from trestle.common.list_utils import as_list
from trestle.common.load_validate import load_validate_model_path
from trestle.core.catalog.catalog_interface import CatalogInterface
from trestle.core.control_interface import ControlInterface
from trestle.core.profile_resolver import ProfileResolver
from trestle.oscal.catalog import Catalog
from trestle.oscal.ssp import ImplementedRequirement, SystemSecurityPlan

from trestle_fedramp.const import FEDRAMP_IS_SHORT_TO_LONG_NAME
from trestle_fedramp.core.fedramp_values import ControlOrigination


@dataclass
class FedrampSSPData:
    """
    Class to hold the OSCAL SSP data for FedRAMP SSP conversion.

    Fields:
        control_implementation_description: Dictionary of control implementation description by control part
        control_origination: Top level control origination values list

    Notes: To conform to the convention used by Trestle to denote information at
    the control level, will be '' in the control_implementation_description dictionary.
    """

    control_implementation_description: Dict[str, str]
    control_origination: Optional[List[str]]
    implementation_status: Optional[str]


# FedRAMP data by control label
FedrampControlDict = Dict[str, FedrampSSPData]


class FedrampSSPReader:
    """
    Read OSCAL SSP information for FedRAMP SSP conversion.

    Notes: This class provided an opinionated way to read the OSCAL SSP and
    prepare the data for the FedRAMP Template.
    """

    def __init__(
        self,
        trestle_root: pathlib.Path,
        ssp_path: pathlib.Path,
    ) -> None:
        """
        Initialize FedRAMP SSP reader.

        Args:
            trestle_root: Trestle project root path.
            ssp_path: Path to the OSCAL SSP.
        """
        self._root = trestle_root
        self._ssp: SystemSecurityPlan = load_validate_model_path(self._root, ssp_path)  # type: ignore

        profile_resolver = ProfileResolver()
        resolved_catalog: Catalog = profile_resolver.get_resolved_profile_catalog(
            self._root,
            self._ssp.import_profile.href,
            block_params=False,
            params_format='[.]',
            show_value_warnings=True,
        )
        catalog_interface = CatalogInterface(resolved_catalog)

        # Setup dictionaries for control and statement mapping
        self._control_labels_by_id: Dict[str, str] = self._load_profile_info(catalog_interface=catalog_interface)
        self._statement_labels_by_id: Dict[str, Dict[str, str]] = catalog_interface.get_statement_part_id_map(False)

        # Setup dictionaries for component title. Only include components that are in the include_components list.
        self._comp_titles_by_uuid: Dict[str, str] = self._get_component_info()

    def _get_component_info(self) -> Dict[str, str]:
        """Get the component information mapped to UUID."""
        return {component.uuid: component.title for component in as_list(self._ssp.system_implementation.components)}

    def _load_profile_info(self, catalog_interface: CatalogInterface) -> Dict[str, str]:
        """Load the profile and store the control by label."""
        controls_by_label: Dict[str, str] = {}

        for control in catalog_interface.get_all_controls_from_dict():
            label = ControlInterface.get_label(control)
            if label:
                controls_by_label[control.id] = label
        return controls_by_label

    def read_ssp_data(self) -> FedrampControlDict:
        """Read the ssp from file and return the data for the FedRAMP Template."""
        control_dict: FedrampControlDict = {}

        for implemented_requirement in as_list(self._ssp.control_implementation.implemented_requirements):
            control_id = implemented_requirement.control_id
            label = self._control_labels_by_id.get(control_id, '')
            if label:
                control_origination: Optional[List[str]] = self.get_control_origination_values(implemented_requirement)
                control_implementation_description: Dict[
                    str, str] = self.get_control_implementation_description(implemented_requirement)
                implementation_status: Optional[str] = self.get_implementation_status(implemented_requirement)
                control_dict[label] = FedrampSSPData(
                    control_origination=control_origination,
                    control_implementation_description=control_implementation_description,
                    implementation_status=implementation_status
                )
        return control_dict

    def get_control_implementation_description(self, implemented_requirement: ImplementedRequirement) -> Dict[str, str]:
        """Get the control implementation description."""
        control_implementation_description: Dict[str, str] = {}

        response_text: str = self._get_responses_from_by_comp(implemented_requirement)
        if response_text:
            control_implementation_description[''] = response_text

        statement_labels = self._statement_labels_by_id.get(implemented_requirement.control_id, {})

        for statement in as_list(implemented_requirement.statements):
            statement_label = statement_labels.get(statement.statement_id, '')
            # Remove ending period from statement label to ensure consistency
            statement_label = statement_label[:-1] if statement_label and statement_label.endswith(
                '.'
            ) else statement_label
            if statement_label:
                response_text = self._get_responses_from_by_comp(statement)
                if response_text:
                    control_implementation_description[statement_label] = response_text

        return control_implementation_description

    def _get_responses_from_by_comp(self, type_with_bycomp: TypeWithByComps) -> str:
        """Get the control implementation description for each by component."""
        control_response_text_list: List[str] = [
            f"{self._comp_titles_by_uuid.get(by_component.component_uuid, '')}: {by_component.description}"
            for by_component in as_list(type_with_bycomp.by_components)
            if by_component.description
        ]
        return '\n\n'.join(control_response_text_list)

    @staticmethod
    def get_implementation_status(implemented_requirement: ImplementedRequirement) -> Optional[str]:
        """Get the implementation status."""
        prop_values: List[str] = [
            prop.value
            for prop in as_list(implemented_requirement.props)
            if prop.name == IMPLEMENTATION_STATUS and prop.ns == NAMESPACE_FEDRAMP
        ]

        if not prop_values:
            return None
        elif len(prop_values) > 1:
            raise ValueError(
                'Multiple implementation status properties found for control id '
                f'{implemented_requirement.control_id} implemented requirement'
            )

        implementation_status_value = prop_values[0]

        if implementation_status_value not in FEDRAMP_IS_SHORT_TO_LONG_NAME:
            raise ValueError(
                f'Invalid implementation status value: {implementation_status_value}. '
                f'Use one of {list(FEDRAMP_IS_SHORT_TO_LONG_NAME.keys())}'
            )

        return FEDRAMP_IS_SHORT_TO_LONG_NAME[implementation_status_value]

    @staticmethod
    def get_control_origination_values(implemented_requirement: ImplementedRequirement) -> Optional[List[str]]:
        """
        Check for the control origination property and return the value.

        Notes:
            This is checking for the FedRAMP specific property in the OSCAL SSP,
            not the OSCAL control origination values.
        """
        prop_values: List[str] = [
            prop.value
            for prop in as_list(implemented_requirement.props)
            if prop.name == CONTROL_ORIGINATION and prop.ns == NAMESPACE_FEDRAMP
        ]

        if not prop_values:
            return None

        return ControlOrigination.get_long_names(prop_values)
