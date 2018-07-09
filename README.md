# HDS-821PR MQTT 
MQTT Bridge for HDS-821PR HDMI Picture in Picture (PiP) Scaler

This docker uses python module hds_821pr. 
[Github](https://github.com/ragingcomputer/hds_821pr) / [Pypi](https://pypi.org/project/hds-821pr/)

### MQTT Control
Assuming your `MQTT_ROOT` is set to `pipswitch` this docker subscribes to `pipswitch/cmnd/mode` and `pipswitch/cmnd/input`

##### Switch Mode:
Send mqtt message to `pipswitch/cmnd/mode`

Valid modes: `single`, `pip`, `side_full`, and `side_scale`. 
See [module documentation](https://github.com/ragingcomputer/hds_821pr/blob/master/docs/hex_commands.md#mode) for more info.


##### Switch Input:
Send mqtt message to `pipswitch/cmnd/input`

Valid inputs: `1` and `2`
See [module documentation](https://github.com/ragingcomputer/hds_821pr/blob/master/docs/hex_commands.md#input) for more info.


## Docker Image

The only important parts are configuring the MQTT server and passing the serial device into the container.

#### Required Environment Variables:
* SERIAL_PORT = Serial interface to communicate with HDS-821PR
* MQTT_SERVER = Address of MQTT server

#### Optional Environment Variables:
* MQTT_USERNAME = username for MQTT server. Not required if no server auth
* MQTT_PASSWORD = password for MQTT server
* MQTT_ROOT = path to begin MQTT topic path. Default pipswitch
* MQTT_CLIENT_NAME = client identifier for MQTT client. Only important when using multiple instances. Default pipswitch


### docker run

```console
sudo docker run -d \
      --name mqtt_pip \
      --restart=always \
      --device=/dev/ttyS0 \
      -e MQTT_SERVER="192.168.0.10" \
      -e MQTT_USERNAME="mqttusername" \
      -e MQTT_PASSWORD="P4ssw0rd" \
      -e SERIAL_PORT="/dev/ttyS0" \
      ragingcomputer/hds-821pr-mqtt

```

### docker-compose

```yaml
version: '3'

services:

  mqtt_pip:
    image: ragingcomputer/hds-821pr-mqtt
    container_name: "mqtt_pip"
    restart: always
    devices:
      - /dev/ttyS0:/dev/ttyS0
    environment:
      - MQTT_SERVER="192.168.0.10"
      - MQTT_USERNAME="mqttusername"
      - MQTT_PASSWORD="P4ssw0rd"
      - SERIAL_PORT="/dev/ttyS0"
```

# Home Assistant Example

In this example, I have an input_select that lists a dash character "-" and the available modes. I can drop down and select the mode to send mqtt and change on the device.

I have a timer to reset the mode after 45 seconds, assuming the notification is no longer relevant.

There are 3 automations.

hdmi_pip_mode listens for state change on the input_select. If it isn't "-", send the mode over mqtt and reset the active item to "-"

hdmi_pip_display_pip listens for state change of my doorbell. When activated, it changes the input_select to pip mode, activating the first automation. it then starts the timer.

hdmi_pip_hide_pip listens for the timer to end. When the timer ends, it changes the input_select to single mode, activating the first automation.

#### excerpts from configuration.yaml

```yaml
input_select:
  hdmi_pip_select:
    name: HDMI PIP
    icon: mdi:tablet
    initial: "-"
    options:
    - "-"
    - single
    - pip
    - side_full
    - side_scale

timer:
  # timer to reset input after doorbell displayed
  doorbell_notification:
    duration: '00:00:45'

automation:
  - id: hdmi_pip_mode
    alias: HDMI PiP Mode
    trigger:
      platform: state
      entity_id: input_select.hdmi_pip_select
    condition:
      condition: template
      value_template: '{{ not is_state("input_select.hdmi_pip_select", "-") }}'
    action:
    - service: mqtt.publish
      data:
        topic: 'pipswitch/cmnd/mode'
        payload_template: '{{ states("input_select.hdmi_pip_select") }}'
    - service: input_select.select_option
      data:
        entity_id: input_select.hdmi_pip_select
        option: "-"

  - id: hdmi_pip_display_pip
    alias: Display PiP
    trigger:
      platform: state
      entity_id: binary_sensor.door_bell
      to: 'on'
    action:
    - service: input_select.select_option
      data:
        entity_id: input_select.hdmi_pip_select
        option: "pip"
    - service: timer.start
      entity_id: timer.doorbell_notification

  - id: hdmi_pip_hide_pip
    alias: Hide PiP
    trigger:
      platform: event
      event_type: timer.finished
      event_data:
        entity_id: timer.doorbell_notification
    action:
    - service: input_select.select_option
      data:
        entity_id: input_select.hdmi_pip_select
        option: "single"
```

