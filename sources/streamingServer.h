#ifndef streamingServer
#define streamingServer
#include "mongoose.h"
#include <iostream>
#include <opencv2/core.hpp>
#include <opencv2/highgui.hpp>

void HTTPServer(cv::Mat *colorFrame, mg_mgr *mgr);
static void ev_handler(struct mg_connection *c, int ev, void *ev_data, cv::Mat *colorFrame);

#endif