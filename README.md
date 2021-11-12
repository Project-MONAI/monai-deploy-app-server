# MONAI Deploy Application Server

Application server that will run [MAPs](https://github.com/Project-MONAI/monai-deploy/blob/main/guidelines/monai-application-package.md) (MONAI Application Package).

First version's (v0.1) scope will include a basic component called the MONAI Inference Service ([MIS](./components/inference-service/README.md)).

MIS is a RESTful Service which supports [MONAI workloads](https://github.com/Project-MONAI/monai-deploy/blob/main/guidelines/monai-workloads.md#synchronous-computational-workload) that can be completed within the timeframe of a single HTTP request/response.