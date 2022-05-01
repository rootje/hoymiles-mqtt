# Hoymiles-mqtt-server

This program will connect to the Hoymiles webservice and gather the energy information from it. The program is configurable through a .env configuration file. Use the following parameters in order to configure:

- USERNAME: the username used for logging in on the Hoymiles website
- USERPASSWORD: the password used for logging in on the Hoymiles website
- MQTT_HOST_ADDRESS: an ip-address or dns hostname on which to reach the mqtt server
- MQTT_USERNAME: username used to login to the mqtt server
- MQTT_PASSWORD: password used to login to the mqtt server
- MQTT_PORT: the ip port on which the mqtt server is listening
- API_FREQUENCY_CHECK: interval (in seconds) in between queries (default value is 900 seconds, do not make the interval too small for a too long period of time or you might get banned from the Hoymiles API). The Hoymiles API gets updated every 15 minutes by Hoymiles anyway.

I use it for filling a couple of basic Home Assistant MQTT Sensors so that these can be used in the Energy dashboard or for other visualisations or automations. 

## Docker-compose

There is a docker container available on the docker hub for your convenience. The following docker-compose.yml can be used to run the container easily:

```
version: '3.4'

services:
  hoymiles-mqtt:
    container_name: hoymiles-mqtt
    image: rgardeniers/hoymiles-mqtt:latest
    volumes:
    - ./env/.env:/app/.env
    - /etc/timezone:/etc/timezone:ro
    - /etc/localtime:/etc/localtime:ro
    restart: always
    network_mode: host
```


Just put this docker-compose.yml file in a directory, create a subdirectory "env" and place a file in it called ".env" with the correct parameters.

## Home Assistant variables

In the configuration.yaml file just add a couple of sensors that this program put on the MQTT queue like so:

```
  - platform: mqtt
    name: hoymiles_energy_lifetime_energy
    state_topic: "hoymiles/energy_lifetime_energy"
    unit_of_measurement: "kWh"
    value_template: "{{ value | float / 1000 }}"
    device_class: energy
    icon: mdi:solar-power
```

To use the above sensor in the Energy dashboard add

```
    state_class: total
```

But of course you can use this program/container for other purposes!
