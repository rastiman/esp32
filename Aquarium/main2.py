import machine
from umqtt.robust import MQTTClient
import onewire 
import ds18x20 
import json

with open('config.json') as config_file:
    config = json.load(config_file)

mqtt = MQTTClient(config["device_name"], config["mqtt_server"],
                  user=config["mqtt_user"], password=config["mqtt_pass"])


rtc = machine.RTC()

#rel1 = machine.Pin(12, machine.Pin.OUT)
#rel2 = machine.Pin(13, machine.Pin.OUT)
#rel3 = machine.Pin(14, machine.Pin.OUT)

ow = onewire.OneWire(machine.Pin(5))
ow.reset()


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

def mqtt_publish():
    """Connect to MQTT broker, publish message and disconnect again."""
    try:
        mqtt.connect()
        mqtt.publish(config["mqtt_temp_topic"].encode("utf-8"),
                     measure().encode("utf-8"), retain=True)
        mqtt.disconnect()
        print("Message successfully published in topic " +
              config["mqtt_temp_topic"])
    except:
        print("Message NOT published!")


def wifi_disconnect():
    """Disonnect from WiFi."""
    if sta.isconnected():
        sta.disconnect()
    sta.active(False)
    print("WiFi disconnected")


def go_sleep(sleep_minutes):
    """Perform deepsleep to save energy."""
    rtc = machine.RTC()
    rtc.irq(trigger=rtc.ALARM0, wake=machine.DEEPSLEEP)
    # ticks_ms is used to make wake up period more consistent
    sleep_seconds = (sleep_minutes * 60) - (ticks_ms() // 1000)
    rtc.alarm(rtc.ALARM0, sleep_seconds * 1000)
    print(str(sleep_seconds // 60) +
          ":" + str(sleep_seconds % 60) +
          " minutes deep sleep NOW!")
    machine.deepsleep()


wifi_connect()
mqtt_publish()
wifi_disconnect()
go_sleep(config["wakeup_period"])
