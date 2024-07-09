#include <stdio.h>
#include <iostream>
#include <chrono>
#include <opencv2/core.hpp>
#include <opencv2/imgproc.hpp>
#include <opencv2/videoio.hpp>
#include <opencv2/highgui.hpp>
using namespace std;

float distance(float x1, float x2, float y1, float y2);
void incrementFrame();

int frameCount = 0;
auto frameStart = chrono::high_resolution_clock::now();
int main(int argc, char **argv) {
    int frameWidth = 48;
    int frameHeight = 48;

    cv::Scalar orangeLow = cv::Scalar(33.0 / 2.0, 70.0 / 100.0 * 255, 50.0 / 100.0 * 255);
    cv::Scalar orangeHigh = cv::Scalar(42.0 / 2.0, 100.0 / 100.0 * 255, 100.0 / 100.0 * 255);
    cv::Mat colorFrame, hsvFrame, mask;
    cv::VideoCapture camera;
    camera.open(0);

     //--- GRAB AND WRITE LOOP
    cout << "Start grabbing" << endl
    << "Press any key to terminate" << endl;

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
        if (cv::waitKey(1) >= 0) break;
    }
    camera.release();
    cv::destroyAllWindows();
    return 0;
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