import json
import time

import paho.mqtt.client as mqtt

file = open("brokerConfig.json")
broker_config = json.load(file)
file.close()

HOST = broker_config["broker_host"]
PORT = broker_config["broker_port"]

REGISTER_STATUS = "device/register/response/"
LIGHT_DEVICES = "device/light/"
REGISTER_DEVICE = "device/register"
DEVICE_REGISTER_MSG = "device/register_status"
DEVICE_STATUS = "device/status"

class Light_Device():

    # setting up the intensity choices for Smart Light Bulb  
    _INTENSITY = ["LOW", "HIGH", "MEDIUM", "OFF"]

    def __init__(self, device_id, room):
        # Assigning device level information for each of the devices. 
        self._device_id = device_id
        self._room_type = room
        self._light_intensity = self._INTENSITY[0]
        self._device_type = "LIGHT"
        self._switch_status = "OFF"
        self._DEVICE_ID_TOPIC = "device/" + self._device_id + "/"
        self._ROOM_TOPIC = "device/" + self._room_type + "/"
        self._device_registration_flag = False
        self.client = mqtt.Client(self._device_id)  
        self.client.on_connect = self._on_connect  
        self.client.on_message = self._on_message
        self.client.connect(HOST, PORT, keepalive=60)  
        self.client.loop_start()  
        self._register_device(self._device_id, self._room_type, self._device_type)

    def _register_device(self, device_id, room_type, device_type):
        while not self.client.is_connected():
            pass
        message = dict()
        message['device_id'] = device_id
        message['room_type'] = room_type
        message['device_type'] = device_type
        self.client.publish(REGISTER_DEVICE, json.dumps(message))

    # Connect method to subscribe to various topics. 
    def _on_connect(self, client, userdata, flags, result_code):
        if result_code == 0:
            while not self.client.is_connected():
                pass
            self.client.subscribe(REGISTER_STATUS + self._device_id)
            self.client.subscribe(self._DEVICE_ID_TOPIC)
            self.client.subscribe(self._ROOM_TOPIC)
            self.client.subscribe(LIGHT_DEVICES)
        else:
            print(f'Bad connection for {self._device_type}_instance "{self._device_id}" with result code={str(result_code)}')
            if result_code == 4:
                print("MQTT server is unavailable. Please start MQTT server and try again.")
    # method to process the recieved messages and publish them on relevant topics
    # this method can also be used to take the action based on received commands
    def _on_message(self, client, userdata, msg):
        received_message = (msg.payload.decode("utf-8")).split(',')
        # Publishing registartion status
        if msg.topic == (REGISTER_STATUS + self._device_id):
            self._device_registration_flag = True
            light_device_register = dict()
            light_device_register['device_id'] = self._device_id
            light_device_register['registered_status'] = self._device_registration_flag
            light_device_register['msg'] = "LIGHT-DEVICE Registered!"
            self.client.publish(DEVICE_REGISTER_MSG, json.dumps(light_device_register))

        # Performing get or control operation based on the request received for direct device_id, device_type, or room_type
        elif msg.topic in [self._DEVICE_ID_TOPIC, LIGHT_DEVICES, self._ROOM_TOPIC]:
            if received_message[0] == 'get':
                # Status will be published at the end for set type message as well
                pass
            elif received_message[0] in ("ON", "OFF"):
                self._set_switch_status(received_message[0])
            elif type(received_message[0] == str):
                if self._switch_status != 'ON':
                    self._set_switch_status("ON")
                self._set_light_intensity(received_message[0])

            # Creating the payload to publish the status of the devices.
            light_device_status = dict()
            light_device_status['device_id'] = self._device_id
            light_device_status['switch_state'] = self._get_switch_status()
            light_device_status['intensity'] = self._get_light_intensity()
            self.client.publish(DEVICE_STATUS, json.dumps(light_device_status))

    # Getting the current switch status of devices
    def _get_switch_status(self):
        return self._switch_status

    # Setting the the switch of devices
    def _set_switch_status(self, switch_state):
        self._switch_status = switch_state

    # Getting the light intensity for the devices
    def _get_light_intensity(self):
        return self._light_intensity

    # Setting the light intensity for devices
    def _set_light_intensity(self, light_intensity):
        if light_intensity.upper() in self._INTENSITY:
            self._light_intensity = light_intensity.upper()
        elif light_intensity.isnumeric():
            pass
        else:
            print("\nIntensity Change FAILED. Invalid Light Intensity level received")