#include <civetweb.h>

cv::Mat frame;
cv::VideoCapture cap(0);
bool stop_stream = false;

int request_handler(struct mg_connection *conn, void *cbdata) {
    if (stop_stream) {
        return 500; // Stop streaming
    }

    std::vector<uchar> buffer;
    cv::imencode(".jpg", frame, buffer);
    mg_printf(conn, "HTTP/1.1 200 OK\r\n"
                    "Content-Type: image/jpeg\r\n"
                    "Content-Length: %d\r\n"
                    "Connection: keep-alive\r\n"
                    "\r\n", buffer.size());
    mg_write(conn, buffer.data(), buffer.size());
    return 200;
}

void* capture_frames(void* arg) {
    while (!stop_stream) {
        cap >> frame;
        if (frame.empty()) {
            stop_stream = true;
        }
        cv::waitKey(30);
    }
    return nullptr;
}

int main() {
    if (!cap.isOpened()) {
        std::cerr << "Error opening camera" << std::endl;
        return -1;
    }

    const char *options[] = {
        "document_root", ".",
        "listening_ports", "8080",
        0
    };

    struct mg_callbacks callbacks;
    memset(&callbacks, 0, sizeof(callbacks));
    struct mg_context *ctx = mg_start(&callbacks, 0, options);
    mg_set_request_handler(ctx, "/video_feed", request_handler, 0);

    pthread_t capture_thread;
    pthread_create(&capture_thread, 0, capture_frames, 0);

    std::cout << "Server started on http://localhost:8080/video_feed" << std::endl;
    std::cout << "Press Enter to stop the server..." << std::endl;
    std::cin.get();
    stop_stream = true;

    pthread_join(capture_thread, 0);
    mg_stop(ctx);

    return 0;
}