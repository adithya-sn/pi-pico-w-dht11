"""
DHT11 with Pi Pico W
"""

import wlan_cfg
import network, rp2, time
import urequests
import ntptime
from machine import Pin
from dht import DHT11

## WLAN config
# Set your WiFi Country
rp2.country("IN")
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
# Set power mode to get WiFi power-saving off (if needed)
wlan.config(pm=0xA11140)
wlan.connect(wlan_cfg.SSID, wlan_cfg.PASSWORD)

while not wlan.isconnected() and wlan.status() >= 0:
    print("Waiting to connect:")
    time.sleep(1)

print(f"Connected {wlan.ifconfig()}.")

## Set time as this board does not have RTC
ntptime.settime()

## Sensor stuff
dht_pin = Pin(28, Pin.OUT, Pin.PULL_DOWN)  ## Pin 34/GPIO28
sensor = DHT11(dht_pin)

influxdb_host = "http://172.0.0.201:8086"

while True:
    epoch_time = int(time.time())
    url_string = influxdb_host + "/write?db=dht11"
    temp = str(sensor.temperature)
    humidity = str(sensor.humidity)
    print(f"Temp: {temp}\tHumidity: {humidity}")
    ## Push to InfluxDB
    if temp and humidity:
        data_string_temp = (
            f"room_temperature,sensor=dht11 value={temp} "
            + str(epoch_time)
            + "000000000"
        )
        data_string_humidity = (
            f"room_humidity,sensor=dht11 value={humidity} "
            + str(epoch_time)
            + "000000000"
        )
        try:
            r_t = urequests.post(url_string, data=data_string_temp)
            r_t.close()
            if not str(r_t.status_code).startswith("2"):
                print(f"Failed to push data to InfluxDB due to {r_t.text}")
            r_h = urequests.post(url_string, data=data_string_humidity)
            r_h.close()
            if not str(r_h.status_code).startswith("2"):
                print(f"Failed to push data to InfluxDB due to {r_h.text}")
        except Exception as e:
            print(f"Failed to push data to InfluxDB due to {e}")
    else:
        print(f"No data from sensor, skipping InfluxDB push.")
    ## How frequently you get data
    time.sleep(1800)
