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

import argparse

from fastapi import FastAPI
from kubernetes import config

import handler

app = FastAPI()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--map-urn', type=str, required=True,
                        help="MAP Container <image>:<tag> to de deployed for inference")
    parser.add_argument('--map-entrypoint', type=str, required=True, help="Entry point command for MAP Container")
    parser.add_argument('--map-cpu', type=int, required=True, help="Maximum CPU cores needed by MAP Container")
    parser.add_argument('--map-memory', type=int, required=True,
                        help="Maximum memory in Megabytes needed by MAP Container")
    parser.add_argument('--map-gpu', type=int, required=True, help="Maximum GPUs needed by MAP Container")
    parser.add_argument('--map-input-path', type=str, required=True,
                        help="Input directory path of MAP Container")
    parser.add_argument('--map-output-path', type=str, required=True,
                        help="Output directory path of MAP Container")
    parser.add_argument('--payload-host-path', type=str, required=True,
                        help="Host path of payload directory")

    args = parser.parse_args()

    config.load_config()

    service_config = handler.Config(args.map_urn, args.map_entrypoint.split(' '), args.map_cpu, args.map_memory,
                                    args.map_gpu, args.map_input_path, args.map_output_path, args.payload_host_path)

    kubernetes_handler = handler.KubernetesHandler(service_config)

    '''
        TODO: This is to be incorporated in the FAST API endpoint
        kubernetes_handler.create_kubernetes_pod()
        pod_status = kubernetes_handler.watch_kubernetes_pod()

        if (pod_status is handler.PodStatus.Pending):
            print("Pod Pending")
        elif (pod_status is handler.PodStatus.Running):
            print("Pod Running")
        elif (pod_status is handler.PodStatus.Succeeded):
            print("Pod Completed")
        elif (pod_status is handler.PodStatus.Failed):
            print("Pod Failed")

        kubernetes_handler.delete_kubernetes_pod()

    '''


if __name__ == "__main__":
    main()
