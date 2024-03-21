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
template structure/format.
Control ID -> Labels
Control Origination Property -> Control Origination String Value(s)
Control Implementation Description -> Dictionary of response for each part
Control Parameters -> Dictionary of parameter values for each part and location in the prose to match the
expected FedRAMP values
"""

import logging
import pathlib
import re
from dataclasses import dataclass
from typing import Dict, List, Optional

from trestle.common.common_types import TypeWithByComps
from trestle.common.const import CONTROL_ORIGINATION, IMPLEMENTATION_STATUS, NAMESPACE_FEDRAMP, STATEMENT
from trestle.common.err import TrestleError
from trestle.common.list_utils import as_filtered_list, as_list
from trestle.common.load_validate import load_validate_model_path
from trestle.core.catalog.catalog_interface import CatalogInterface
from trestle.core.control_interface import ControlInterface, ParameterRep
from trestle.core.profile_resolver import ProfileResolver
from trestle.oscal import common
from trestle.oscal.catalog import Catalog, Control
from trestle.oscal.ssp import ImplementedRequirement, SetParameter, SystemSecurityPlan

from trestle_fedramp.const import FEDRAMP_IS_SHORT_TO_LONG_NAME
from trestle_fedramp.core.fedramp_values import ControlOrigination

logger = logging.getLogger(__name__)


@dataclass
class FedrampSSPData:
    """
    Class to hold the OSCAL SSP data for FedRAMP SSP conversion.

    Fields:
        control_implementation_description: Dictionary of control implementation description by control part
        parameters: Dictionary of parameters by control part and prose placement in the SSP (e.g AC(1)(a))
        control_origination: Top level control origination values list
        implementation_status: Implementation status value

    Notes: To conform to the convention used by Trestle to denote information at
    the control level, will be '' in the control_implementation_description and parameters dictionaries.
    """

    control_implementation_description: Dict[str, str]
    parameters: Dict[str, str]
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
            param_rep=ParameterRep.LEAVE_MOUSTACHE,
        )
        self.catalog_interface = CatalogInterface(resolved_catalog)

        # Setup dictionaries for control and statement mapping
        self._control_labels_by_id: Dict[str, str] = self._load_label_info()
        self._statement_labels_by_id: Dict[str, Dict[str,
                                                     str]] = self.catalog_interface.get_statement_part_id_map(False)

        # Setup dictionaries for component title. Only include components that are in the include_components list.
        self._comp_titles_by_uuid: Dict[str, str] = self._get_component_info()

    def _get_component_info(self) -> Dict[str, str]:
        """Get the component information mapped to UUID."""
        return {component.uuid: component.title for component in as_list(self._ssp.system_implementation.components)}

    def _load_label_info(self) -> Dict[str, str]:
        """Load the profile and store the control by label."""
        controls_by_label: Dict[str, str] = {}

        for control in self.catalog_interface.get_all_controls_from_dict():
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
                parameters: Dict[str, str] = self.get_control_parameters(implemented_requirement)
                control_dict[label] = FedrampSSPData(
                    control_origination=control_origination,
                    control_implementation_description=control_implementation_description,
                    implementation_status=implementation_status,
                    parameters=parameters
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
        control_response_text_list: List[str] = [  # type: ignore
            f"{self._comp_titles_by_uuid.get(by_component.component_uuid, '')}: {by_component.description}"
            for by_component in as_list(type_with_bycomp.by_components)  # type: ignore
            if by_component.description
        ]
        return '\n\n'.join(control_response_text_list)

    def get_control_parameters(self, implemented_requirement: ImplementedRequirement) -> Dict[str, str]:
        """Get the control parameters."""
        parameters: Dict[str, str] = {}
        control: Optional[Control] = self.catalog_interface.get_control(implemented_requirement.control_id)
        if control is None:
            raise TrestleError(f'Control {implemented_requirement.control_id} not found in the catalog')

        control_parameters = ControlInterface.get_control_param_dict(control, False)
        # Replace all of the parameter with the resolved values from the catalog, profile, or set parameters
        for param_id, param in control_parameters.items():
            logger.debug(f'Using parameter key {param_id} for control {implemented_requirement.control_id}')
            # Set parameters can be set at the by_comp level, but only supporting at the control level
            # for now since that is used in compliance-trestle during
            # SSP markdown editing.
            if implemented_requirement.set_parameters:
                self._update_param(param, implemented_requirement.set_parameters)
            param_str = ControlInterface.param_to_str(param, ParameterRep.VALUE_OR_EMPTY_STRING)
            parameters[param_id] = param_str if param_str else ''

        parameters_by_part_name: Dict[str, str] = {}
        label = self._control_labels_by_id.get(implemented_requirement.control_id, '')
        for part in as_filtered_list(control.parts, lambda p: p.name == STATEMENT):
            self._get_parameters_by_part(part, label, parameters, parameters_by_part_name)
        return parameters_by_part_name

    def _update_param(self, parameter: common.Parameter, set_params: List[SetParameter]) -> None:
        """Update the parameter value from the implemented requirement."""
        for set_param in as_filtered_list(set_params, lambda p: p.param_id == parameter.id):
            if set_param.values:
                logger.debug(f'Updating parameter {parameter.id} with values {set_param.values}')
                parameter.values = set_param.values
                return

    def _get_parameters_by_part(
        self, part: common.Part, label: str, parameters: Dict[str, str], parameters_by_part_name: Dict[str, str]
    ) -> None:
        """
        Get the control parameters for a specific part.

        Notes:
            Map them to the control part and prose location in the way that is expected by the FedRAMP template
            The pattern is 'control(part)(subpart) or 'control(part)'. If there are multiple associated parameters
            they are separated list in order with a dash in the key (e.g. AT-3(b)-1).
        """
        part_label = ControlInterface.get_label(part)
        part_label = part_label[:-1] if part_label and part_label.endswith('.') else part_label
        if part_label:
            label = f'{label}({part_label})'
        if part.prose:
            params_ids = self.find_params_in_text(part.prose)
            if len(params_ids) == 1:
                parameters_by_part_name[label] = parameters.get(params_ids[0], '')
            elif params_ids:
                for i, param_id in enumerate(params_ids):
                    parameters_by_part_name[f'{label}-{i+1}'] = parameters.get(param_id, '')
        for subpart in as_list(part.parts):
            self._get_parameters_by_part(subpart, label, parameters, parameters_by_part_name)

    def find_params_in_text(self, text: str) -> List[str]:
        """Find the parameters in the text."""
        # Logic adapted from
        # https://github.com/oscal-compass/compliance-trestle/blob/main/trestle/core/control_interface.py#L836
        param_ids: List[str] = []
        staches: List[str] = re.findall(r'{{.*?}}', text)
        if not staches:
            return param_ids
        # now have list of all staches including braces, e.g. ['{{foo}}', '{{bar}}']
        # clean the staches so they just have the param ids
        for stache in staches:
            # remove braces so these are just param_ids but may have extra chars
            stache_contents = stache[2:(-2)]
            param_id = stache_contents.replace('insert: param,', '').strip()
            param_ids.append(param_id)
        return param_ids

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
