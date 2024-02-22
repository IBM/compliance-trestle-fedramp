# -*- mode:python; coding:utf-8 -*-

# Copyright (c) 2021 IBM Corp. All rights reserved.
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
"""Testing docx utility classes."""

from typing import List

from docx.document import Document as DocxDocument  # type: ignore
from docx.table import _Cell  # type: ignore
from docx.text.paragraph import Paragraph  # type: ignore

import pytest

from trestle.common.err import TrestleError

from trestle_fedramp import const
from trestle_fedramp.core.docx_helper import ControlImplementationDescriptions, ControlSummaries, FedrampDocx
from trestle_fedramp.core.ssp_reader import FedrampControlDict, FedrampSSPData


def verify_checkboxes(cell: _Cell, ssp_data: FedrampSSPData) -> None:
    """Verify the checkboxes are populated correctly."""
    checked_list: List[int] = []
    checked_list_text: str = ''
    for i, paragraph in enumerate(cell.paragraphs):
        if checkbox_is_set(paragraph) and checkbox_text_is_set(paragraph):
            checked_list.append(i)
            checked_list_text += paragraph.text

    if ssp_data.control_origination is None:
        assert len(checked_list) == 0
    else:
        expected_checklist_list: List[int] = []
        for control_origination in ssp_data.control_origination:
            index_loc: int = ControlSummaries.get_control_origination_index(control_origination)
            expected_checklist_list.append(index_loc)

            # Check that the actual text is correct in the paragraph
            # Each FedRAMP long string should be in the checked paragraphs of the
            # cell.
            assert control_origination in checked_list_text

        assert checked_list == expected_checklist_list


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


def test_fedramp_docx_populate(docx_document: DocxDocument, test_ssp_control_dict: FedrampControlDict) -> None:
    """Test FedRAMP docx populate and verify the correct controls are populated."""
    fedramp_docx = FedrampDocx(docx_document, test_ssp_control_dict)
    fedramp_docx.populate()

    # Read the table information validate the proper check boxes are populated
    control_summaries = ControlSummaries()
    control_implementation_description = ControlImplementationDescriptions()
    for table in docx_document.tables:
        row_header = table.rows[0].cells[0].text
        if control_summaries.is_control_summary_table(row_header):
            control_id = fedramp_docx.get_control_id(row_header)
            data: FedrampSSPData = test_ssp_control_dict.get(control_id, FedrampSSPData({}, None))
            verify_checkboxes(table.cell(*control_summaries.control_origination_cell), data)
        if control_implementation_description.is_control_implementation_table(row_header):
            control_id = fedramp_docx.get_control_id(row_header)
            data = test_ssp_control_dict.get(control_id, FedrampSSPData({}, None))
            for cell in table.columns[0].cells[1:]:
                label = control_implementation_description.get_part_id(cell.text)
                content = data.control_implementation_description.get(label, '')
                assert content in cell.text


def test_fedramp_docx_with_invalid_input(docx_document: DocxDocument) -> None:
    """Trigger and error with invalid input."""
    # AC-1 does not have an control origination inherited value
    invalid_control_dict: FedrampControlDict = {
        'AC-1': FedrampSSPData({}, control_origination=[const.FEDRAMP_INHERITED])
    }
    fedramp_docx = FedrampDocx(docx_document, invalid_control_dict)

    with pytest.raises(TrestleError, match='.*Invalid control origination for AC-1: Inherited'):
        fedramp_docx.populate()


def test_fedramp_docx_with_non_existent_control_origination(docx_document: DocxDocument) -> None:
    """Trigger and error with a non-existent control origination."""
    # AC-1 does not have an control origination inherited value
    invalid_control_dict: FedrampControlDict = {'AC-1': FedrampSSPData({}, control_origination=['invalid'])}
    fedramp_docx = FedrampDocx(docx_document, invalid_control_dict)

    with pytest.raises(TrestleError, match='.*Invalid FedRAMP control origination value: invalid'):
        fedramp_docx.populate()


def test_get_control_id() -> None:
    """Test FedRAMP docx get control id."""
    test_row_header = 'AC-2 Control Summary Information'
    control_label = FedrampDocx.get_control_id(test_row_header)
    assert control_label == 'AC-2'
