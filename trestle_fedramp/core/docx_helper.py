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
"""Classes for populate FedRAMP Docx template."""

import logging
from typing import Dict, Tuple

from docx.document import Document  # type: ignore
from docx.table import Table, _Cell  # type: ignore
from docx.text.paragraph import Paragraph  # type: ignore

from trestle.common.err import TrestleError
from trestle.common.list_utils import as_list

import trestle_fedramp.const as const
from trestle_fedramp.core.ssp_reader import FedrampControlDict, FedrampSSPData

logger = logging.getLogger(__name__)


class ControlSummaries():
    """Populate the control summaries in the FedRAMP template."""

    def __init__(self, docx: Document, control_dict: FedrampControlDict) -> None:
        """Initialize the ControlSummaries class."""
        self.docx = docx
        self.control_dict = control_dict

        self.control_origination_cell: Tuple[int, int] = (-1, 0)
        self.row_header_location: Tuple[int, int] = (0, 0)

    def populate(self) -> None:
        """Populate the control summaries."""
        try:
            for table in self.docx.tables:
                row_header: str = table.cell(*self.row_header_location).text
                if self.is_control_summary_table(row_header):
                    control_id = self.get_control_id(row_header)
                    if control_id in self.control_dict:
                        logging.info(f'Populating the control summary for {control_id}.')
                        self._populate_table(table, control_id, self.control_dict[control_id])
                    else:
                        logger.debug(f'Control ID {control_id} not found in the control dictionary.')
        except Exception as e:
            raise TrestleError(f'Error populating control summaries: {e}')

    @staticmethod
    def get_control_id(row_header: str) -> str:
        """Get the control id from the table."""
        return row_header.split(' ')[0]

    @staticmethod
    def is_control_summary_table(row_header: str) -> bool:
        """Check if the table is a control summary table."""
        return row_header.endswith(const.CONTROL_SUMMARY)

    @staticmethod
    def get_control_origination_index(control_origination: str) -> int:
        """
        Get paragraph index in the control origination cell by control origination string.

        Args:
            control_origination: The control origination string.

        Returns:
            The paragraph index location in the control origination cell
            in the control summary table.
        """
        data: Dict[str, int] = {
            const.FEDRAMP_SP_CORPORATE: 1,
            const.FEDRAMP_SP_SYSTEM: 2,
            const.FEDRAMP_HYBRID: 3,
            const.FEDRAMP_CUST_CONFIGURED: 4,
            const.FEDRAMP_CUST_PROVIDED: 5,
            const.FEDRAMP_SHARED: 6,
            const.FEDRAMP_INHERITED: 7
        }
        return data[control_origination]

    def _populate_table(self, table: Table, control_id: str, ssp_data: FedrampSSPData) -> None:
        """Populate the table with the SSP data."""
        try:
            control_origination_cell: _Cell = table.cell(*self.control_origination_cell)
            for control_origination in as_list(ssp_data.control_origination):
                co_paragraph_index_loc = self.get_control_origination_index(control_origination)
                # Control origination is always the last row in the table
                if co_paragraph_index_loc > len(control_origination_cell.paragraphs):
                    raise TrestleError(f'Invalid control origination for {control_id}: {control_origination}')
                co_paragraph: Paragraph = control_origination_cell.paragraphs[co_paragraph_index_loc]
                self._set_checkbox(co_paragraph)
        except Exception as e:
            raise TrestleError(f'Error populating control summary for {control_id}: {e}')

    def _set_checkbox(self, paragraph: Paragraph) -> None:
        """Check the checkbox in the paragraph."""
        # Find the checkbox element and set the checked attribute to 1
        check_box = paragraph._element.xpath(const.CHECKBOX_XPATH)[0]
        if check_box is None:
            raise TrestleError(f'Checkbox not found in the paragraph with text: {paragraph.text}')
        checked = check_box.find(f'{const.XML_NAMESPACE}checked')
        checked.attrib[f'{const.XML_NAMESPACE}val'] = '1'
        self._set_checkbox_text(paragraph)

    def _set_checkbox_text(self, paragraph: Paragraph) -> None:
        """Set the checkbox text."""
        checkbox_text = paragraph._element.xpath(const.BOX_ICON_XPATH)[0]
        if checkbox_text is None:
            raise TrestleError(f'Checkbox text not found in the paragraph with text: {paragraph.text}')
        logger.debug(f'Checkbox text found in the paragraph with text: {paragraph.text}')
        checkbox_text.text = const.CHECKED_BOX_ICON
