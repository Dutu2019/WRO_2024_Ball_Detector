import cv2 as cv
import numpy as np
import http.server as sr
import time, json, threading
from sys import platform

if platform == "linux":
    import pigpio

camera = cv.VideoCapture(0)
colorFrame = None

try:
    with open("HSV.json", "r") as file:
        obj = json.load(file)
        orangeLow = obj["orangeLow"]
        orangeHigh = obj["orangeHigh"]
        temperature = obj["temperature"]
except Exception:
    orangeLow = [0, 0, 0]
    orangeHigh = [0, 0, 0]
    temperature = 0
orangeLowOpenCV   = np.array(( orangeLow[0] / 2, orangeLow[1] / 100 * 255, orangeLow[2] / 100 * 255), dtype=np.uint8, ndmin=1)
orangeHighOpenCV   = np.array(( orangeHigh[0] / 2, orangeHigh[1] / 100 * 255, orangeHigh[2] / 100 * 255), dtype=np.uint8, ndmin=1)

ip = "0.0.0.0"
port = 8000
ball_coords = []
lock = threading.Lock()

I2C_ADDR = 0x12
SDA = 18
SCL = 19

class Server(sr.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.path = '/index.html'
            return sr.SimpleHTTPRequestHandler.do_GET(self)
        elif self.path == '/stream':
            self.send_response(200)
            self.send_header('Content-Type', 'multipart/x-mixed-replace; boundary=frame')
            self.end_headers()
            while True:
                try:
                    buffer = cv.imencode(".jpg", colorFrame)[1]
                    # Write the boundary string before each part
                    self.wfile.write(b'--frame\r\n')
                    self.send_header('Content-Type', 'image/jpeg')
                    self.end_headers()
                    self.wfile.write(bytes(buffer))
                    self.wfile.write(b'\r\n')
                    
                    # Sleep to simulate a frame rate
                    time.sleep(0.1)
                except Exception as e:
                    print(f"Exception: {e}")
                    break
        elif self.path == "/getHSV":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(bytes(json.dumps({"orangeLow": orangeLow, "orangeHigh": orangeHigh}), "UTF-8"))
        else:
            self.send_error(404, "File not found")
    
    def do_POST(self):
        global orangeLow, orangeHigh, orangeLowOpenCV, orangeHighOpenCV, temperature
        if self.path == '/':
            content_length = int(self.headers['Content-Length'])
            if content_length > 0:
                post_data_bytes = self.rfile.read(content_length)

                post_data_str = post_data_bytes.decode("UTF-8")
                list_of_post_data = post_data_str.split('&')
                
                post_data_dict = {}
                for item in list_of_post_data:
                    variable, value = item.split('=')
                    post_data_dict[variable] = value
                
            if len(post_data_dict) == 7:
                orangeLow = [
                    float(post_data_dict["H_low"]),
                    float(post_data_dict["S_low"]),
                    float(post_data_dict["V_low"]),
                ]
                orangeHigh = [
                    float(post_data_dict["H_high"]),
                    float(post_data_dict["S_high"]),
                    float(post_data_dict["V_high"]),
                ]
                orangeLowOpenCV = np.array(( orangeLow[0] / 2, orangeLow[1] / 100 * 255, orangeLow[2] / 100 * 255), dtype=np.uint8, ndmin=1)
                orangeHighOpenCV = np.array(( orangeHigh[0] / 2, orangeHigh[1] / 100 * 255, orangeHigh[2] / 100 * 255), dtype=np.uint8, ndmin=1)

                temperature = int(post_data_dict["temperature"])
                calibrate_camera(camera)

                with open("HSV.json", "w") as file:
                    json.dump({"orangeLow": orangeLow, "orangeHigh": orangeHigh, "temperature": temperature}, file)
            self.send_response(301)
            self.send_header("Location", "/")
            self.end_headers()

numFrames = 0
lastFrameTimestamp = time.perf_counter()
def incrementFrames() -> None:
    global lastFrameTimestamp, numFrames
    numFrames += 1
    if time.perf_counter() - lastFrameTimestamp >= 1:
        print(f"FPS: {numFrames}")
        numFrames = 0
        lastFrameTimestamp = time.perf_counter()

def calibrate_camera(camera: cv.VideoCapture) -> None:
    with lock:
        camera.set(cv.CAP_PROP_FRAME_WIDTH, 600)
        camera.set(cv.CAP_PROP_FRAME_HEIGHT, 600)
        camera.set(cv.CAP_PROP_AUTO_WB, 1)
        # camera.set(cv.CAP_PROP_AUTO_WB, 0)
        # camera.set(cv.CAP_PROP_WB_TEMPERATURE, temperature)
        camera.set(cv.CAP_PROP_SATURATION, 200)
        camera.set(cv.CAP_PROP_APERTURE, 8)

def main() -> None:
    global colorFrame, ball_coords
    calibrate_camera(camera)


    while True:
        with lock:
            if not camera.isOpened():
                print("Cannot open camera")
                break
            ret, colorFrame = camera.read()
            colorFrame = cv.GaussianBlur(colorFrame, (17, 17), 1.3, sigmaY=0.0)
            hsvFrame = cv.cvtColor(colorFrame, cv.COLOR_BGR2HSV)

            # Get Bounding boxes of balls
            mask = cv.inRange(hsvFrame, orangeLowOpenCV, orangeHighOpenCV)
            contours, src = cv.findContours(mask, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
            ball_coords = []
            for contour in contours:
                x, y, w, h = cv.boundingRect(contour)
                if w * h > 270:
                    cv.rectangle(colorFrame, (x, y), (x+w, y+h), (0, 255, 0), 3)
                    ball_coords.append((x, y))
            
            incrementFrames()

def i2c_callback(id, tick):
    global pi
    s, b, d = pi.bsc_i2c(I2C_ADDR)
    if b > 1:
        if d[1] == ord("t"):
            if len(ball_coords) > 0:
                pi.bsc_i2c(I2C_ADDR, f"{ball_coords[0][0]} {ball_coords[0][1]}\n")
            else:
                pi.bsc_i2c(I2C_ADDR, "NULL")

if __name__ == "__main__":
    if platform == "linux":
        pi = pigpio.pi()
        pi.set_pull_up_down(SDA, pigpio.PUD_UP)
        pi.set_pull_up_down(SCL, pigpio.PUD_UP)
        pi.event_callback(pigpio.EVENT_BSC, i2c_callback)
        pi.bsc_i2c(I2C_ADDR)
        print("I2C active")

    server = sr.HTTPServer((ip, port), Server)
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.daemon = True
    server_thread.start()
    main()
