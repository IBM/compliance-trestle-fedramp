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
"""Testing reading OSCAL SSP data for FedRAMP transformation."""

import pathlib
from typing import List, Tuple

import pytest

from trestle.common.const import NAMESPACE_FEDRAMP
from trestle.common.model_utils import ModelUtils
from trestle.core.generators import generate_sample_model
from trestle.oscal import ssp
from trestle.oscal.common import Property

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
from trestle_fedramp.core.ssp_reader import (ControlOrigination, FedrampControlDict, FedrampSSPReader)


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


def test_reader_control_origination(tmp_trestle_dir_with_ssp: Tuple[pathlib.Path, str]) -> None:
    """Test retrieving control origination values from the SSP."""
    tmp_trestle_dir, ssp_name = tmp_trestle_dir_with_ssp

    ssp_reader: FedrampSSPReader = FedrampSSPReader(tmp_trestle_dir)

    ssp_file_path = ModelUtils.get_model_path_for_name_and_class(tmp_trestle_dir, ssp_name, ssp.SystemSecurityPlan)
    assert ssp_file_path is not None
    ssp_control_dict: FedrampControlDict = ssp_reader.read_ssp_data(ssp_file_path)
    assert len(ssp_control_dict) > 0

    # Verify the control origination values for the implemented requirements.
    assert ssp_control_dict['AC-1'].control_origination == ['Service Provider System Specific']
    assert ssp_control_dict['AC-2'].control_origination == ['Shared (Service Provider and Customer Responsibility)']
    assert ssp_control_dict['AU-1'].control_origination == ['Service Provider Corporate']


def test_get_control_origination() -> None:
    """Test getting control origination from the implemented requirement."""
    ssp_reader: FedrampSSPReader = FedrampSSPReader(pathlib.Path.cwd())
    impl_req = generate_sample_model(ssp.ImplementedRequirement)
    impl_req.props = []
    impl_req.props.append(
        Property(name='control-origination', value='sp-corporate', ns='https://example.com')  # type: ignore
    )

    # This should be none because the namespace is not the FedRAMP namespace.
    assert ssp_reader._get_control_origination_values(impl_req) is None

    impl_req.props = []
    impl_req.props.append(
        Property(name='control-origination', value='sp-corporate', ns=NAMESPACE_FEDRAMP)  # type: ignore
    )

    # This should return the long name of the control origination value.
    assert ssp_reader._get_control_origination_values(impl_req) == ['Service Provider Corporate']
