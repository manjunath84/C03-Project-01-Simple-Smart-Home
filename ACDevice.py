
import json
import paho.mqtt.client as mqtt

file = open("brokerConfig.json")
broker_config = json.load(file)
file.close()

HOST = broker_config["broker_host"]
PORT = broker_config["broker_port"]

REGISTER_STATUS = "device/register/response/"
AC_DEVICES = "device/ac/"
REGISTER_DEVICE = "device/register"
DEVICE_REGISTER_MSG = "device/register_status"
DEVICE_STATUS = "device/status"

class AC_Device():
    
    _MIN_TEMP = 18  
    _MAX_TEMP = 32  

    def __init__(self, device_id, room):
        
        self._device_id = device_id
        self._room_type = room
        self._temperature = 22
        self._device_type = "AC"
        self._device_registration_flag = False
        self._switch_status = "OFF"
        self._DEVICE_ID_TOPIC = "device/" + self._device_id + "/"
        self._ROOM_TOPIC = "device/" + self._room_type + "/"
        self.client = mqtt.Client(self._device_id)  
        self.client.on_connect = self._on_connect  
        self.client.on_message = self._on_message
        self.client.connect(HOST, PORT, keepalive=60)
        self.client.loop_start()  
        self._register_device(self._device_id, self._room_type, self._device_type)

    # calling registration method to register the device
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
            self.client.subscribe(REGISTER_STATUS+self._device_id)
            self.client.subscribe(self._DEVICE_ID_TOPIC)
            self.client.subscribe(self._ROOM_TOPIC)
            self.client.subscribe(AC_DEVICES)
        else:
            print(f'Bad connection for {self._device_type} instance "{self._device_id}" with result code : {str(result_code)}')
            if result_code == 4:
                print("MQTT server is unavailable. Please start MQTT server and try again.")

    # method to process the recieved messages and publish them on relevant topics 
    # this method can also be used to take the action based on received commands
    def _on_message(self, client, userdata, msg): 
        received_message = (msg.payload.decode("utf-8")).split(",")
        # Publishing registration status

        if msg.topic == (REGISTER_STATUS + self._device_id):
            self._device_registration_flag = True
            ac_device_register = dict()
            ac_device_register['device_id'] = self._device_id
            ac_device_register['registered_status'] = self._device_registration_flag
            ac_device_register['msg'] = "AC-DEVICE Registered!"
            self.client.publish(DEVICE_REGISTER_MSG, json.dumps(ac_device_register))

        # Performing get or control operation based on the request received for direct device_id, device_type, or room_type
        elif msg.topic in [self._DEVICE_ID_TOPIC, AC_DEVICES, self._ROOM_TOPIC]:
            if received_message[0] == 'get':
                # Status will be published at the end for set type message as well
                pass
            elif received_message[0] in ("ON", "OFF"):
                self._set_switch_status(received_message[0])
            elif type(received_message[0] == int):
                if self._switch_status != 'ON':
                    self._set_switch_status("ON")
                self._set_temperature(received_message[0])

                # Creating the payload to publish the status of the devices.
            ac_device_state = dict()
            ac_device_state['device_id'] = self._device_id
            ac_device_state['switch_state'] = self._get_switch_status()
            ac_device_state['temperature'] = self._get_temperature()
            self.client.publish(DEVICE_STATUS, json.dumps(ac_device_state))

    # Getting the current switch status of devices 
    def _get_switch_status(self):
        return self._switch_status

    # Setting the the switch of devices
    def _set_switch_status(self, switch_state):
        self._switch_status = switch_state

    # Getting the temperature for the devices
    def _get_temperature(self):
        return self._temperature

    # Setting up the temperature of the devices
    def _set_temperature(self, temperature):
        if temperature.isnumeric() and (self._MIN_TEMP <= int(temperature) <= self._MAX_TEMP):
            self._temperature = int(temperature)

        elif (temperature.isalpha()):
            pass
        else:
            print("\nTemperature Change FAILED. Invalid temperature value received")
    
