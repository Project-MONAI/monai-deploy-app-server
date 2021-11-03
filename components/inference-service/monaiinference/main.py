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
import logging

from starlette.middleware import Middleware
import uvicorn

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from kubernetes import config
from starlette.routing import Host

from monaiinference.handler.config import ServerConfig
from monaiinference.handler.kubernetes import KubernetesHandler, PodStatus
from monaiinference.handler.payload import PayloadProvider

MIS_HOST = "0.0.0.0"

logging_config = {
    'version': 1, 'disable_existing_loggers': True,
    'formatters': {'default': {'()': 'uvicorn.logging.DefaultFormatter',
                               'fmt': '%(levelprefix)s %(message)s', 'use_colors': None},
                   'access': {'()': 'uvicorn.logging.AccessFormatter',
                              'fmt': '%(levelprefix)s %(client_addr)s - "%(request_line)s" %(status_code)s'}},
    'handlers': {'default': {'formatter': 'default', 'class': 'logging.StreamHandler', 'stream': 'ext://sys.stderr'},
                 'access': {'formatter': 'access', 'class': 'logging.StreamHandler', 'stream': 'ext://sys.stdout'}},
    'loggers': {'uvicorn': {'handlers': ['default'], 'level': 'INFO'},
                'uvicorn.error': {'level': 'INFO', 'handlers': ['default'], 'propagate': True},
                'uvicorn.access': {'handlers': ['access'], 'level': 'INFO', 'propagate': False},
                'MIS_Main': {'handlers': ['default'], 'level': 'INFO'},
                'MIS_Payload': {'handlers': ['default'], 'level': 'INFO'},
                'MIS_Kubernetes': {'handlers': ['default'], 'level': 'INFO'}
                },
}

logger = logging.getLogger('MIS_Main')
app = FastAPI(
    middleware=[
        Middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    ],
)


def main():
    """Driver method that parses arguements and intializes providers
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('--map-urn', type=str, required=True,
                        help="MAP Container <image>:<tag> to de deployed for inference")
    parser.add_argument('--map-entrypoint', type=str, required=True,
                        help="Entry point command for MAP Container")
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
    parser.add_argument('--port', type=int, required=False, default=8000,
                        help="Host port of MONAI Inference Service")

    args = parser.parse_args()

    config.load_incluster_config()

    service_config = ServerConfig(args.map_urn, args.map_entrypoint.split(' '), args.map_cpu,
                                  args.map_memory, args.map_gpu, args.map_input_path,
                                  args.map_output_path, args.payload_host_path)
    kubernetes_handler = KubernetesHandler(service_config)
    server_payload_provider = PayloadProvider(args.payload_host_path,
                                              args.map_input_path,
                                              args.map_output_path)

    @app.post("/upload/")
    async def upload_file(file: UploadFile = File(...)) -> FileResponse:
        """Defines REST POST Endpoint for Uploading input payloads.
        Will trigger inference job sequentially after uploading payload

        Args:
            file (UploadFile, optional): .zip file provided by user to be moved
            and extracted in shared volume directory for input payloads. Defaults to File(...).

        Returns:
            FileResponse: Asynchronous object for FastAPI to stream compressed .zip folder with
            the output payload from running the MONAI Application Package
        """

        try:
            await server_payload_provider.upload_input_payload(file)
            kubernetes_handler.create_kubernetes_pod()

            try:
                pod_status = kubernetes_handler.watch_kubernetes_pod()
            finally:
                kubernetes_handler.delete_kubernetes_pod()

            if (pod_status is PodStatus.Pending):
                logger.error("Request timed out since MAP container's pod was in pending state after timeout")
                raise HTTPException(
                    status_code=500,
                    detail="Request timed out since MAP container's pod was in pending state after timeout")
            elif (pod_status is PodStatus.Running):
                logger.error("Request timed out since MAP container's pod was in running state after timeout")
                raise HTTPException(
                    status_code=500,
                    detail="Request timed out since MAP container's pod was in running state after timeout")
            elif (pod_status is PodStatus.Failed):
                logger.info("Request failed since MAP container's pod failed")
                raise HTTPException(status_code=500, detail="Request failed since MAP container's pod failed")
            elif (pod_status is PodStatus.Succeeded):
                logger.info("MAP container's pod completed")
                return server_payload_provider.stream_output_payload()
        except Exception as e:
            logging.error(e, exc_info=True)

    print(f'MAP URN: \"{args.map_urn}\"')
    print(f'MAP entrypoint: \"{args.map_entrypoint}\"')
    print(f'MAP cpu: \"{args.map_cpu}\"')
    print(f'MAP memory: \"{args.map_memory}\"')
    print(f'MAP gpu: \"{args.map_gpu}\"')
    print(f'MAP input path: \"{args.map_input_path}\"')
    print(f'MAP output path: \"{args.map_output_path}\"')
    print(f'payload host path: \"{args.payload_host_path}\"')
    print(f'MIS host: \"{MIS_HOST}\"')
    print(f'MIS port: \"{args.port}\"')

    uvicorn.run(app, host=MIS_HOST, port=args.port, log_config=logging_config)


if __name__ == "__main__":
    main()
