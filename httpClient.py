#!/usr/bin/env python

# Copyright 2018 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from locust import HttpLocust, TaskSet, task
import base64
import json
import os
import utilities


def create_publish_url(project_id, cloud_region, registry_id, device_id):
    return ('/projects/{}/locations/{}/registries/{}/devices/{}:{}').format(
    project_id, cloud_region, registry_id, device_id, 'publishEvent')

def generatePayload(numberOfFields):
    payload = {}
    for i in range(1, numberOfFields+1):
        iStr = "%03d" % (i,)
        payload['field'+iStr] = 'payload_value_'+iStr
    return json.dumps(payload)

def create_send_body(payload_size):
    msg_bytes = base64.urlsafe_b64encode(generatePayload(payload_size).encode('utf-8'))
    body = {'binary_data': msg_bytes.decode('ascii')}
    return json.dumps(body)

def create_headers(project_id, private_key_file, algorithm):
    return {
        'authorization': 'Bearer {}'.format(utilities.create_jwt(project_id, private_key_file, algorithm).decode('ascii')),
        'content-type': 'application/json',
        'cache-control': 'no-cache'
    }

class Device(HttpLocust):

    class task_set(TaskSet):
        project_id = os.environ.get('PROJECT_ID')
        registry_id = os.environ.get('REGISTRY_ID')
        device_id = os.environ.get('DEVICE_ID')
        private_key_file = os.environ.get('PRIVATE_KEY_FILE')
        cloud_region = os.environ.get('CLOUD_REGION')
        ca_certs = os.environ.get('CA_CERTS')
        algorithm = os.environ.get('ALGORITHM')
        payload_size = int(os.environ.get('PAYLOAD_SIZE'))
        min_wait = 1
        max_wait = 1
        publish_url = create_publish_url(project_id, cloud_region, registry_id, device_id)
        send_body = create_send_body(payload_size)
        headers = create_headers(project_id, private_key_file, algorithm)

        @task(1)
        def send_one(self):
            self.client.post(self.publish_url, self.send_body, headers=self.headers)

