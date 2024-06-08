#include <cstring>
#include <iostream>
#include <vector>
#include <nvjpeg.h>
#include <cuda_runtime.h>
#include "cpp-base64/base64.h"

nvjpegHandle_t nvjpeg_handle;
nvjpegEncoderState_t nvjpeg_state;
nvjpegEncoderParams_t nvjpeg_params;
nvjpegImage_t nvjpeg_image;

extern "C" {
    void initialize_nvjpeg() {
        nvjpegCreateSimple(&nvjpeg_handle);
        nvjpegEncoderStateCreate(nvjpeg_handle, &nvjpeg_state, 0);
        nvjpegEncoderParamsCreate(nvjpeg_handle, &nvjpeg_params, 0);
    }

    void encode_image(unsigned char* d_image, int width, int height, char** base64_output) {
        nvjpeg_image.channel[0] = d_image;
        nvjpeg_image.pitch[0] = width * 3;

        nvjpegEncodeImage(nvjpeg_handle, nvjpeg_state, nvjpeg_params, &nvjpeg_image, NVJPEG_INPUT_RGB, width, height, 0);

        size_t length;
        nvjpegEncodeRetrieveBitstream(nvjpeg_handle, nvjpeg_state, NULL, &length, 0);

        std::vector<char> jpeg_output(length);
        nvjpegEncodeRetrieveBitstream(
            nvjpeg_handle,
            nvjpeg_state,
            (unsigned char*) jpeg_output.data(),
            &length,
            0
        );

        std::string base64_encoded = base64_encode(reinterpret_cast<const unsigned char*>(jpeg_output.data()), jpeg_output.size());

        *base64_output = (char*)malloc(base64_encoded.size() + 1);
        strcpy(*base64_output, base64_encoded.c_str());
    }

    void cleanup_nvjpeg() {
        nvjpegEncoderStateDestroy(nvjpeg_state);
        nvjpegEncoderParamsDestroy(nvjpeg_params);
        nvjpegDestroy(nvjpeg_handle);
    }
}
