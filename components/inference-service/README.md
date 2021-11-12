# MONAI Inference Service

[![License](https://img.shields.io/badge/license-Apache%202.0-green.svg)](https://opensource.org/licenses/Apache-2.0)

MONAI Inference Service(MIS) is a server that runs MONAI Application Packages [MAP](https://github.com/Project-MONAI/monai-deploy/blob/main/guidelines/monai-application-package.md) in a [Kubernetes](https://kubernetes.io/) cluster. It shares the same
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

MIS is intended to be deployed as a microservice in a [Kubernetes](https://kubernetes.io/) cluster.

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
To register the host path on which the payload volume for the MAP resides, record the host path in the `hostVolumePath` field of the `payloadService` sub-section of the `server` section.

#### MAP Configuration
The `map` sub-section in the `server` section has all the configuration values for the MAP.
- urn: This represents the container "\<image\>:\<tag\>" to be deployed by MIS. For example, `urn: ubuntu:latest`.
- entrypoint: String value which defines entry point command for MAP Container. For example, `entrypoint: "/bin/echo Hello"`.
- cpu: Integer value which defines the CPU limit assigned to the MAP container. This value can not be less than 1. For example, `cpu: 1`.
- memory: Integer value in Megabytes which defines the Memory limit assigned to the MAP container. This value can not be less than 256. For example, `memory: 8192`.
- gpu: Integer value which defines the number of GPUs assigned to the MAP container. This value can not be less than 0. For example, `gpu: 0`.
- inputPath: Input directory path of MAP Container. For example, `inputPath: "/var/monai/input"`. An environment variable `MONAI_INPUTPATH` is mounted in the MAP container with it's value equal to the one provided for this field.
- outputPath: Output directory path of MAP Container. For example, `outputPath: "/var/monai/output"`. An environment variable `MONAI_OUTPUTPATH` is mounted in the MAP container with it's value equal to the one provided for this field.
- modelPath: Model directory path of MAP Container. For example, `modelPath: "/opt/monai/models"`. This is an optional field. An environment variable `MONAI_MODELPATH` is mounted in the MAP container with it's value equal to the one provided for this field.

### Helm Chart Deployment

In order to install the helm chart, please run:
```bash
helm install monai ./charts
```

##  Submitting inference requests
####  Making a request with `curl`

With MIS running, a user can make an inference request to the service using the `/upload` POST endpoint with the **cluster IP** and **Port** from running `kubectl get svc` and a compressed .zip file containing all the input payload files (eg. input.zip)

#### Usage:


curl -X 'POST' 'http://`INSERT CLUSER IP & PORT HERE`/upload/'
&nbsp; &nbsp;  &nbsp;  &nbsp; -H 'accept: application/json'
&nbsp; &nbsp;  &nbsp;  &nbsp; -H 'Content-Type: multipart/form-data'
&nbsp; &nbsp;  &nbsp;  &nbsp; -F 'file=@`PATH TO INPUT PAYLOAD ZIP`;type=application/x-zip-compressed'
&nbsp; &nbsp;  &nbsp;  &nbsp; -o output.zip

For example,
```bash
curl -X 'POST' 'http://10.97.138.32:8000/upload/' \
   -H 'accept: application/json' \
   -H 'Content-Type: multipart/form-data' \
   -F 'file=@input.zip;type=application/x-zip-compressed' \
   -o output.zip
```

To view the FastAPI generated UI for an instance of MIS, have the service running and then on any browser, navigate to `http://CLUSTER IP:PORT/docs` (eg. http://10.97.138.32:8000/docs)
