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

app = FastAPI()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--payload', type=str, required=True)
    args = parser.parse_args()

    config.load_incluster_config()


if __name__ == "__main__":
    main()
