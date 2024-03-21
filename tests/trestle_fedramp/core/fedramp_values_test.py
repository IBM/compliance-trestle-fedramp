# -*- mode:python; coding:utf-8 -*-

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
"""Tests for FedRAMP values translation."""

from typing import List

import pytest

from trestle_fedramp.const import (
    FEDRAMP_CUST_CONFIGURED,
    FEDRAMP_HYBRID,
    FEDRAMP_INHERITED,
    FEDRAMP_SHARED,
    FEDRAMP_SHORT_CUST_CONFIGURED,
    FEDRAMP_SHORT_INHERITED,
    FEDRAMP_SHORT_SP_CORPORATE,
    FEDRAMP_SHORT_SP_SYSTEM,
    FEDRAMP_SP_CORPORATE
)
from trestle_fedramp.core.fedramp_values import ControlOrigination


def test_control_origination() -> None:
    """Test valid and invalid control origination values."""
    # Validate combinations of control origination values.
    long_names: List[str] = ControlOrigination.get_long_names([FEDRAMP_SHORT_SP_CORPORATE, FEDRAMP_SHORT_SP_SYSTEM])
    assert long_names == [FEDRAMP_HYBRID]

    # Shared should take precedence over the other values.
    long_names = ControlOrigination.get_long_names(
        [FEDRAMP_SHORT_SP_CORPORATE, FEDRAMP_SHORT_SP_SYSTEM, FEDRAMP_SHORT_CUST_CONFIGURED]
    )
    assert long_names == [FEDRAMP_SHARED]

    # Combination with inherited
    long_names = ControlOrigination.get_long_names(
        [FEDRAMP_SHORT_SP_CORPORATE, FEDRAMP_SHORT_CUST_CONFIGURED, FEDRAMP_SHORT_INHERITED]
    )

    assert len(long_names) == 2
    assert FEDRAMP_SHARED in long_names
    assert FEDRAMP_INHERITED in long_names

    # Neither shared nor hybrid
    long_names = ControlOrigination.get_long_names([FEDRAMP_SHORT_INHERITED, FEDRAMP_SHORT_CUST_CONFIGURED])

    assert len(long_names) == 2
    assert FEDRAMP_INHERITED in long_names
    assert FEDRAMP_CUST_CONFIGURED in long_names

    # Single value
    long_names = ControlOrigination.get_long_names([FEDRAMP_SHORT_SP_CORPORATE])
    assert long_names == [FEDRAMP_SP_CORPORATE]

    # Assert that if the input is not a valid control origination value, it raises a ValueError.
    with pytest.raises(ValueError, match='Invalid control origination value: invalid. Use one of .*'):
        ControlOrigination.get_long_names([FEDRAMP_SHORT_CUST_CONFIGURED, 'invalid'])

    # Validate error for empty list.
    with pytest.raises(ValueError, match='Control origination values are empty'):
        ControlOrigination.get_long_names([])
