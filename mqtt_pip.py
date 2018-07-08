#!/usr/bin/env python3
import hds_821pr
import time
import os
import logging
import paho.mqtt.client as mqtt


logging.basicConfig(level=logging.DEBUG)

class PipBridge():

    def __init__(self, device, mqtt_server, mqtt_username, mqtt_password,
                 mqtt_root='pipswitch', mqtt_client_name='pipswitch'):

        self.pip = hds_821pr.Hex(device)
        self.pip.reset()
        self.pip.set_pip_size(hds_821pr.pip_sizes.large)
        self.pip.set_pip_position(hds_821pr.pip_positions.top_right)
        self.pip.set_pip_border(hds_821pr.pip_borders.hide)

        self.mqtt_root = mqtt_root

        print("Starting MQTT")
        self.client = mqtt.Client(mqtt_client_name)
        self.client.on_message = self.on_message
        self.client.on_connect = self.on_connect
        print("Connecting to Broker: " + mqtt_server)
        self.client.username_pw_set(mqtt_username, mqtt_password)
        self.client.connect(mqtt_server)

        self.client.loop_start()

        # keep_looping is the control variable.
        # If it is False, loop stops, program cleans up and exits
        self.keep_looping = True
        self.update_timer = 0
        self.command_active = False
        update_interval = 180

        while self.keep_looping:
            if self.update_timer >= update_interval:
                self.update_config()

            self.update_timer += 1
            if not self.command_active:
                self.pip.get_serial_response()
            time.sleep(1)

        self.client.loop_stop()

    def on_connect(self, client, userdata, flags, rc):
        print("Connected with result code "+str(rc))
        # Subscribing in on_connect() means that if we lose the connection and
        # reconnect then subscriptions will be renewed.
        topic = self.mqtt_root + '/cmnd/+'
        print("Subscribing to topic ", topic)
        client.subscribe(topic)

    def on_message(self, client, userdata, message):
        print("Message received: ", str(message.payload.decode("utf-8")))
        print("-Userdata: ", userdata)
        print("-Topic: ", message.topic)
        print("-QOS: ", message.qos)
        print("-Retain: ", message.retain)

        topic_string = message.topic[len(self.mqtt_root) + 1:]
        attrib = str(topic_string.split('/')[1])
        value = str(message.payload.decode("utf-8"))
        print(attrib, value)

        if attrib == 'mode':
            self.set_mode(value)

        if attrib == 'input':
            self.set_input(value)

        self.update_config()

    def set_mode(self, value):
        if value == hds_821pr.modes.single:
            self.pip.set_mode(hds_821pr.modes.single)
        elif value == hds_821pr.modes.pip:
            self.pip.set_mode(hds_821pr.modes.pip)
        elif value == hds_821pr.modes.side_scale:
            self.pip.set_mode(hds_821pr.modes.side_scale)
        elif value == hds_821pr.modes.side_full:
            self.pip.set_mode(hds_821pr.modes.side_full)
        elif value == 'reset':
            self.pip.reset()
            self.pip.set_pip_size(hds_821pr.pip_sizes.large)
            self.pip.set_pip_position(hds_821pr.pip_positions.top_right)
            self.pip.set_pip_border(hds_821pr.pip_borders.hide)
        else:
            print('invalid mode')

    def set_input(self, value):
        if value in ['1', '2']:
            self.pip.set_port(value)
        else:
            print('invalid input')

    def update_config(self):
        self.command_active = True
        self.client.publish(self.mqtt_root + '/stat/mode', self.pip.get_mode())
        time.sleep(.1)
        self.client.publish(self.mqtt_root + '/stat/input', self.pip.get_port())
        self.update_timer = 0
        self.command_active = False


# Get environment variables
SERIAL_PORT = os.getenv('SERIAL_PORT', '/dev/ttyS0')
MQTT_SERVER = os.getenv('MQTT_SERVER', 'iot.eclipse.org')
MQTT_USERNAME = os.getenv('MQTT_USERNAME')
MQTT_PASSWORD = os.getenv('MQTT_PASSWORD')
MQTT_ROOT = os.getenv('MQTT_ROOT', 'pipswitch')
MQTT_CLIENT_NAME = os.getenv('MQTT_CLIENT_NAME', 'pipswitch')

# Create an instance of PipBridge
PipBridge(SERIAL_PORT, MQTT_SERVER, MQTT_USERNAME, MQTT_PASSWORD, mqtt_root=MQTT_ROOT, mqtt_client_name=MQTT_CLIENT_NAME)
