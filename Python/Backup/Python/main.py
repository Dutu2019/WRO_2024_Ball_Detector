import cv2 as cv
import numpy as np
import http.server as sr
import time, threading, pigpio

colorFrame = None
lastFrameTimestamp = time.perf_counter()
numFrames = 0
ball_coords = []

I2C_ADDR = 0x12
SDA = 18
SCL = 19

def i2c_callback(id, tick):
    global pi
    s, b, d = pi.bsc_i2c(I2C_ADDR)
    if b > 1:
        if d[1] == ord("t"):
            if len(ball_coords) > 0:
                pi.bsc_i2c(I2C_ADDR, f"{ball_coords[0][0]} {ball_coords[0][1]}\n")
            else:
                pi.bsc_i2c(I2C_ADDR, "NULL")

class Server(sr.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/stream':
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
                    time.sleep(0.05)
                except Exception as e:
                    print(f"Exception: {e}")
                    break
        else:
            self.send_error(404, "File not found")

def incrementFrames() -> None:
    global lastFrameTimestamp, numFrames
    numFrames += 1
    if time.perf_counter() - lastFrameTimestamp >= 1:
        print(f"FPS: {numFrames}")
        numFrames = 0
        lastFrameTimestamp = time.perf_counter()

def main() -> None:
    global colorFrame, ball_coords
    # orangeLow = [33, 70, 50]
    # orangeHigh = [42, 100, 100]
    orangeLow = [20, 70, 50]
    orangeHigh = [50, 100, 100]
    orangeLowOpenCV   = np.array(( orangeLow[0] / 2, orangeLow[1] / 100 * 255, orangeLow[2] / 100 * 255), dtype=np.uint8, ndmin=1)
    orangeHighOpenCV   = np.array(( orangeHigh[0] / 2, orangeHigh[1] / 100 * 255, orangeHigh[2] / 100 * 255), dtype=np.uint8, ndmin=1)

    camera = cv.VideoCapture(0)
    camera.set(cv.CAP_PROP_FRAME_WIDTH, 720)
    camera.set(cv.CAP_PROP_FRAME_HEIGHT, 480)
    while True:
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
        print(ball_coords)
        incrementFrames()

        if cv.waitKey(1) >= 0: break


if __name__ == "__main__":
    server = sr.HTTPServer(("0.0.0.0", 8000), Server)
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.daemon = True
    server_thread.start()

    pi = pigpio.pi()
    pi.set_pull_up_down(SDA, pigpio.PUD_UP)
    pi.set_pull_up_down(SCL, pigpio.PUD_UP)
    pi.event_callback(pigpio.EVENT_BSC, i2c_callback)
    pi.bsc_i2c(I2C_ADDR)
    print("I2C active")

    main()
