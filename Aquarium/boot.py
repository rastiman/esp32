import json
import network
from time import ticks_ms, sleep, sleep_ms

with open('config.json') as config_file:
    config = json.load(config_file)

sta = network.WLAN(network.STA_IF)

def wifi_connect(timeout=20):
    """Connect to WiFi with timeout [s]."""
    sta.active(True)
    sta.connect(config["wifi_ssid"], config["wifi_pass"])
    attempt = 0
    print("Connecting to WiFi.", end="")
    while not sta.isconnected():
        sleep(1)
        attempt += 1
        print(".", end="")
        if attempt > timeout:
            sta.disconnect()
            print("\nConnection could NOT be established!")
            break
    if sta.isconnected():
        print("\nConnected to WiFi")

wifi_connect()
