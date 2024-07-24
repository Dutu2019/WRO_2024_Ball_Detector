#include <stdio.h>
#include <iostream>
#include <fstream>
#include <thread>
#include <chrono>
#include "mongoose.h"
#include <opencv2/core.hpp>
#include <opencv2/imgproc.hpp>
#include <opencv2/videoio.hpp>
#include <opencv2/highgui.hpp>
using namespace std;

void HTTPServer();
static void ev_handler(struct mg_connection *c, int ev, void *ev_data);
void incrementFrame();
float distance(float x1, float x2, float y1, float y2);

// For HTTP Server
struct mg_mgr mgr;

int frameCount = 0;
auto frameStart = chrono::high_resolution_clock::now();
cv::Mat colorFrame, hsvFrame, mask;
int main(int argc, char **argv) {
    // Color range for orange ping pong ball
    cv::Scalar orangeLow = cv::Scalar(33.0 / 2.0, 70.0 / 100.0 * 255, 50.0 / 100.0 * 255);
    cv::Scalar orangeHigh = cv::Scalar(42.0 / 2.0, 100.0 / 100.0 * 255, 100.0 / 100.0 * 255);
    cv::VideoCapture camera;
    camera.open(0);

     //--- GRAB AND WRITE LOOP
    cout << "Start grabbing" << endl
    << "Press any key to terminate" << endl;


    std::thread httpServer(HTTPServer);

    for (;;)
    {   
        camera.read(colorFrame);
        // check if we succeeded
        if (colorFrame.empty()) {
            cerr << "ERROR! blank frame grabbed\n";
            break;
        }
        // Apply filters to video stream
        cv::GaussianBlur(colorFrame, colorFrame, cv::Size(17, 17), 1.3, 0.0);
        cv::cvtColor(colorFrame, hsvFrame, cv::COLOR_BGR2HSV);

        // Get Bounding boxes of balls
        vector<vector<cv::Point>> contours;
        cv::inRange(hsvFrame, orangeLow, orangeHigh, mask);
        cv::findContours(mask, contours, cv::RETR_EXTERNAL, cv::CHAIN_APPROX_SIMPLE);
        for (int i = 0; i < contours.size(); i++) {
            cv::Rect boundRect = cv::boundingRect(contours[i]);
            if (boundRect.area() > 270) {
                cv::rectangle(colorFrame, boundRect.tl(), boundRect.br(), (255, 0, 0), 3);
            }
        }

        incrementFrame();
        cv::imshow("Live", colorFrame);
        if (cv::waitKey(1) >= 0) break;
    }
    mg_mgr_free(&mgr);
    camera.release();
    cv::destroyAllWindows();
    return 0;
}

void HTTPServer() {
    // Initialize Mongoose server
    mg_log_set(MG_LL_DEBUG);
    mg_mgr_init(&mgr);
    const char *url = "http://0.0.0.0:8000";
    struct mg_connection *c = mg_http_listen(&mgr, url, (mg_event_handler_t) ev_handler, NULL);
    
    if (c == NULL) {
        std::cerr << "Error: Cannot start server on port " << url << std::endl;
    }

    // Enter Mongoose event loop
    while (true) {
        mg_mgr_poll(&mgr, 1000);
    }
}

// Function to handle HTTP requests
void ev_handler(struct mg_connection *c, int ev, void *ev_data) {
    if (ev == MG_EV_HTTP_MSG) {
        struct mg_http_message *hm = (struct mg_http_message *) ev_data;

        // Check if the request is for the frame buffer
        if (mg_match(hm->uri, mg_str("/frame"), NULL)) {
            std::vector<uchar> buf;
            // mg_printf(c,
            //     "HTTP/1.1 200 OK\r\n"
            //     "Content-Type: text/html\r\n"
            //     "Content-Length: 5\r\n\r\n");

            mg_printf(c,
                "HTTP/1.1 200 OK\r\n"
                "Content-Type: multipart/x-mixed-replace; boundary=frame\r\n\r\n");
            
            while (true) {
                try {
                    cv::imencode(".jpg", colorFrame, buf);  // Encode cv::Mat to JPEG
                    std::string jpeg_data(buf.begin(), buf.end());
                    mg_printf(c,
                        "--frame\r\n"
                        "Content-Type: image/jpeg\r\n"
                        // "Content-Length: %s\r\n"
                        // "\r\n", jpeg_data.size() + 2
                    );
                    mg_send(c, jpeg_data.data(), jpeg_data.size());
                    mg_send(c, "\r\n", 2);
                    std::this_thread::sleep_for(std::chrono::milliseconds(50));
                    
                } catch (...) {
                    printf("User disconnected");
                }
            }
            
        } else {
            // Handle other requests or send a 404 Not Found response
            mg_http_reply(c, 404, "", "Not Found");
        }
    }
}

void incrementFrame() {
    auto stop = chrono::high_resolution_clock::now();
    auto duration = chrono::duration_cast<chrono::milliseconds>(stop - frameStart);
    if (duration.count() >= 1000) {
        printf("FPS: %d\n", frameCount);
        frameCount = 0;
        frameStart = stop;
    }
    frameCount++;
}

float distance(float x1, float x2, float y1, float y2) {
    return (x1-x2)*(x1-x2) + (y1-y2)*(y1-y2);
}