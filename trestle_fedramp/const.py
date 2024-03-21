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
"""Core constants module containing all constants."""

from typing import Dict, List

# FedRAMP related files and directories
FEDRAM_BASELINE = 'fedramp-source/content/baselines/rev5/xml'
FEDRAMP_REGISTRY = 'fedramp-source/content/resources/xml'
FEDRAM__SVRL_XSL = 'fedramp-source/vendor/svrl2html.xsl'
FEDRAMP_SSP_XSL = 'fedramp-source/ssp.xsl'

# NIST related files for format conversion
NIST_SSP_JSON_XML_XSL = 'nist-source/xml/convert/oscal_ssp_json-to-xml-converter-new.xsl'
NIST_INITIAL_TEMPLATE = 'from-json'
NIST_FILE_PARAM_NAME = 'file'

# FedRAMP related files for SSP Appendix A conversion
FEDRAMP_APPENDIX_A_LOW = 'fedramp-source/content/templates/SSP-Appendix-A-Low-FedRAMP-Security-Controls.docx'
FEDRAMP_APPENDIX_A_MODERATE = 'fedramp-source/content/templates/SSP-Appendix-A-Moderate-FedRAMP-Security-Controls.docx'
FEDRAMP_APPENDIX_A_HIGH = 'fedramp-source/content/templates/SSP-Appendix-A-High-FedRAMP-Security-Controls.docx'

# CONTROL ORIGINATION FEDRAMP

FEDRAMP_SHORT_SP_CORPORATE = 'sp-corporate'
FEDRAMP_SHORT_SP_SYSTEM = 'sp-system'
FEDRAMP_SHORT_CUST_CONFIGURED = 'customer-configured'
FEDRAMP_SHORT_CUST_PROVIDED = 'customer-provided'
FEDRAMP_SHORT_INHERITED = 'inherited'

FEDRAMP_CO_VALUES: List[str] = [
    FEDRAMP_SHORT_SP_CORPORATE,
    FEDRAMP_SHORT_SP_SYSTEM,
    FEDRAMP_SHORT_CUST_CONFIGURED,
    FEDRAMP_SHORT_CUST_PROVIDED,
    FEDRAMP_SHORT_INHERITED
]

FEDRAMP_SP_CORPORATE = 'Service Provider Corporate'
FEDRAMP_SP_SYSTEM = 'Service Provider System Specific'
FEDRAMP_CUST_CONFIGURED = 'Configured by Customer (Customer System Specific)'
FEDRAMP_CUST_PROVIDED = 'Provided by Customer (Customer System Specific)'
FEDRAMP_SHARED = 'Shared (Service Provider and Customer Responsibility)'
FEDRAMP_HYBRID = 'Service Provider Hybrid (Corporate and System Specific)'
FEDRAMP_INHERITED = 'Inherited'

FEDRAMP_CO_SHORT_TO_LONG_NAME: Dict[str, str] = {
    FEDRAMP_SHORT_SP_CORPORATE: FEDRAMP_SP_CORPORATE,
    FEDRAMP_SHORT_SP_SYSTEM: FEDRAMP_SP_SYSTEM,
    FEDRAMP_SHORT_CUST_CONFIGURED: FEDRAMP_CUST_CONFIGURED,
    FEDRAMP_SHORT_CUST_PROVIDED: FEDRAMP_CUST_PROVIDED,
    FEDRAMP_SHORT_INHERITED: FEDRAMP_INHERITED
}

# FedRAMP Template Constants
CONTROL_SUMMARY = 'Control Summary Information'
CONTROL_RESPONSE = 'What is the solution and how is it implemented?'
XML_NAMESPACE = '{http://schemas.microsoft.com/office/word/2010/wordml}'
CHECKBOX_XPATH = './/w:sdt//w:sdtPr//w14:checkbox'
BOX_ICON_XPATH = './/w:sdt//w:sdtContent//w:r//w:t'
CHECKED_BOX_ICON = '☒'
FEDRAMP_STATEMENT_PREFIX = 'Part'
FEDRAMP_PARAMETER_PREFIX = 'Parameter'

# Implementation Status FedRAMP

FEDRAMP_SHORT_IMPLEMENTED = 'implemented'
FEDRAMP_SHORT_PARTIAL = 'partial'
FEDRAMP_SHORT_PLANNED = 'planned'
FEDRAMP_SHORT_ALTERNATIVE = 'alternative'
FEDRAMP_SHORT_NOT_APPLICABLE = 'not-applicable'

FEDRAMP_IMPLEMENTED = 'Implemented'
FEDRAMP_PARTIAL = 'Partially Implemented'
FEDRAMP_PLANNED = 'Planned'
FEDRAMP_ALTERNATIVE = 'Alternative Implementation'
FEDRAMP_NOT_APPLICABLE = 'Not Applicable'

FEDRAMP_IS_SHORT_TO_LONG_NAME: Dict[str, str] = {
    FEDRAMP_SHORT_IMPLEMENTED: FEDRAMP_IMPLEMENTED,
    FEDRAMP_SHORT_PARTIAL: FEDRAMP_PARTIAL,
    FEDRAMP_SHORT_PLANNED: FEDRAMP_PLANNED,
    FEDRAMP_SHORT_ALTERNATIVE: FEDRAMP_ALTERNATIVE,
    FEDRAMP_SHORT_NOT_APPLICABLE: FEDRAMP_NOT_APPLICABLE
}
