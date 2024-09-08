#!/usr/bin/env pybricks-micropython
from pybricks.hubs import EV3Brick
from pybricks.parameters import Port
from pybricks.ev3devices import Motor, GyroSensor
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
        self.FOV_height = 480
        self.max_speed = 500

        self.search_speed = 100
        self.search_countdown = time.perf_counter()
        self.search_countdown_is_set = False

        self.chase_adjust_speed = 100
        self.ball_is_close = False
        self.is_chasing = False
        self.ball_coords = []
        self.ball_coords_try_again = 0

        # Return
        self.return_angles = []
        self.chase_start_times = []
        self.chase_end_times = []

        self.ev3 = EV3Brick()
        self.rpi = I2CDevice(Port.S1, 0x12)

        self.LMotor = Motor(Port.A)
        self.RMotor = Motor(Port.B)
        self.MMotor = Motor(Port.C)
        self.Gyro = GyroSensor(Port.S2, Direction.COUNTERCLOCKWISE)
        self.Gyro.reset_angle(0)
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
        try:
            self.rpi.write(0, b't')
            ball_coords = self.extract_coords(self.rpi.read(0, 8))
            if ball_coords:
                if ball_coords[0] < self.FOV_width and ball_coords[1] < self.FOV_height:
                    self.ball_coords = ball_coords
                    self.ball_coords_try_again = 0
                return
            else:
                self.ball_coords_try_again += 1
        except Exception:
            self.ball_coords_try_again += 1
        
        if self.ball_coords_try_again > 5:
            self.ball_coords = []

    def run_motors(self, LSpeed: float, RSpeed: float) -> None:
        self.LMotor.run(LSpeed)
        self.RMotor.run(RSpeed)

    def update_motors_V2(self) -> None:
        if len(self.ball_coords) > 0:
            self.run_motors(
                -self.search_speed * (self.ball_coords[0] - self.FOV_width//2) * 2/self.FOV_width,
                -self.search_speed * (self.FOV_width//2 - self.ball_coords[0]) * 2/self.FOV_width
            )
            if self.ball_coords[0] > self.FOV_width//2 - 15 and self.ball_coords[0] < self.FOV_width//2 + 15:
                if not self.search_countdown_is_set:
                    self.search_countdown = time.perf_counter()
                    self.search_countdown_is_set = True
                if time.perf_counter() - self.search_countdown > .5:
                    self.is_chasing = True
                    self.return_angles.append(self.Gyro.angle())
                    self.chase_start_times.append(time.perf_counter())
        else:
            self.LMotor.stop()
            self.RMotor.stop()
    
    def turnAngle(self, angle) -> None:
        while not (self.Gyro.angle() > angle-7 and self.Gyro.angle() < angle+7):
            self.run_motors(
                -self.max_speed * (angle-self.Gyro.angle())/60,
                -self.max_speed * (self.Gyro.angle()-angle)/60
            )
        self.LMotor.hold()
        self.RMotor.hold()

    def throw_ball(self) -> None:
        self.chase_end_times.append(time.perf_counter())
        robot.MMotor.run(-180)
        self.LMotor.run_angle(-self.max_speed//2, 180, wait=False)
        self.RMotor.run_angle(-self.max_speed//2, 180)
        self.LMotor.run_angle(self.max_speed, 180, wait=False)
        self.RMotor.run_angle(self.max_speed, 180)
        self.turnAngle(30)
        time.sleep(1.3)
        robot.MMotor.stop()
        self.ball_is_close = False
        self.is_chasing = False
        self.return_to_start()

    def chase_ball(self) -> None:
        if len(self.ball_coords) > 0:
            self.run_motors(
                -self.max_speed - self.chase_adjust_speed * (self.ball_coords[0]/self.FOV_width),
                -self.max_speed - self.chase_adjust_speed * (1 - self.ball_coords[0]/self.FOV_width)
            )
            if self.ball_coords[1] > 5/6 * self.FOV_height:
                self.ball_is_close = True
        elif self.ball_is_close:
            self.throw_ball()
        else:
            self.is_chasing = False
            self.chase_end_times.append(time.perf_counter())

    def search_ball(self) -> None:
        pass
    
    def return_to_start(self) -> None:
        print("angles:", self.return_angles)
        if len(self.return_angles) == len(self.chase_start_times) and len(self.chase_start_times) == len(self.chase_end_times):
            return_lenth = len(self.return_angles)
            for i in range(return_lenth):
                self.turnAngle(self.return_angles[return_lenth-1 - i])
                self.run_motors(self.max_speed, self.max_speed)
                time.sleep(
                    self.chase_end_times[return_lenth-1 - i] - self.chase_start_times[return_lenth-1 - i]
                )
            self.return_angles = []
            self.chase_start_times = []
            self.chase_end_times = []
        else:
            print("Cannot return because differents list lengths")

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
        if robot.is_chasing:
            robot.chase_ball()
        else:
            robot.update_motors_V2()
        # incrementFrames()