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
import time
import ssl
import json
import sys
import os
import utilities
from locust import Locust, TaskSet, events, task
import paho.mqtt.client as mqtt

class IoTCoreMQTTClient(object):
    mqtt_bridge_hostname = 'mqtt.googleapis.com'
    mqtt_bridge_port = 8883

    def __init__(self, project_id, registry_id, device_id, private_key_file, cloud_region, ca_certs, algorithm, payload_size):
        self.device_id = device_id
        self.payload_size = payload_size

        self.client = mqtt.Client(
            client_id=('projects/{}/locations/{}/registries/{}/devices/{}'
                   .format(
                           project_id,
                           cloud_region,
                           registry_id,
                           device_id)))
        self.client.username_pw_set(
            username='unused',
            password=utilities.create_jwt(
                project_id, private_key_file, algorithm))

        self.client.tls_set(ca_certs=ca_certs, tls_version=ssl.PROTOCOL_TLSv1_2)

    def connect_to_server(self):
        start_time = time.time()
        try:
            self.client.connect(self.mqtt_bridge_hostname, self.mqtt_bridge_port)
        except NameError as e:
            total_time = int((time.time() - start_time) * 1000)
            events.request_failure.fire(request_type="mqtt_connect", name='connect', response_time=total_time, exception=e)
        else:
            total_time = int((time.time() - start_time) * 1000)
            events.request_success.fire(request_type="mqtt_connect", name='connect', response_time=total_time, response_length=0)

    def disconnect_from_server(self):
        start_time = time.time()
        try:
            self.client.disconnect()
        except NameError as e:
            total_time = int((time.time() - start_time) * 1000)
            events.request_failure.fire(request_type="mqtt_disconnect", name='disconnect', response_time=total_time, exception=e)
        else:
            total_time = int((time.time() - start_time) * 1000)
            events.request_success.fire(request_type="mqtt_disconnect", name='disconnect', response_time=total_time, response_length=0)

    def generate_payload(self):
        payload = {}
        for i in range(1, self.payload_size+1):
            iStr = "%03d" % (i,)
            payload['field'+iStr] = 'payload_value_'+iStr
        return json.dumps(payload)

    def send_event(self, numberOfMsg):
        mqtt_topic = '/devices/{}/events'.format(self.device_id)
        payload = self.generate_payload()
        start_time = time.time()
        try:
            self.client.reconnect()
            self.client.loop_start()
            for i in range(1, numberOfMsg+1):
                msgInfo = self.client.publish(mqtt_topic, payload, qos=1)
                msgInfo.wait_for_publish()
            self.client.disconnect()
        except ValueError as e:
            total_time = int((time.time() - start_time) * 1000)
            events.request_failure.fire(request_type="mqtt_payload", name='event'+str(numberOfMsg), response_time=total_time, exception=e)
        else:
            total_time = int((time.time() - start_time) * 1000)
            events.request_success.fire(request_type="mqtt_payload", name='event'+str(numberOfMsg), response_time=total_time, response_length=0)

class MQTTLocust(Locust):
    def __init__(self, *args, **kwargs):
        super(MQTTLocust, self).__init__(*args, **kwargs)
        self.client = IoTCoreMQTTClient(
            self.project_id,
            self.registry_id,
            self.device_id,
            self.private_key_file,
            self.cloud_region,
            self.ca_certs,
            self.algorithm,
            self.payload_size)

class Device(MQTTLocust):
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

    class task_set(TaskSet):
        def on_start(self):
            self.client.connect_to_server()
            self.client.disconnect_from_server()

        @task(1)
        def send_one(self):
            self.client.send_event(1)

        @task(1)
        def send_ten(self):
            self.client.send_event(10)

        @task(1)
        def send_hundred(self):
            self.client.send_event(100)

        @task(1)
        def send_thousand(self):
            self.client.send_event(1000)

