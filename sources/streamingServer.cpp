#include "streamingServer.h"

void HTTPServer(cv::Mat *colorFrame, mg_mgr *mgr) {
    // Initialize Mongoose server
    mg_mgr_init(mgr);
    const char *url = "http://0.0.0.0:8000";
    struct mg_connection *c = mg_http_listen(mgr, url, (mg_event_handler_t) ev_handler, colorFrame);
    
    if (c == NULL) {
        std::cerr << "Error: Cannot start server on port " << url << std::endl;
    }

    // Enter Mongoose event loop
    while (true) {
        mg_mgr_poll(mgr, 1000);
    }
}

// Function to handle HTTP requests
void ev_handler(struct mg_connection *c, int ev, void *ev_data, cv::Mat *colorFrame) {
    if (ev == MG_EV_HTTP_MSG) {
        struct mg_http_message *hm = (struct mg_http_message *) ev_data;

        // Check if the request is for the frame buffer
        if (mg_match(hm->uri, mg_str("/frame"), NULL)) {
            std::vector<uchar> buf;
            cv::Mat colorFrameCopy;
            printf("Yes");
            colorFrame->copyTo(colorFrameCopy);
            cv::imencode(".jpg", colorFrameCopy, buf);  // Encode cv::Mat to JPEG
            std::string jpeg_data(buf.begin(), buf.end());
            // Create and send the HTTP response with explicit content length
            mg_printf(c,
                "HTTP/1.1 200 OK\r\n"
                "Content-Type: image/jpeg\r\n"
                "Content-Length: %d\r\n"
                "\r\n", (int)jpeg_data.size());
            mg_send(c, jpeg_data.data(), jpeg_data.size());
            
        } else {
            // Handle other requests or send a 404 Not Found response
            mg_http_reply(c, 404, "", "Not Found");
        }
    }
}