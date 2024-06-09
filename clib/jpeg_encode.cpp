/*
    JPEG conversion using CUDA nvJPEG

    This uses the cuda runtime nad the nvJPEG cuda library to 
    take in RGB arrays and convert them to JPEG.

*/
#include <cstring>
#include <iostream>
#include <vector>
#include <nvjpeg.h>
#include <cuda_runtime.h>

nvjpegHandle_t nvjpeg_handle;
nvjpegEncoderState_t nvjpeg_state;
nvjpegEncoderParams_t nvjpeg_params;
nvjpegImage_t nvjpeg_image;
cudaStream_t stream;

const char* get_nvjpeg_error_string(nvjpegStatus_t status) {
    switch (status) {
        case NVJPEG_STATUS_SUCCESS:
            return "The API call returned with no errors.";
        case NVJPEG_STATUS_NOT_INITIALIZED:
            return "The library was not initialized with nvjpegCreate().";
        case NVJPEG_STATUS_INVALID_PARAMETER:
            return "Invalid parameter.";
        case NVJPEG_STATUS_BAD_JPEG:
            return "Bitstream is not a valid JPEG stream.";
        case NVJPEG_STATUS_JPEG_NOT_SUPPORTED:
            return "JPEG bitstream not supported.";
        case NVJPEG_STATUS_ALLOCATOR_FAILURE:
            return "Memory allocation failure.";
        case NVJPEG_STATUS_EXECUTION_FAILED:
            return "Execution failed.";
        case NVJPEG_STATUS_ARCH_MISMATCH:
            return "Architecture mismatch.";
        case NVJPEG_STATUS_INTERNAL_ERROR:
            return "Internal error.";
        default:
            return "Unknown error.";
    }
}

extern "C" {
    void initialize_nvjpeg() {
        std::cout << "Initializing NVJPEG" << std::endl;
        nvjpegCreateSimple(&nvjpeg_handle);
        nvjpegEncoderStateCreate(nvjpeg_handle, &nvjpeg_state, stream);
        nvjpegEncoderParamsCreate(nvjpeg_handle, &nvjpeg_params, stream);
        nvjpegEncoderParamsSetSamplingFactors(nvjpeg_params, NVJPEG_CSS_444, stream);
        std::cout << "NVJPEG initialized" << std::endl;
    }

    void encode_image(unsigned char* h_image, int width, int height, std::vector<unsigned char>& jpeg_output) {
        // Allocate device memory and copy image data
        for (int i = 0; i < 3; i++) {
            cudaError_t cuda_status = cudaMalloc((void**)&(nvjpeg_image.channel[i]), width * height);
            if (cuda_status != cudaSuccess) {
                std::cerr << "Error allocating CUDA memory: " << cudaGetErrorString(cuda_status) << std::endl;
                return;
            }

            cuda_status = cudaMemcpy(nvjpeg_image.channel[i], h_image + width * height * i, width * height, cudaMemcpyHostToDevice);
            if (cuda_status != cudaSuccess) {
                std::cerr << "Error copying image data to device: " << cudaGetErrorString(cuda_status) << std::endl;
                return;
            }

            nvjpeg_image.pitch[i] = width;
        }

        nvjpegStatus_t status = nvjpegEncodeImage(
            nvjpeg_handle,
            nvjpeg_state,
            nvjpeg_params,
            &nvjpeg_image,
            NVJPEG_INPUT_RGB,
            width,
            height,
            stream
        );

        if (status != NVJPEG_STATUS_SUCCESS) {
            std::cerr << "Error encoding image: " << get_nvjpeg_error_string(status) << std::endl;
            return;
        }

        size_t length;
        status = nvjpegEncodeRetrieveBitstream(
            nvjpeg_handle,
            nvjpeg_state,
            nullptr,
            &length,
            stream
        );

        if (status != NVJPEG_STATUS_SUCCESS) {
            std::cerr << "Error retrieving bitstream length: " << get_nvjpeg_error_string(status) << std::endl;
            return;
        }

        cudaStreamSynchronize(stream);
        jpeg_output.resize(length);
        status = nvjpegEncodeRetrieveBitstream(
            nvjpeg_handle,
            nvjpeg_state,
            jpeg_output.data(),
            &length,
            stream
        );

        if (status != NVJPEG_STATUS_SUCCESS) {
            std::cerr << "Error retrieving bitstream: " << get_nvjpeg_error_string(status) << std::endl;
            return;
        }

        cudaStreamSynchronize(stream);

        for(int i = 0; i < 3; i++){
            cudaFree(nvjpeg_image.channel[i]);
        }
    }


    void cleanup_nvjpeg() {
        nvjpegEncoderStateDestroy(nvjpeg_state);
        nvjpegEncoderParamsDestroy(nvjpeg_params);
        nvjpegDestroy(nvjpeg_handle);
    }
}