#ifndef impulse
#define impulse

#include <stdio.h>
#include "edge-impulse-sdk/classifier/ei_run_classifier.h"

unsigned char *bufp;
static int get_signal_data(size_t offset, size_t length, float *out_ptr);
namespace dutu {
    void run_inference(unsigned char &buffer, int size) {
        // --INFERENCE--
        // Raw features copied from test sample (Edge Impulse > Model testing)
        bufp = &buffer;
        int buf_len = size;
        signal_t signal;            // Wrapper for raw input buffer
        ei_impulse_result_t result; // Used to store inference output
        EI_IMPULSE_ERROR res;       // Return code from inference

        // Assign callback function to fill buffer used for preprocessing/inference
        signal.total_length = buf_len;
        signal.get_data = &get_signal_data;

        // Perform DSP pre-processing and inference
        res = run_classifier(&signal, &result, false);

        // Print return code and how long it took to perform inference
        printf("run_classifier returned: %d\r\n", res);
        printf("Timing: DSP %d ms, inference %d ms, anomaly %d ms\r\n", 
                result.timing.dsp, 
                result.timing.classification, 
                result.timing.anomaly);

        // Print the prediction results (object detection)
    #if EI_CLASSIFIER_OBJECT_DETECTION == 1
        printf("Object detection bounding boxes:\r\n");
        for (uint32_t i = 0; i < EI_CLASSIFIER_OBJECT_DETECTION_COUNT; i++) {
            ei_impulse_result_bounding_box_t bb = result.bounding_boxes[i];
            if (bb.value == 0) {
                continue;
            }
            printf("  %s (%f) [ x: %u, y: %u, width: %u, height: %u ]\r\n", 
                    bb.label, 
                    bb.value, 
                    bb.x, 
                    bb.y, 
                    bb.width, 
                    bb.height);
        }
    #endif
    }

}

// Callback: fill a section of the out_ptr buffer when requested
static int get_signal_data(size_t offset, size_t length, float *out_ptr) {
    for (size_t i = 0; i < length; i++) {
        out_ptr[i] = (bufp + offset)[i];
    }

    return EIDSP_OK;
}
#endif