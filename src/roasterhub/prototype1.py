from os import uname
import serial
import time


# com port for linux os
def serial_print_arduino():
    os_name = uname()[0]
    ArduinoUnoSerial = serial.Serial('/dev/ttyACM0', 115200)
    if os_name == 'Linux':
        ArduinoUnoSerial = serial.Serial('/dev/ttyACM0', 115200)

    print(ArduinoUnoSerial.readline())
    print("You have new message from Arduino")
    while True:
        time.sleep(3)
        print(ArduinoUnoSerial.readline())


if __name__ == '__main__':
    serial_print_arduino()
