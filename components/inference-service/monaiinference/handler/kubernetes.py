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

import enum
import logging
import os
import time
from pathlib import Path

from monaiinference.handler.config import ServerConfig

from kubernetes import client
from kubernetes.client import models

API_VERSION_FOR_PODS = "v1"
API_VERSION_FOR_PERSISTENT_VOLUME = "v1"
API_VERSION_FOR_PERSISTENT_VOLUME_CLAIM = "v1"
DEFAULT_NAMESPACE = "default"
DEFAULT_STORAGE_SPACE = "10Gi"
DIRECTORY_OR_CREATE = "DirectoryOrCreate"
IF_NOT_PRESENT = "IfNotPresent"
MAP = "map"
MONAI = "monai"
POD = "Pod"
POD_NAME = "monai-pod"
PERSISTENT_VOLUME = "PersistentVolume"
PERSISTENT_VOLUME_CLAIM = "PersistentVolumeClaim"
PERSISTENT_VOLUME_CLAIM_NAME = "monai-volume-claim"
PERSISTENT_VOLUME_NAME = "monai-volume"
READ_WRITE_ONCE = "ReadWriteOnce"
RESTART_POLICY_NEVER = "Never"
STORAGE = "storage"
STORAGE_CLASS_NAME = "monai-storage-class"
WAIT_TIME_FOR_POD_COMPLETION = 50

logger = logging.getLogger('MIS_Kubernetes')


class KubernetesHandler:
    """Class to handle interactions with kubernetes for fulflling an inference request."""

    def __init__(self, config: ServerConfig):
        """Constructor of the base KubernetesHandler class

        Args:
            config (ServerConfig): Instance of ServerConfig class with MONAI Inference
            configuration specifications
        """
        # Initialize kubernetes client and handler configuration.
        self.kubernetes_core_client = client.CoreV1Api()
        self.config = config

    def __build_resources_requests(self) -> models.V1ResourceRequirements:
        # Derive CPU, memory(in Megabytes) and GPU limits for container from handler configuration.
        limits = {
            "cpu": str(self.config.map_cpu),
            "memory": str(self.config.map_memory) + "Mi",
            "nvidia.com/gpu": str(self.config.map_gpu)
        }

        resources = models.V1ResourceRequirements(limits=limits)
        return resources

    def __build_container_template(self) -> models.V1Container:
        # Derive container POSIX input path for defining input mount.
        input_path = Path(os.path.join("/", self.config.map_input_path)).as_posix()

        input_mount = models.V1VolumeMount(
            name=PERSISTENT_VOLUME_CLAIM_NAME,
            mount_path=input_path,
            sub_path=input_path[1:],
            read_only=True
        )

        # Derive container POSIX output path for defining output mount.
        output_path = Path(os.path.join("/", self.config.map_output_path)).as_posix()

        output_mount = models.V1VolumeMount(
            name=PERSISTENT_VOLUME_CLAIM_NAME,
            mount_path=output_path,
            sub_path=output_path[1:],
        )

        # Build Shared Memory volume mount.
        shared_memory_volume_mount = models.V1VolumeMount(
            mount_path="/dev/shm",
            name="shared-memory",
            read_only=False
        )

        # Build container object.
        container = models.V1Container(
            name=MAP,
            image=self.config.map_urn,
            command=self.config.map_entrypoint,
            image_pull_policy=IF_NOT_PRESENT,
            resources=self.__build_resources_requests(),
            volume_mounts=[input_mount, output_mount, shared_memory_volume_mount]
        )

        return container

    def __build_kubernetes_pod(self) -> models.V1Pod:
        container = self.__build_container_template()

        # Build pod object.
        pod = models.V1Pod(
            api_version=API_VERSION_FOR_PODS,
            kind=POD,
            metadata=models.V1ObjectMeta(
                name=POD_NAME,
                labels={
                    "pod-name": POD_NAME,
                    "pod-type": MONAI
                }
            ),
            spec=models.V1PodSpec(
                containers=[container],
                restart_policy=RESTART_POLICY_NEVER,
                volumes=[
                    models.V1Volume(
                        name=PERSISTENT_VOLUME_CLAIM_NAME,
                        persistent_volume_claim=models.V1PersistentVolumeClaimVolumeSource(
                            claim_name=PERSISTENT_VOLUME_CLAIM_NAME,
                        ),
                    ),
                    models.V1Volume(
                        name="shared-memory",
                        empty_dir=models.V1EmptyDirVolumeSource
                        (
                            medium="Memory",
                        )
                    )
                ]
            )
        )

        return pod

    def __build_kubernetes_persistent_volume(self) -> models.V1PersistentVolume:
        persistent_volume = models.V1PersistentVolume(
            api_version=API_VERSION_FOR_PERSISTENT_VOLUME,
            kind=PERSISTENT_VOLUME,
            metadata=models.V1ObjectMeta(
                name=PERSISTENT_VOLUME_NAME,
                labels={
                    "volume-type": MONAI
                }
            ),
            spec=models.V1PersistentVolumeSpec(
                access_modes=[READ_WRITE_ONCE],
                capacity={
                    STORAGE: DEFAULT_STORAGE_SPACE,
                },
                host_path=models.V1HostPathVolumeSource(
                    path=self.config.payload_host_path,
                    type=DIRECTORY_OR_CREATE,
                ),
                storage_class_name=STORAGE_CLASS_NAME,
            )
        )

        return persistent_volume

    def __build_kubernetes_persistent_volume_claim(self) -> models.V1PersistentVolumeClaim:
        persistent_volume_claim = models.V1PersistentVolumeClaim(
            api_version=API_VERSION_FOR_PERSISTENT_VOLUME_CLAIM,
            kind=PERSISTENT_VOLUME_CLAIM,
            metadata=models.V1ObjectMeta(
                name=PERSISTENT_VOLUME_CLAIM_NAME,
                labels={
                    "volume-claim-type": MONAI
                }
            ),
            spec=models.V1PersistentVolumeClaimSpec(
                access_modes=[READ_WRITE_ONCE],
                resources=models.V1ResourceRequirements(
                    requests={
                        STORAGE: DEFAULT_STORAGE_SPACE,
                    }
                ),
                storage_class_name=STORAGE_CLASS_NAME,
            )
        )

        return persistent_volume_claim

    def create_kubernetes_pod(self):
        """Create a kubernetes pod and the Persistent Volume and Persistent Volume Claim needed by the pod.
        """

        try:
            # Create a Kubernetes Persistent Volume.
            pv = self.__build_kubernetes_persistent_volume()
            self.kubernetes_core_client.create_persistent_volume(pv)
            logger.info(f'Created Persistent Volume {pv.metadata.name}')
        except Exception as e:
            logger.error(e, exc_info=True)

        try:
            # Create a Kubernetes Persistent Volume Claim.
            pvc = self.__build_kubernetes_persistent_volume_claim()
            self.kubernetes_core_client.create_namespaced_persistent_volume_claim(namespace=DEFAULT_NAMESPACE, body=pvc)
            logger.info(f'Created Persistent Volume Claim {pvc.metadata.name}')
        except Exception as e:
            logger.error(e, exc_info=True)
            self.kubernetes_core_client.delete_persistent_volume(name=PERSISTENT_VOLUME_NAME)

        try:
            # Create a Kubernetes Pod.
            pod = self.__build_kubernetes_pod()
            self.kubernetes_core_client.create_namespaced_pod(
                namespace=DEFAULT_NAMESPACE,
                body=pod
            )

            logger.info(f'Created pod {pod.metadata.name}')
        except Exception as e:
            self.kubernetes_core_client.delete_namespaced_persistent_volume_claim(
                namespace=DEFAULT_NAMESPACE, name=PERSISTENT_VOLUME_CLAIM_NAME)
            self.kubernetes_core_client.delete_persistent_volume(name=PERSISTENT_VOLUME_NAME)
            logger.error(e, exc_info=True)

    def delete_kubernetes_pod(self):
        """Delete a kubernetes pod and the Persistent Volume and Persistent Volume Claim created for the pod.
        """

        # Delete the Kubernetes Pod, Persistent Volume Claim and Persistent Volume.
        try:
            self.kubernetes_core_client.delete_namespaced_pod(name=POD_NAME, namespace=DEFAULT_NAMESPACE)
            logger.info(f'Deleted pod {POD_NAME}')
        except Exception as e:
            logger.error(e, exc_info=True)

        try:
            self.kubernetes_core_client.delete_namespaced_persistent_volume_claim(
                namespace=DEFAULT_NAMESPACE, name=PERSISTENT_VOLUME_CLAIM_NAME)
            logger.info(f'Deleted Persistent Volume Claim {PERSISTENT_VOLUME_CLAIM_NAME}')
        except Exception as e:
            logger.error(e, exc_info=True)

        try:
            self.kubernetes_core_client.delete_persistent_volume(name=PERSISTENT_VOLUME_NAME)
            logger.info(f'Deleted Persistent Volume {PERSISTENT_VOLUME_NAME}')
        except Exception as e:
            logger.error(e, exc_info=True)

    def watch_kubernetes_pod(self):
        """Watch the status of kubernetes pod until it completes or it times out.

        Returns:
            PodStatus: Enum which denotes a pod status.
        """
        polling_time = 1
        current_sleep_time = 0
        status = PodStatus.Pending

        # Check every `polling_time` seconds if pod has completed(successfully/failed).
        # If Pod does not complete within timeout, return last reported status(Pending/Running) of pod.
        # If pod is in a pending state with ImagePullBackOff error, then quit checking for pod status
        # and return error along with Pending status.

        while (current_sleep_time < WAIT_TIME_FOR_POD_COMPLETION):
            pod = self.kubernetes_core_client.read_namespaced_pod(name=POD_NAME, namespace=DEFAULT_NAMESPACE)
            if (pod.status is None):
                continue

            pod_status = pod.status.phase

            if (pod_status == "Pending"):
                status = PodStatus.Pending

                container_statuses = pod.status.container_statuses
                if (container_statuses is None):
                    continue

                container_status = container_statuses[0]
                if (container_status.state.waiting is not None and
                        container_status.state.waiting.reason == "ImagePullBackOff"):
                    logger.warning(f'Pod {POD_NAME} in Pending State: Image Pull Back Off')
                    break
            elif (pod_status == "Running"):
                status = PodStatus.Running
            elif (pod_status == "Succeeded"):
                status = PodStatus.Succeeded
                break
            elif (pod_status == "Failed"):
                status = PodStatus.Failed
                break
            else:
                logger.warning(f'Unknown pod status {pod.status.phase}')

            time.sleep(polling_time)
            current_sleep_time += polling_time

        logger.info(f'Pod status is {status} after {current_sleep_time} seconds')

        return status


class PodStatus(enum.Enum):
    Pending = 1,
    Running = 2,
    Succeeded = 3,
    Failed = 4
