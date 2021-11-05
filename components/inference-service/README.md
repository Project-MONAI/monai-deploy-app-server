# MONAI Inference Service

[![License](https://img.shields.io/badge/license-Apache%202.0-green.svg)](https://opensource.org/licenses/Apache-2.0)

MONAI Inference Service(MIS) is a server that runs MONAI Application Packages (MAP)[https://github.com/Project-MONAI/monai-deploy/blob/main/guidelines/monai-application-package.md] in a Kubernetes cluster. It shares the same
principles with [MONAI](https://github.com/Project-MONAI).

## Features

> _The codebase is currently under active development._

- Register a MAP in the Helm Charts of MIS.
- Upload inputs via a REST API request and make them available to the MAP container.
- Provision resources for the MAP container.
- Provide outputs of the MAP container to the client which made the request.

## Installation

MIS supports following OS with **GPU/CUDA** enabled.

- Ubuntu

### Building the MIS Container

To build the MIS container, you can simply run:
```bash
   ./build.sh
```

To build the MIS container manually, you can run:
```bash
   docker build -f dockerfile -t monai/inference-service:0.1 .
```

### Helm Chart Configuration
Helm charts are located in the charts folder.

All helm chart configuration values are listed in the `values.yaml` file in the charts folder.

#### MIS Image and Tag
MIS container image can be set in the `monaiInferenceService` field of the images section.

The container tag for MIS can be set in the `monaiInferenceServiceTag` of the images section.

#### MIS Kubernetes Service Type
MIS supports two Kubernetes [service types](https://kubernetes.io/docs/concepts/services-networking/service/#publishing-services-service-types) types: NodePort and ClusterIp.

This can be set in the `serviceType` field of the server section.

The default value of `serviceType` is `NodePort`.

#### MIS Node Port
The node port can be set in the `nodePort` field of the server section. If the `serviceType` is set to `NodePort`, the IP address of the machine on which MIS is deployed along with the node port can be used to reach the MIS.

#### MIS Target Port
The target port can be set in the `targetPort` field of the server section. Regardless of service type, if a client is on a machine belonging to the Kubernetes cluster on which MIS is deployed, cluster IP of the MIS kubernetes service along with the target port can be used to reach the MIS.

You can obtain the cluster IP of the MIS Kubernetes service by doing a `kubectl get svc`.

For example,
```bash
user@hostname:~$ kubectl get svc
NAME                      TYPE        CLUSTER-IP     EXTERNAL-IP   PORT(S)          AGE
kubernetes                ClusterIP   10.96.0.1      <none>        443/TCP          8d
monai-inference-service   NodePort    10.97.138.32   <none>        8000:32000/TCP   4s
```

Under the entry `monai-inference-service`, note the IP registered under the `CLUSTER-IP` section. This is the Cluster IP of the MIS.

#### MIS Volume Host Path
To register the host path on which the payload volume for the MAP resides, record the host path in the `hostVolumePath` field of the `payloadService` sub section of the `server` section.

#### MAP Configuration
TODO

### Helm Chart Deployment

In order to install the helm chart, please run:
```bash
   helm install monai-inference-service ./charts
```

## Submitting inference requests
TODO
