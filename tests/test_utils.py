# -*- mode:python; coding:utf-8 -*-

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
"""Test utils module."""

import pathlib

JSON_FEDRAMP_SAR_PATH = pathlib.Path('fedramp-source/dist/content/rev5/templates/sar/json/').resolve()
JSON_FEDRAMP_SAR_NAME = 'FedRAMP-SAR-OSCAL-Template.json'
JSON_FEDRAMP_SSP_PATH = pathlib.Path('fedramp-source/dist/content/rev5/templates/ssp/json/').resolve()
JSON_FEDRAMP_SSP_NAME = 'FedRAMP-SSP-OSCAL-Template.json'
XML_FEDRAMP_SSP_PATH = pathlib.Path('fedramp-source/dist/content/rev5/templates/ssp/xml/').resolve()
XML_FEDRAMP_SSP_NAME = 'FedRAMP-SSP-OSCAL-Template.xml'
JSON_TEST_DATA_PATH = pathlib.Path('tests/data/json/').resolve()
TEST_SSP_JSON = 'simplified_fedramp_ssp_template.json'
