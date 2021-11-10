# Copyright 2021 MONAI Consortium
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging
import os
import shutil
import zipfile
from pathlib import Path

from fastapi import File, UploadFile
from fastapi.responses import FileResponse

logger = logging.getLogger('MIS_Payload')


class PayloadProvider:
    """Class to handle interactions with payload I/O and Monai Inference Service
    shared volumes"""

    def __init__(self, host_path: str, input_path: str, output_path: str):
        """Constructor for Payload Provider class

        Args:
            host_path (str): Absolute path of shared volume for payloads
            input_path (str): Relative path of input sub-directory within shared volume for payloads
            output_path (str): Relative path of input sub-directory within shared volume for payloads
        """
        self._host_path = host_path
        self._input_path = input_path.strip('/')
        self._output_path = output_path.strip('/')

        PayloadProvider.clean_directory(self._host_path)

        abs_input_path = Path(os.path.join(self._host_path, self._input_path))
        abs_input_path.mkdir(parents=True, exist_ok=True)
        os.chmod(abs_input_path, 0o777)

        abs_output_path = Path(os.path.join(self._host_path, self._output_path))
        abs_output_path.mkdir(parents=True, exist_ok=True)
        os.chmod(abs_output_path, 0o777)


    def upload_input_payload(self, file: UploadFile=File(...)):
        """Uploads and extracts input payload .zip provided by user to input folder within MIS container

        Args:
            file (UploadFile, optional): .zip file provided by user to be moved
            and extracted in shared volume directory for input payloads. Defaults to File(...).
        """

        abs_input_path = os.path.join(self._host_path, self._input_path)
        # Clean input payload directory of any lingering content
        PayloadProvider.clean_directory(abs_input_path)

        abs_output_path = os.path.join(self._host_path, self._output_path)
        # Clean output payload directory of any lingering content
        PayloadProvider.clean_directory(abs_output_path)

        # Read contents of .zip file arguement and write it to input payload folder
        target_path = f'{abs_input_path}/{file.filename}'
        f = open(f'{target_path}', 'wb')
        content = file.file.read()
        f.write(content)
        f.close()

        # Extract contents of .zip into input payload folder
        with zipfile.ZipFile(target_path, 'r') as zip_ref:
            zip_ref.extractall(abs_input_path)

        # Remove compressed input payload .zip file
        os.remove(target_path)

        logger.info(f'Extracted {target_path} into {abs_input_path}')

    def stream_output_payload(self) -> FileResponse:
        """Compresses output payload directory and returns .zip as FileResponse object

        Returns:
            FileResponse: Asynchronous object for FastAPI to stream compressed .zip folder with
            the output payload from running the MONAI Application Package
        """
        abs_output_path = os.path.join(self._host_path, self._output_path)
        abs_zip_path = os.path.join(self._host_path, 'output.zip')

        # Compress output payload directory into .zip file in root payload directory
        with zipfile.ZipFile(abs_zip_path, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for root_dir, dirs, files in os.walk(abs_output_path):
                for file in files:
                    zip_file.write(os.path.join(root_dir, file),
                                   os.path.relpath(os.path.join(root_dir, file),
                                   os.path.join(abs_output_path, '..')))

            logger.info(f'Compressed {abs_output_path} into {abs_zip_path}')

        # Move compressed .zip into output payload directory
        target_zip_path = os.path.join(abs_output_path, 'output.zip')
        shutil.move(abs_zip_path, target_zip_path)

        # Return stream of resulting .zip file using the FastAPI FileResponse object
        logger.info(f'Returning stream of {target_zip_path}')
        return FileResponse(target_zip_path)

    @staticmethod
    def clean_directory(dir_path: str):
        """Cleans contents of a directory, but does not delete directory itself

        Args:
            dir_path (str): Path to of directory to be cleaned
        """

        deletion_files = [f for f in os.listdir(dir_path)]

        for f in deletion_files:
            deletion_path = os.path.join(dir_path, f)
            if os.path.isdir(deletion_path):
                shutil.rmtree(deletion_path)
            else:
                os.remove(deletion_path)
