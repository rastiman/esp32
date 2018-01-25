import machine
from umqtt.robust import MQTTClient
import onewire 
import ds18x20 

with open('config.json') as config_file:
    config = json.load(config_file)

mqtt = MQTTClient(config["device_name"], config["mqtt_server"],
                  user=config["mqtt_user"], password=config["mqtt_pass"])



rel1 = machine.Pin(12, machine.Pin.OUT)
rel2 = machine.Pin(14, machine.Pin.OUT)
rel3 = machine.Pin(27, machine.Pin.OUT)

ow = onewire.OneWire(machine.Pin(19))

#rtc = machine.RTC()

sensors = ds18x20.DS18X20(ow)

# scan for devices on the bus
roms = sensors.scan()
print('Found devices:', roms)

def set_device():
    with open('setting.json') as setting_file:
        setting = json.load(setting_file)

def measure():
    """Perform DS18B20 measurement and return json message to publish."""
    sensors.convert_temp()
    sleep_ms(750)
    temperature = [sensors.read_temp(t) for t in sensors.scan()]
    try:
        print("Temp: " + str(temperature[0]) + chr(176) + "C")
        return json.dumps({'temp': temperature[0]})
    except IndexError:
        print("Sensor Error!")

measure()