# -*- mode:python; coding:utf-8 -*-
#
# Copyright (c) 2021 IBM Corp. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Common fixtures."""

import argparse
import os
import pathlib
import sys
from typing import Iterator, Tuple

from docx import Document  # type: ignore
from docx.document import Document as DocxDocument  # type: ignore

import pytest
from pytest import MonkeyPatch

from tests import test_utils

from trestle.cli import Trestle
from trestle.common.err import TrestleError
from trestle.core.commands.import_ import ImportCmd

from trestle_fedramp import const
from trestle_fedramp.core.baselines import BaselineLevel
from trestle_fedramp.core.ssp_reader import FedrampControlDict, FedrampSSPData


@pytest.fixture(scope='function')
def tmp_trestle_dir(tmp_path: pathlib.Path, monkeypatch: MonkeyPatch) -> Iterator[pathlib.Path]:
    """Create and return a new trestle project directory using std tmp_path fixture.

    Note that this fixture relies on the 'trestle init' command and therefore may
    misbehave if there are errors in trestle init, perhaps in spite of the try block.
    """
    pytest_cwd = pathlib.Path.cwd()
    os.chdir(tmp_path)
    testargs = ['trestle', 'init']
    monkeypatch.setattr(sys, 'argv', testargs)
    try:
        Trestle().run()
    except BaseException as e:
        raise TrestleError(f'Initialization failed for temporary trestle directory: {e}.')
    else:
        yield tmp_path
    finally:
        os.chdir(pytest_cwd)


@pytest.fixture(scope='function')
def tmp_trestle_dir_with_ssp(tmp_path: pathlib.Path, monkeypatch: MonkeyPatch) -> Iterator[Tuple[pathlib.Path, str]]:
    """Create initialized trestle workspace and import the model into it."""
    pytest_cwd = pathlib.Path.cwd()
    model_name = 'ssp'
    file_path = test_utils.JSON_TEST_DATA_PATH / test_utils.TEST_SSP_JSON
    os.chdir(tmp_path)
    testargs = ['trestle', 'init']
    monkeypatch.setattr(sys, 'argv', testargs)
    try:
        Trestle().run()
        i = ImportCmd()
        args = argparse.Namespace(
            trestle_root=tmp_path, file=str(file_path), output=model_name, verbose=1, regenerate=False
        )
        assert i._run(args) == 0
    except Exception as e:
        raise TrestleError(f'Error creating trestle workspace with ssp: {e}')
    else:
        yield (tmp_path, model_name)
    finally:
        os.chdir(pytest_cwd)


@pytest.fixture(scope='function')
def docx_document() -> Iterator[DocxDocument]:
    """Return a docx document."""
    template = pathlib.Path(BaselineLevel.get_template('high')).resolve()
    with open(template, 'rb') as file:
        document: DocxDocument = Document(file)
    yield document


@pytest.fixture(scope='function')
def test_ssp_control_dict() -> Iterator[FedrampControlDict]:
    """Return a dictionary of control data."""
    control_dict: FedrampControlDict = {
        'AC-1': FedrampSSPData({'a': 'Part a example for AC-1'}, control_origination=None, implementation_status=None),
        'AC-2(1)': FedrampSSPData(
            {'': 'Overall description for AC-2(1)'},
            control_origination=[const.FEDRAMP_SP_SYSTEM],
            implementation_status=const.FEDRAMP_PLANNED
        ),
        'AC-20': FedrampSSPData(
            {
                'a': 'Part a example for AC-20',
                'b': 'Part b example for AC-20',
            },
            control_origination=[const.FEDRAMP_SP_CORPORATE, const.FEDRAMP_INHERITED],
            implementation_status=const.FEDRAMP_PARTIAL
        ),
        'CM-6': FedrampSSPData(
            {
                'a': 'Part a example for CM-6',
                'b': 'Part b example for CM-6',
                'c': 'Part c example for CM-6',
                'd': 'Part d example for CM-6',
            },
            control_origination=[const.FEDRAMP_SHARED],
            implementation_status=const.FEDRAMP_IMPLEMENTED
        )
    }
    yield control_dict
