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
would be expected by the FedRAMP Template.
Control ID -> Labels
Control Origination Property -> Control Origination String Value
"""

import pathlib
from dataclasses import dataclass
from typing import Dict, List, Optional, Set

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
    """Class to hold the OSCAL SSP data for FedRAMP SSP conversion."""

    control_origination: Optional[List[str]]


# FedRAMP data by control
FedrampControlDict = Dict[str, FedrampSSPData]


class FedrampSSPReader:
    """
    Read OSCAL SSP information for FedRAMP SSP conversion.

    Notes: This class provided an opinionated way to read the OSCAL SSP and
    prepare the data for the FedRAMP Template.
    """

    def __init__(self, trestle_root: pathlib.Path) -> None:
        """Initialize FedRAMP SSP reader."""
        self._root = trestle_root

    def read_ssp_data(self, ssp_path: pathlib.Path) -> FedrampControlDict:
        """Read the ssp from file and return the data for the FedRAMP Template."""
        control_dict: FedrampControlDict = {}
        ssp_data: SystemSecurityPlan = load_validate_model_path(self._root, ssp_path)  # type: ignore

        controls_by_label: Dict[str, str] = self.load_profile_info(ssp_data.import_profile.href)

        for implemented_requirement in as_list(ssp_data.control_implementation.implemented_requirements):
            control_id = implemented_requirement.control_id
            label = controls_by_label.get(control_id, '')
            if label:
                control_origination: Optional[List[str]] = self._get_control_origination_values(implemented_requirement)
                control_dict[label] = FedrampSSPData(control_origination=control_origination)
        return control_dict

    def load_profile_info(self, profile_path: str) -> Dict[str, str]:
        """Load the profile and store the control by label."""
        controls_by_label: Dict[str, str] = {}
        profile_resolver = ProfileResolver()
        resolved_catalog: Catalog = profile_resolver.get_resolved_profile_catalog(
            self._root,
            profile_path,
            block_params=False,
            params_format='[.]',
            show_value_warnings=True,
        )

        for control in CatalogInterface(resolved_catalog).get_all_controls_from_dict():
            label = ControlInterface.get_label(control)
            if label:
                controls_by_label[control.id] = label
        return controls_by_label

    def _get_control_origination_values(self, implemented_requirement: ImplementedRequirement) -> Optional[List[str]]:
        """
        Check for the control origination property and return the value.

        Notes:
            This is checking for the FedRAMP specific property in the OSCAL SSP,
            not the OSCAL control origination values.
        """
        prop_values: List[str] = []
        for prop in as_list(implemented_requirement.props):
            if prop.name == CONTROL_ORIGINATION and prop.ns == NAMESPACE_FEDRAMP:
                prop_values.append(prop.value)

        if not prop_values:
            return None

        return ControlOrigination.get_long_names(prop_values)
