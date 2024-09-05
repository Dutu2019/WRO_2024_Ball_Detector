#!/usr/bin/env pybricks-micropython
from pybricks.hubs import EV3Brick
from pybricks.parameters import Port
from pybricks.ev3devices import Motor
from pybricks.iodevices import I2CDevice
from pybricks.parameters import Direction
import time

lastFrameTimestamp = time.perf_counter()
numFrames = 0

def time_taken(func):
    def wrapper(*args):
        start = time.perf_counter()
        func(*args)
        end = time.perf_counter()
        print("Time taken:", end - start)
    return wrapper

class Robot():
    def __init__(self) -> None:
        # Global variables
        self.FOV_width = 600
        self.FOV_height = 500
        self.max_speed = 200
        self.ball_coords = []
        self.ev3 = EV3Brick()
        self.rpi = I2CDevice(Port.S1, 0x12)
        self.LMotor = Motor(Port.A)
        self.RMotor = Motor(Port.B)
        print("Connected to device ")
    
    def extract_coords(self, rx: bytes) -> tuple|None:
        rx = rx.decode()
        for i in range(3):
            if i == 3: return
            if not rx[0].isdigit(): rx = rx[1:]
            else: break
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
        while try_again < 5:
            try:
                self.rpi.write(0, b't')
                RPI_bytes = self.rpi.read(0, 8)
                ball_coords = self.extract_coords(RPI_bytes)
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
            self.LMotor.run(self.max_speed * (self.ball_coords[0]/self.FOV_width)**2)
            self.RMotor.run(self.max_speed * (1 - self.ball_coords[0]/self.FOV_width)**2)
        else:
            self.LMotor.brake()
            self.RMotor.brake()

def incrementFrames() -> None:
    global lastFrameTimestamp, numFrames
    numFrames += 1
    if time.perf_counter() - lastFrameTimestamp >= 1:
        print("FPS:", numFrames)
        numFrames = 0
        lastFrameTimestamp = time.perf_counter()

if __name__ == "__main__":
    robot = Robot()
    while True:
        robot.set_ball_coords()
        if robot.ball_coords[1] > 5/6 * robot.FOV_height:
            # Spin meduim motor
            robot.RMotor.run_angle(robot.max_speed//2, 180, wait=False)
            robot.LMotor.run_angle(robot.max_speed//2)
        robot.update_motors()
        # incrementFrames()