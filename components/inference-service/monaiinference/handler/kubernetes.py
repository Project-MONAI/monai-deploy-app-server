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

import os
import time

from kubernetes import client
from kubernetes.client import models

API_VERSION_FOR_JOBS = "batch/v1"
API_VERSION_FOR_PERSISTENT_VOLUME = "v1"
API_VERSION_FOR_PERSISTENT_VOLUME_CLAIM = "v1"
DEFAULT_NAMESPACE = "default"
DIRECTORY_OR_CREATE = "DirectoryOrCreate"
JOB = "Job"
JOB_NAME = "monai-job"
PERSISTENT_VOLUME = "PersistentVolume"
PERSISTENT_VOLUME_CLAIM = "PersistentVolumeClaim"
PERSISTENT_VOLUME_CLAIM_NAME = "monai-volume-claim"
PERSISTENT_VOLUME_NAME = "monai-volume"
READ_WRITE_ONCE = "ReadWriteOnce"
RESTART_POLICY_NEVER = "Never"
STORAGE = "storage"
STORAGE_CLASS_NAME = "monai-storage-class"


class KubernetesHandler:
    'TODO: Documentation for K8s Handler'

    def __init__(self, config):
        # Initialize kubernetes clients
        self.kubernetes_batch_client = client.BatchV1Api()
        self.kubernetes_core_client = client.CoreV1Api()
        self.config = config

    def __create_container_template(self) -> models.V1Container:

        input_path = self.config.map_input_path
        if (os.path.isabs(input_path) is False):
            input_path = '/' + input_path

        input_mount = models.V1VolumeMount(
            name=PERSISTENT_VOLUME_CLAIM_NAME,
            mount_path=input_path,
            sub_path=input_path[1:],
            read_only=True
        )

        output_path = self.config.map_output_path
        if (os.path.isabs(output_path) is False):
            output_path = '/' + output_path

        output_mount = models.V1VolumeMount(
            name=PERSISTENT_VOLUME_CLAIM_NAME,
            mount_path=output_path,
            sub_path=output_path[1:],
        )

        container = models.V1Container(
            name="map",
            image=self.config.map_urn,
            command=self.config.map_entrypoint,
            image_pull_policy="IfNotPresent",
            volume_mounts=[input_mount, output_mount]
        )

        return container

    def __create_kubernetes_job(self) -> models.V1Job:
        container = self.__create_container_template()

        job = models.V1Job(
            api_version=API_VERSION_FOR_JOBS,
            kind=JOB,
            metadata=models.V1ObjectMeta(
                name=JOB_NAME,
                labels={
                    "job-name": JOB_NAME,
                    "job-type": "monai"
                }
            ),
            spec=models.V1JobSpec(
                template=models.V1PodTemplateSpec(
                    spec=models.V1PodSpec(
                        containers=[container],
                        restart_policy=RESTART_POLICY_NEVER,
                        volumes=[
                            models.V1Volume(
                                name=PERSISTENT_VOLUME_CLAIM_NAME,
                                persistent_volume_claim=models.V1PersistentVolumeClaimVolumeSource(
                                    claim_name=PERSISTENT_VOLUME_CLAIM_NAME,
                                ),
                            )
                        ]
                    )
                )
            )
        )

        return job

    def __create_kubernetes_persistent_volume(self) -> models.V1PersistentVolume:
        persistent_volume = models.V1PersistentVolume(
            api_version=API_VERSION_FOR_PERSISTENT_VOLUME,
            kind=PERSISTENT_VOLUME,
            metadata=models.V1ObjectMeta(
                name=PERSISTENT_VOLUME_NAME,
                labels={
                    "volume-type": "monai"
                }
            ),
            spec=models.V1PersistentVolumeSpec(
                access_modes=[READ_WRITE_ONCE],
                capacity={
                    STORAGE: "10Gi",
                },
                host_path=models.V1HostPathVolumeSource(
                    path=self.config.payload_host_path,
                    type=DIRECTORY_OR_CREATE,
                ),
                storage_class_name=STORAGE_CLASS_NAME,
            )
        )

        return persistent_volume

    def __create_kubernetes_persistent_volume_claim(self) -> models.V1PersistentVolumeClaim:
        persistent_volume_claim = models.V1PersistentVolumeClaim(
            api_version=API_VERSION_FOR_PERSISTENT_VOLUME_CLAIM,
            kind=PERSISTENT_VOLUME_CLAIM,
            metadata=models.V1ObjectMeta(
                name=PERSISTENT_VOLUME_CLAIM_NAME,
                labels={
                    "volume-claim-type": "monai"
                }
            ),
            spec=models.V1PersistentVolumeClaimSpec(
                access_modes=[READ_WRITE_ONCE],
                resources=models.V1ResourceRequirements(
                    requests={
                        STORAGE: "10Gi",
                    }
                ),
                storage_class_name=STORAGE_CLASS_NAME,
            )
        )

        return persistent_volume_claim

    def create_kubernetes_job(self):
        pv = self.__create_kubernetes_persistent_volume()
        self.kubernetes_core_client.create_persistent_volume(pv)

        pvc = self.__create_kubernetes_persistent_volume_claim()
        self.kubernetes_core_client.create_namespaced_persistent_volume_claim(namespace=DEFAULT_NAMESPACE, body=pvc)

        job = self.__create_kubernetes_job()

        self.kubernetes_batch_client.create_namespaced_job(
            namespace=DEFAULT_NAMESPACE,
            body=job
        )

    def delete_kubernetes_job(self):
        self.kubernetes_batch_client.delete_namespaced_job(name=JOB_NAME, namespace=DEFAULT_NAMESPACE)

    def watch_kubernetes_job(self):
        polling_time = 1
        total_sleep_time = 50
        current_sleep_time = 0
        job_completed = False
        succeeded = False
        failed = False
        running = False

        while (current_sleep_time < total_sleep_time):
            job = self.kubernetes_batch_client.read_namespaced_job(name=JOB_NAME, namespace=DEFAULT_NAMESPACE)

            if (job.status is None):
                continue

            print(job.status)

            if (job.status.active == 1):
                running = True

            if (job.status.succeeded == 1):
                succeeded = True
                running = False
                break

            if (job.status.failed == 1):
                failed = True
                running = False
                break

            time.sleep(polling_time)
            current_sleep_time += polling_time
