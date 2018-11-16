# load-test-iot-core
## Introduction
The repo contains example code to execute performance tests that compare between HTTP and MQTT. The tests are performed against API endpoints that are exposed by Google Cloud IoT Core. The tests simulate a virtual device that sends telemetry events to Google Cloud IoT Core. The [locust.io](https://locust.io/) framework is utilized to perform the tests as well as gathering and presenting the test results.

## Implementation
The implementation in `httpClient.py`file adapts the POST request sent by HttpLocust by adding the JWT in request headers. This is needed to authenticate against the [Cloud IoT Core - HTTP Bridge](https://cloud.google.com/iot/docs/how-tos/http-bridge). The telemetry events is delivered to Cloud IoT Core by calling the [publishEvent](https://cloud.google.com/iot/docs/reference/cloudiotdevice/rest/v1/projects.locations.registries.devices/publishEvent) endpoint with payload data.

For the MQTT part of the test, a [custom locust client](https://docs.locust.io/en/stable/testing-other-systems.html) is implemented using the [paho mqtt python client](https://www.eclipse.org/paho/clients/python/docs/) to properly interact with [Cloud IoT Core - MQTT Bridge](https://cloud.google.com/iot/docs/how-tos/mqtt-bridge). The client handles connect and disconnect to MQTT server and is capable of sending multiple events. The time it takes to conduct each of the steps are measured and is sent to locust.io by triggering the `request_success` and `request_failure` events.

## What is being tested
For event publishing through HTTP the request and response time is measured for each event.
For the MQTT case because of the protocol is publish/subscribe oriented there is a connection establishing process between the client and the server before event could be published. So we choose to measure the connect and disconnect time together with the event publishing time, as the total time it takes to publish event. We also choose to send the events with [QoS 1](https://www.hivemq.com/blog/mqtt-essentials-part-6-mqtt-quality-of-service-levels) which guarantees at least once delivery through a `PUBACK` response which matches the HTTP request and response cycle.
With a established MQTT connection multiple events could be send, we choose to measure the time it takes to send 1, 10, 100 and 1000 events between one connect/disconnect cycle.

## Environment setup
We assume you already have a GCP project setup with an IoT Core registry created, and inside of registry there's a device created with a public/private key pair stored in you local environment.
Follow the [Getting Started](https://cloud.google.com/iot/docs/how-tos/getting-started) and [Creating Registries and Devices](https://cloud.google.com/iot/docs/how-tos/devices) to create this prerequisite cloud environment.
Following steps are all done on your local environment where the tests will be conducted.

### Local Prerequisites
- Git
- Python 2.7

Clone the repoistory:
```bash
git clone https://github.com/GoogleCloudPlatform/iot-core-load-test-python.git
cd iot-core-load-test-python
```
### Download the google root certificate
```bash
curl https://pki.google.com/roots.pem > roots.pem
```
### Set environment variables
```bash
cp set_env_template set_env.sh
```
Put in the proper values for you setup by editing then `set_env.sh` file and set the variables
```bash
source set_env.sh
```
### Install dependent Python libraries
```bash
virtualenv env && source env/bin/activate
pip install -r requirements.txt
```
## Execute the tests

### MQTT
Start locust with the MQTT client
```bash
locust --no-reset-stats -f mqttClient.py
```
Open the web interface at http://127.0.0.1:8089/ and choose the number of simulated user and ramp up pace to execute the test.

### HTTP
Start locust with the HTTP client
```bash
locust --host='https://cloudiotdevice.googleapis.com/v1' -f httpClient.py
```
Open the web interface at http://127.0.0.1:8089/ and choose the number of simulated user and ramp up pace to execute the test.

