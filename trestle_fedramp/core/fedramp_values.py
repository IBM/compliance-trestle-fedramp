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
"""Classes for translating OSCAL values FedRAMP values to document values."""

from typing import List, Set

from trestle_fedramp.const import (
    FEDRAMP_CO_SHORT_TO_LONG_NAME,
    FEDRAMP_CO_VALUES,
    FEDRAMP_HYBRID,
    FEDRAMP_SHARED,
    FEDRAMP_SHORT_CUST_CONFIGURED,
    FEDRAMP_SHORT_CUST_PROVIDED,
    FEDRAMP_SHORT_INHERITED,
    FEDRAMP_SHORT_SP_CORPORATE,
    FEDRAMP_SHORT_SP_SYSTEM
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
            fedramp_inherited_long = FEDRAMP_CO_SHORT_TO_LONG_NAME[FEDRAMP_SHORT_INHERITED]
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
                long_names.add(FEDRAMP_CO_SHORT_TO_LONG_NAME[value])

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
