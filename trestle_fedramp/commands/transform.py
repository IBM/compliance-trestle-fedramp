# -*- mode:python; coding:utf-8 -*-

# Copyright (c) 2024 IBM Corp. All rights reserved.
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
"""Trestle FedRAMP Transform Command."""

import argparse
import logging
import pathlib

from docx import Document  # type: ignore
from docx.document import Document as DocxDocument  # type: ignore

import trestle.common.log as log
from trestle.common.err import TrestleError, handle_generic_command_exception
from trestle.common.model_utils import ModelUtils
from trestle.core.commands.command_docs import CommandPlusDocs
from trestle.core.commands.common import return_codes
from trestle.oscal import ssp

from trestle_fedramp.core.baselines import BaselineLevel
from trestle_fedramp.core.docx_helper import ControlSummaries
from trestle_fedramp.core.ssp_reader import FedrampControlDict, FedrampSSPReader

logger = logging.getLogger(__name__)


class SSPTransformCmd(CommandPlusDocs):
    """Transform an OSCAL SSP to FedRAMP SSP Appendix A document."""

    name = 'fedramp-transform'

    def _init_arguments(self) -> None:
        logger.debug('Init arguments')
        self.add_argument('-n', '--ssp-name', help='OSCAL SSP name from trestle workspace.', type=str, required=True)
        self.add_argument(
            '-l',
            '--level',
            required=True,
            type=str,
            choices=BaselineLevel.LEVELS,
            help='FedRAMP Baseline level for template selection.',
        )
        self.add_argument(
            '-o', '--output-file', help='Output file for populated SSP Appendix A template', type=str, required=True
        )

    def _run(self, args: argparse.Namespace) -> int:
        logger.debug('Entering trestle fedramp-transform.')

        log.set_log_level_from_args(args)

        ssp_file_path = ModelUtils.get_model_path_for_name_and_class(
            args.trestle_root, args.ssp_name, ssp.SystemSecurityPlan
        )

        if ssp_file_path is None or not ssp_file_path.exists():
            logger.error(f'Input ssp {args.ssp_name} does not exist in the trestle workspace.')
            return return_codes.CmdReturnCodes.COMMAND_ERROR.value

        try:
            # If this error is thrown, there is a bug in the code
            template = pathlib.Path(BaselineLevel.get_template(args.level)).resolve()
            if not template.exists():
                raise TrestleError(f'Bug FedRAMP Template {template} does not exist')

            # Read the OSCAL SSP data
            ssp_reader = FedrampSSPReader(args.trestle_root)
            control_dict: FedrampControlDict = ssp_reader.read_ssp_data(ssp_file_path)

            # Load the document and save it for altering
            with open(template, 'rb') as file:
                document: DocxDocument = Document(file)

            # Populate the document with the OSCAL SSP data
            control_summaries: ControlSummaries = ControlSummaries(document, control_dict)
            control_summaries.populate()

            document.save(args.output_file)
        except Exception as e:
            return handle_generic_command_exception(e, logger)

        return return_codes.CmdReturnCodes.SUCCESS.value
