## Overview
As data scientists & application developers build AI models they need a way to deploy these applications in production. MONAI Inference Service will be used to deploy a MONAI application. This proposal documents the requirements for the MONAI Inference Service (MIS).

## Goal
The goal for this proposal is to enlist, prioritize and provide clarity on the requirements for MIS. Developers working on different software modules in MIS SHALL use this specification as a guideline when designing and implementing software for the Service.

## Success Criteria
MIS SHALL provide a REST based RPC API for client to communicate with.

MIS SHALL support configuration of the [MONAI Application Package(MAP)](https://github.com/Project-MONAI/monai-deploy/blob/main/guidelines/monai-application-package.md]) used to service inference requests. 

MIS SHALL provide an API to upload datasets to perform inferencing on.

MIS SHALL return inference results as part of the response to the originating inference request.

## Requirements

### Support for Specific MONAI Workloads
MIS SHALL support [MONAI workloads](https://github.com/Project-MONAI/monai-deploy/blob/main/guidelines/monai-workloads.md#synchronous-computational-workload) which can be completed within the timeframe of a single HTTP request/response.

### Deployable on MONAI Operating Environments
MIS SHALL run on Staging Server and Production Server environments as defined in [MONAI Operating Environments](https://github.com/Project-MONAI/monai-deploy/blob/main/guidelines/MONAI-Operating-Environments.md).

### API Interface
MIS SHALL provide a REST based RPC API which utilizes the functionality of the HTTP transport.

### Consistent and Robust Logging
MIS SHALL provide consistent and robust logging about its operations.

### Register single MAP configuration before MIS startup
MIS SHALL allow clients to provide MAP configuration as part of MIS' deployment configuration.

### Fulfill an inference request with uploaded file inputs
MIS SHALL fulfill an inference request with uploaded file inputs.

### Provision resources for an inference request
MIS SHALL provision CPU, memory, and GPU resources for an inference request as defined in the configuration.

### Provide results of inference request
MIS SHALL provide results of inference request as a part of the response to the request.

### SHALL NOT persist request inputs or inference results
MIS SHALL NOT persist inference request inputs or inference results beyond the lifetime of the originating inferencing request

## Limitations
MIS SHALL service inference requests one at a time.
