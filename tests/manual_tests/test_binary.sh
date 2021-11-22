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

# This script is designed to test whether the bdist is behaving correctly.
# Note that it encodes the stanndard testing protocol and should be updated.

echo $SAXON_PYTHONPATH
mkdir tmp_bin_test
echo '---- setting up venv ----' 
python -m venv tmp_bin_test/venv
echo '---- venv setup done ----'
ls tmp_bin_test
echo '---- Buiilding bdist ----'
python setup.py bdist_wheel
echo '---- Buiilding bdist DONE ----'
echo '---- Enabling venv ----'
. tmp_bin_test/venv/bin/activate
echo '---- setting PYTHON PATH  ----'
export PYTHONPATH=$PYTHONPATH:$SAXON_PYTHONPATH
echo $PYTHONPATH
echo '----  PRINTED PYTHON PATH  ----'
python -m pip install dist/*.whl
python -m pip install pytest
# this is required to get away from the damn base directory
cd tmp_bin_test
ln -s ../tests
python -m pytest -v --exitfirst

