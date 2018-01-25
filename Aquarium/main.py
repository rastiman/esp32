import machine
from umqtt.robust import MQTTClient

with open('config.json') as config_file:
    config = json.load(config_file)

mqtt = MQTTClient(config["device_name"], config["mqtt_server"],
                  user=config["mqtt_user"], password=config["mqtt_pass"])

rel1 = machine.Pin(12, machine.Pin.OUT)
rel2 = machine.Pin(14, machine.Pin.OUT)
rel3 = machine.Pin(27, machine.Pin.OUT)

def set_device():
    with open('setting.json') as setting_file:
        setting = json.load(setting_file)
        


print ("do nothing")