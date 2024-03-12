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
"""Information about Baselines and templates."""

from pkg_resources import resource_filename

from trestle_fedramp.const import (FEDRAMP_APPENDIX_A_HIGH, FEDRAMP_APPENDIX_A_LOW, FEDRAMP_APPENDIX_A_MODERATE)


class BaselineLevel:
    """Represents the baseline level for the FedRAMP SSP."""

    LOW = 'low'
    MODERATE = 'moderate'
    HIGH = 'high'

    LEVELS = {LOW, MODERATE, HIGH}

    @classmethod
    def get_template(cls, level: str) -> str:
        """Get the template file for the given level.

        Args:
            level (str): The baseline level ('low', 'moderate', 'high').

        Returns:
            str: The file path of the template.
        """
        resources_path = 'trestle_fedramp.resources'
        data = {
            cls.LOW: resource_filename(resources_path, FEDRAMP_APPENDIX_A_LOW),
            cls.MODERATE: resource_filename(resources_path, FEDRAMP_APPENDIX_A_MODERATE),
            cls.HIGH: resource_filename(resources_path, FEDRAMP_APPENDIX_A_HIGH)
        }
        if level not in cls.LEVELS:
            raise ValueError(f'Invalid level: {level}. Use one of {cls.LEVELS}')
        return data[level]
