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

try:
    import usocket as socket
except:
    import socket


CONTENT = b"""\
HTTP/1.0 200 OK
Hello #%d from MicroPython!
"""

def main(micropython_optimize=False):
    s = socket.socket()

    # Binding to all interfaces - server will be accessible to other hosts!
    ai = socket.getaddrinfo("0.0.0.0", 8080)
    print("Bind address info:", ai)
    addr = ai[0][-1]

    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(addr)
    s.listen(5)
    print("Listening, connect your browser to http://<this_host>:8080/")

    counter = 0
    while True:
        res = s.accept()
        client_sock = res[0]
        client_addr = res[1]
        print("Client address:", client_addr)
        print("Client socket:", client_sock)

        if not micropython_optimize:
            # To read line-oriented protocol (like HTTP) from a socket (and
            # avoid short read problem), it must be wrapped in a stream (aka
            # file-like) object. That's how you do it in CPython:
            client_stream = client_sock.makefile("rwb")
        else:
            # .. but MicroPython socket objects support stream interface
            # directly, so calling .makefile() method is not required. If
            # you develop application which will run only on MicroPython,
            # especially on a resource-constrained embedded device, you
            # may take this shortcut to save resources.
            client_stream = client_sock

        print("Request:")
        req = client_stream.readline()
        print(req)
        while True:
            h = client_stream.readline()
            if h == b"" or h == b"\r\n":
                break
            print(h)
        client_stream.write(CONTENT % counter)

        client_stream.close()
        if not micropython_optimize:
            client_sock.close()
        counter += 1
        print()


main()
