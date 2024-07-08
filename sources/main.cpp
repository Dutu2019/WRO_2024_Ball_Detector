#include <stdio.h>
#include <chrono>
#include <opencv2/opencv.hpp>
using namespace std;

float distance(float x1, float x2, float y1, float y2);

int main(int argc, char **argv) {
    int frameWidth = 48;
    int frameHeight = 48;

    cv::Scalar orangeLow = cv::Scalar(22 / 2, 70.0 / 100.0 * 255, 45.0 / 100.0 * 255);
    cv::Scalar orangeHigh = cv::Scalar(26 / 2, 90.0 / 100.0 * 255, 90.0 / 100.0 * 255);
    cv::Mat colorFrame, grayFrame, hsvFrame, mask;
    cv::VideoCapture camera;
    camera.open(0);

     //--- GRAB AND WRITE LOOP
    cout << "Start grabbing" << endl
    << "Press any key to terminate" << endl;
    auto start = chrono::high_resolution_clock::now();
    for (;;)
    {   
        auto frameStart = chrono::high_resolution_clock::now();
        camera.read(colorFrame);
        // check if we succeeded
        if (colorFrame.empty()) {
            cerr << "ERROR! blank frame grabbed\n";
            break;
        }

        // Apply filters to video stream
        cv::cvtColor(colorFrame, hsvFrame, cv::COLOR_BGR2HSV);

        vector<vector<cv::Point>> contours;
        cv::inRange(hsvFrame, orangeLow, orangeHigh, mask);
        cv::findContours(mask, contours, cv::RETR_EXTERNAL, cv::CHAIN_APPROX_SIMPLE);
        // cv::drawContours(colorFrame, contours, -1, (255, 0, 0), 3);
        for (int i = 0; i < contours.size(); i++) {
            cv::Rect boundRect = cv::boundingRect(contours[i]);
            if (boundRect.area() > 270) {
                cv::rectangle(colorFrame, boundRect.tl(), boundRect.br(), (255, 0, 0), 3);
            }
        }
        if (chrono::duration_cast<chrono::milliseconds>(chrono::high_resolution_clock::now() - start).count() > 1000) {
            auto stop = chrono::high_resolution_clock::now();
            auto duration = chrono::duration_cast<chrono::milliseconds>(stop - frameStart);
            start = stop;
            printf("FPS: %d\n", 1000/duration.count());
        }
        cv::imshow("Live", colorFrame);
        if (cv::waitKey(1) >= 0) break;
    }
    camera.release();
    cv::destroyAllWindows();
    return 0;
}

float distance(float x1, float x2, float y1, float y2) {
    return (x1-x2)*(x1-x2) + (y1-y2)*(y1-y2);
}