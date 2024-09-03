#!/usr/bin/env pybricks-micropython
from pybricks.hubs import EV3Brick
from pybricks.parameters import Port
from pybricks.ev3devices import Motor
from pybricks.iodevices import I2CDevice
from pybricks.parameters import Direction
import time

class Robot():
    def __init__(self) -> None:
        # Global variables
        self.FOV_width = 600
        self.FOV_height = 800
        self.max_speed = 100
        self.ball_coords = []
        self.ev3 = EV3Brick()
        self.rpi = I2CDevice(Port.S1, 0x12)
        self.LMotor = Motor(Port.A)
        self.RMotor = Motor(Port.B)
        print("Connected to device ")
    
    def extract_coords(self, rx: bytes) -> tuple|None:
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

    def set_ball_coords(self) -> None:
        try_again = 0
        while try_again < 10:
            try:
                self.rpi.write(0, b't')
                ball_coords = self.extract_coords(self.rpi.read(0, 15))
                if ball_coords:
                    if ball_coords[0] < self.FOV_width and ball_coords[1] < self.FOV_height:
                        self.ball_coords = ball_coords
                    return
                else:
                    try_again += 1
            except Exception:
                try_again += 1
        self.ball_coords = []
    
    def update_motors(self) -> None:
        if len(self.ball_coords) > 0:
            self.LMotor.run(max((self.ball_coords[0] - self.FOV_width//2) * 2*self.max_speed/self.FOV_width, 0))
            self.RMotor.run(max((self.FOV_width//2 - self.ball_coords[0]) * 2*self.max_speed/self.FOV_width, 0))
        else:
            self.LMotor.brake()
            self.RMotor.brake()

if __name__ == "__main__":
    robot = Robot()
    while True:
        robot.set_ball_coords()
        robot.update_motors()