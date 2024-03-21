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
from typing import Dict, List, Tuple

from docx.table import Table, _Cell  # type: ignore
from docx.text.paragraph import Paragraph  # type: ignore

from trestle_fedramp import const
from trestle_fedramp.core.docx_helper import ControlImplementationDescriptions, ControlSummaries
from trestle_fedramp.core.ssp_reader import FedrampSSPData

JSON_FEDRAMP_SAR_PATH = pathlib.Path('fedramp-source/dist/content/rev5/templates/sar/json/').resolve()
JSON_FEDRAMP_SAR_NAME = 'FedRAMP-SAR-OSCAL-Template.json'
JSON_FEDRAMP_SSP_PATH = pathlib.Path('fedramp-source/dist/content/rev5/templates/ssp/json/').resolve()
JSON_FEDRAMP_SSP_NAME = 'FedRAMP-SSP-OSCAL-Template.json'
XML_FEDRAMP_SSP_PATH = pathlib.Path('fedramp-source/dist/content/rev5/templates/ssp/xml/').resolve()
XML_FEDRAMP_SSP_NAME = 'FedRAMP-SSP-OSCAL-Template.xml'
JSON_TEST_DATA_PATH = pathlib.Path('tests/data/json/').resolve()
TEST_SSP_JSON = 'simplified_fedramp_ssp_template.json'


def verify_control_origination_checkboxes(cell: _Cell, ssp_data: FedrampSSPData) -> None:
    """Verify the control origination checkboxes are populated correctly."""
    checked_list, checked_list_text = get_checked_list(cell)
    if ssp_data.control_origination is None:
        assert len(checked_list) == 0
    else:
        expected_checklist_list: List[int] = []
        control_summaries = ControlSummaries()
        for control_origination in ssp_data.control_origination:
            index_loc: int = control_summaries.get_control_origination_index(control_origination)
            expected_checklist_list.append(index_loc)

            # Check that the actual text is correct in the paragraph
            # Each FedRAMP long string should be in the checked paragraphs of the
            # cell.
            assert control_origination in checked_list_text

        assert checked_list == expected_checklist_list


def verify_implementation_status_checkboxes(cell: _Cell, ssp_data: FedrampSSPData) -> None:
    """Verify the implementation status checkboxes are populated correctly."""
    checked_list, checked_list_text = get_checked_list(cell)
    if ssp_data.implementation_status is None:
        assert len(checked_list) == 0
    else:
        control_summaries = ControlSummaries()
        implementation_status = control_summaries.get_implementation_status_index(ssp_data.implementation_status)

        assert checked_list == [implementation_status]

        # Verify the text is what is expected
        assert ssp_data.implementation_status in checked_list_text


def get_checked_list(cell: _Cell) -> Tuple[List[int], str]:
    """Get the checked list."""
    checked_list: List[int] = []
    checked_list_text: str = ''
    for i, paragraph in enumerate(cell.paragraphs):
        if checkbox_is_set(paragraph) and checkbox_text_is_set(paragraph):
            checked_list.append(i)
            checked_list_text += paragraph.text
    return checked_list, checked_list_text


def checkbox_is_set(paragraph: Paragraph) -> bool:
    """Get the checkbox value."""
    checkboxes = paragraph._element.xpath(const.CHECKBOX_XPATH)
    if checkboxes:
        checkbox = checkboxes[0]
        checked = checkbox.find(f'{const.XML_NAMESPACE}checked')
        return checked.attrib[f'{const.XML_NAMESPACE}val'] == '1'
    return False


def checkbox_text_is_set(paragraph: Paragraph) -> bool:
    """Get the checkbox text value."""
    checkboxes = paragraph._element.xpath(const.BOX_ICON_XPATH)
    if checkboxes:
        checkbox = checkboxes[0]
        return checkbox.text == const.CHECKED_BOX_ICON
    return False


def verify_responses(implementation_table: Table, responses: Dict[str, str], partial_match: bool = False) -> None:
    """Verify the responses are populated correctly."""
    for row in implementation_table.columns[0].cells[1:]:
        label = ControlImplementationDescriptions.get_part_id(row.text)
        # strip everything after newline and remove the colon.
        # get_part_id retrieves the label correctly for the first part
        # empty cells only
        label = label.split('\n')[0].strip(':')
        if label in responses:
            content = responses.get(label)
            if partial_match:
                assert content in row.text
            else:
                assert content == row.text


def verify_parameters(summary_table: Table, parameters: Dict[str, str], partial_match: bool = False) -> None:
    """Verify the responses are populated correctly."""
    for row in summary_table.columns[0].cells[2:]:
        label = ControlSummaries.get_parameter_id(row.text)
        if label and label in parameters:
            value = parameters.get(label)
            if partial_match:
                assert value in row.text
            else:
                assert value == row.text
