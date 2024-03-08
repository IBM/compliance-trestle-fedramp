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
from typing import Dict, List, Optional, Set

from trestle.common.common_types import TypeWithByComps
from trestle.common.const import CONTROL_ORIGINATION, NAMESPACE_FEDRAMP
from trestle.common.list_utils import as_list
from trestle.common.load_validate import load_validate_model_path
from trestle.core.catalog.catalog_interface import CatalogInterface
from trestle.core.control_interface import ControlInterface
from trestle.core.profile_resolver import ProfileResolver
from trestle.oscal.catalog import Catalog
from trestle.oscal.ssp import ImplementedRequirement, SystemSecurityPlan

from trestle_fedramp.const import (
    FEDRAMP_CO_VALUES,
    FEDRAMP_HYBRID,
    FEDRAMP_SHARED,
    FEDRAMP_SHORT_CUST_CONFIGURED,
    FEDRAMP_SHORT_CUST_PROVIDED,
    FEDRAMP_SHORT_INHERITED,
    FEDRAMP_SHORT_SP_CORPORATE,
    FEDRAMP_SHORT_SP_SYSTEM,
    FEDRAMP_SHORT_TO_LONG_NAME,
)


class ControlOrigination:
    """Represents the FedRAMP control origination mapping per FedRAMP validation rules."""

    customer_sp: List[str] = [FEDRAMP_SHORT_CUST_CONFIGURED, FEDRAMP_SHORT_CUST_PROVIDED]
    provider_sp: List[str] = [FEDRAMP_SHORT_SP_CORPORATE, FEDRAMP_SHORT_SP_SYSTEM]

    @classmethod
    def get_long_names(cls, control_origination_values: List[str]) -> List[str]:
        """
        Get the long name for control origination value(s).

        Args:
            control_origination_values: List of control origination values.

        Returns:
            Long names for the control origination value or combination of values.

        Notes:
            The input values can be a single or set control origination properties values.
            Any set with sp-corporate and sp-system is considered as hybrid and any set with customer
            and specific system is considered as shared.

        """
        # Validate the input values
        if not control_origination_values:
            raise ValueError('Control origination values are empty')

        for value in control_origination_values:
            if value not in FEDRAMP_CO_VALUES:
                raise ValueError(f'Invalid control origination value: {value}. Use one of {FEDRAMP_CO_VALUES}')

        long_names: Set[str] = set()

        # Inherited can be combined with other values
        if FEDRAMP_SHORT_INHERITED in control_origination_values:
            fedramp_inherited_long = FEDRAMP_SHORT_TO_LONG_NAME[FEDRAMP_SHORT_INHERITED]
            long_names.add(fedramp_inherited_long)

        # If the values are in the provider and customer set, then it is shared
        # This would encompass hybrid if both service provider values are present
        # with customer values.
        if cls.is_shared(control_origination_values):
            long_names.add(FEDRAMP_SHARED)
        elif cls._is_hybrid(control_origination_values):
            long_names.add(FEDRAMP_HYBRID)
        else:
            # Add individual long names if they don't belong to shared or hybrid
            for value in control_origination_values:
                long_names.add(FEDRAMP_SHORT_TO_LONG_NAME[value])

        return list(long_names)

    @staticmethod
    def _is_hybrid(control_origination_values: List[str]) -> bool:
        """Check if the control origination values are hybrid."""
        return (
            FEDRAMP_SHORT_SP_CORPORATE in control_origination_values
            and FEDRAMP_SHORT_SP_SYSTEM in control_origination_values
        )

    @classmethod
    def is_shared(cls, control_origination_values: List[str]) -> bool:
        """Check if the control origination values are shared."""
        control_origination_set: Set[str] = set(control_origination_values)

        # If the values contain both customer and provider values, then it is shared
        if control_origination_set.intersection(cls.provider_sp) and control_origination_set.intersection(
                cls.customer_sp):
            return True

        return False


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
                control_dict[label] = FedrampSSPData(
                    control_origination=control_origination,
                    control_implementation_description=control_implementation_description
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
