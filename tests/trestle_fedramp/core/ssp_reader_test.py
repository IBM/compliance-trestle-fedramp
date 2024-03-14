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
from typing import Dict, Tuple

import pytest

from trestle.common.const import NAMESPACE_FEDRAMP
from trestle.common.model_utils import ModelUtils
from trestle.core.generators import generate_sample_model
from trestle.oscal import ssp
from trestle.oscal.common import Property

from trestle_fedramp.core.ssp_reader import FedrampControlDict, FedrampSSPReader


def test_reader_ssp_data(tmp_trestle_dir_with_ssp: Tuple[pathlib.Path, str]) -> None:
    """Test retrieving information from an OSCAL SSP for FedRAMP."""
    tmp_trestle_dir, ssp_name = tmp_trestle_dir_with_ssp
    ssp_file_path = ModelUtils.get_model_path_for_name_and_class(tmp_trestle_dir, ssp_name, ssp.SystemSecurityPlan)
    assert ssp_file_path is not None

    ssp_reader: FedrampSSPReader = FedrampSSPReader(tmp_trestle_dir, ssp_file_path)

    ssp_control_dict: FedrampControlDict = ssp_reader.read_ssp_data()
    assert len(ssp_control_dict) > 0

    # Verify the control origination values for the implemented requirements.
    assert ssp_control_dict['AC-1'].control_origination == ['Service Provider System Specific']
    assert ssp_control_dict['AC-2'].control_origination == ['Shared (Service Provider and Customer Responsibility)']
    assert ssp_control_dict['AU-1'].control_origination == ['Service Provider Corporate']

    # Verify status
    assert ssp_control_dict['AC-1'].implementation_status == 'Planned'
    assert ssp_control_dict['AC-2'].implementation_status == 'Implemented'
    assert ssp_control_dict['AU-1'].implementation_status == 'Partially Implemented'

    # Verify the control implementation descriptions
    responses_dict: Dict[str, str] = ssp_control_dict['AC-1'].control_implementation_description
    assert len(responses_dict) == 2
    assert '' not in responses_dict
    assert 'a' in responses_dict
    assert 'b' in responses_dict

    assert responses_dict['a'] == (
        'This System: Describe how Part a is satisfied within the system.\n'
        '\n[EXAMPLE]Policies: Describe how this policy component satisfies part a.'
    )

    assert responses_dict['b'] == (
        'This System: Describe how Part b is satisfied within the system for a component.\n'
        '\n[EXAMPLE]Procedures: Describe how Part b is satisfied within the system for '
        'another component.'
    )


def test_get_control_origination() -> None:
    """Test getting control origination from the implemented requirement."""
    impl_req = generate_sample_model(ssp.ImplementedRequirement)
    impl_req.props = []
    impl_req.props.append(
        Property(name='control-origination', value='sp-corporate', ns='https://example.com')  # type: ignore
    )

    # This should be none because the namespace is not the FedRAMP namespace.
    assert FedrampSSPReader.get_control_origination_values(impl_req) is None

    impl_req.props = []
    impl_req.props.append(
        Property(name='control-origination', value='sp-corporate', ns=NAMESPACE_FEDRAMP)  # type: ignore
    )

    # This should return the long name of the control origination value.
    assert FedrampSSPReader.get_control_origination_values(impl_req) == ['Service Provider Corporate']


# Negative test cases for implementation status


def test_get_implementation_status_failures() -> None:
    """Testing failure cases for getting the implementation status."""
    # Wrong namespace
    impl_req = generate_sample_model(ssp.ImplementedRequirement)
    impl_req.props = []
    impl_req.props.append(
        Property(name='implementation-status', value='planned', ns='https://example.com')  # type: ignore
    )

    assert FedrampSSPReader.get_implementation_status(impl_req) is None

    # Too many implementation status properties
    impl_req.props = []
    impl_req.props.extend(
        [
            Property(name='implementation-status', value='planned', ns=NAMESPACE_FEDRAMP),  # type: ignore
            Property(name='implementation-status', value='implemented', ns=NAMESPACE_FEDRAMP)  # type: ignore
        ]
    )
    impl_req.control_id = 'ac-1'

    with pytest.raises(ValueError, match='Multiple implementation status properties found for control id .*'):
        FedrampSSPReader.get_implementation_status(impl_req)

    # Invalid implementation status value
    impl_req.props = []
    impl_req.props.append(
        Property(name='implementation-status', value='invalid', ns=NAMESPACE_FEDRAMP)  # type: ignore
    )

    with pytest.raises(ValueError, match='Invalid implementation status value: invalid. Use one of .*'):
        FedrampSSPReader.get_implementation_status(impl_req)
