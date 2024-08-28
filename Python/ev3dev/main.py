#!/usr/bin/env pybricks-micropython
from pybricks.hubs import EV3Brick
from pybricks.parameters import Port
from pybricks.ev3devices import Motor
from pybricks.iodevices import I2CDevice
from pybricks.parameters import Direction
import time

# Create your objects here.
ev3 = EV3Brick()
rpi = I2CDevice(Port.S1, 0x12)
LMotor = Motor(Port.A)
RMotor = Motor(Port.B)
print("Connected to device ")

def extract_coords(rx: bytes) -> tuple|None:
    rx = rx.decode()
    if not rx[0].isdigit(): return
    rx = rx.split(" ")
    ret = []
    for coord in rx[0:2]:
        temp = ""
        for c in coord:
            try:
                int(c)
                temp += c
            except Exception:
                break
        ret.append(int(temp))
    return tuple(ret)

ball_coords = []
while True:
    try:
        print(rpi.read(0, 15))
        rpi.write(0, b't')
        rx = rpi.read(0, 15)
        ball_coords = extract_coords(rx)
        if ball_coords:
            ballx = ball_coords[0]
            print(ballx)
            LMotor.run(ballx/2)
            RMotor.run((600-ballx)/2)
        else:
            LMotor.stop()
            RMotor.stop()
    except Exception:
        pass
    time.sleep(0.01)
