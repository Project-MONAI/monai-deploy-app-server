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


class ServerConfig:
    """Class that defines object to store MONAI Inference configuration specifications"""

    def __init__(self, map_urn: str, map_entrypoint: str, map_cpu: int, map_memory: int,
                 map_gpu: int, map_input_path: str, map_output_path: str,
                 payload_host_path: str):
        """Constructor for Payload Provider class

        Args:
            map_urn (str): MAP Container <image>:<tag> to de deployed for inference
            map_entrypoint (str): Entry point command for MAP Container
            map_cpu (int): Maximum CPU cores needed by MAP Container
            map_memory (int): Maximum memory in Megabytes needed by MAP Container
            map_gpu (int): Maximum GPUs needed by MAP Container
            map_input_path (str): Input directory path of MAP Container
            map_output_path (str): Output directory path of MAP Container
            payload_host_path (str): Host path of payload directory
        """
        self.map_urn = map_urn
        self.map_entrypoint = map_entrypoint
        self.map_cpu = map_cpu
        self.map_memory = map_memory
        self.map_gpu = map_gpu
        self.map_input_path = map_input_path
        self.map_output_path = map_output_path
        self.payload_host_path = payload_host_path
