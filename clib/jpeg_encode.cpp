/*
    JPEG conversion using CUDA nvJPEG

    This uses the cuda runtime and the nvJPEG cuda library to 
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
        case NVJPEG_STATUS_SUCCESS: return "The API call returned with no errors.";
        case NVJPEG_STATUS_NOT_INITIALIZED: return "The library was not initialized with nvjpegCreate().";
        case NVJPEG_STATUS_INVALID_PARAMETER: return "Invalid parameter.";
        case NVJPEG_STATUS_BAD_JPEG: return "Bitstream is not a valid JPEG stream.";
        case NVJPEG_STATUS_JPEG_NOT_SUPPORTED: return "JPEG bitstream not supported.";
        case NVJPEG_STATUS_ALLOCATOR_FAILURE: return "Memory allocation failure.";
        case NVJPEG_STATUS_EXECUTION_FAILED: return "Execution failed.";
        case NVJPEG_STATUS_ARCH_MISMATCH: return "Architecture mismatch.";
        case NVJPEG_STATUS_INTERNAL_ERROR: return "Internal error.";
        default: return "Unknown error.";
    }
}

extern "C" {
    void initialize_nvjpeg() {
        std::cout << "Initializing NVJPEG" << std::endl;
        nvjpegCreateSimple(&nvjpeg_handle);
        nvjpegEncoderStateCreate(nvjpeg_handle, &nvjpeg_state, stream);
        nvjpegEncoderParamsCreate(nvjpeg_handle, &nvjpeg_params, stream);
        nvjpegEncoderParamsSetSamplingFactors(nvjpeg_params, NVJPEG_CSS_444, stream);
        cudaStreamCreate(&stream);
        std::cout << "NVJPEG initialized" << std::endl;
    }

    void encode_image(unsigned char* h_image, int width, int height, unsigned char** jpeg_output, size_t* jpeg_length) {
        std::cout << "Encoding image" << std::endl;

        for (int i = 0; i < 3; i++) {
            cudaError_t cuda_status = cudaMalloc((void**)&(nvjpeg_image.channel[i]), width * height);
            if (cuda_status != cudaSuccess) {
                std::cerr << "Error allocating CUDA memory: " << cudaGetErrorString(cuda_status) << std::endl;
                return;
            }

            cuda_status = cudaMemcpy(nvjpeg_image.channel[i], h_image + width * height * i, width * height, cudaMemcpyHostToDevice);
            if (cuda_status != cudaSuccess) {
                std::cerr << "Error copying image data to device: " << cudaGetErrorString(cuda_status) << std::endl;
                for (int j = 0; j <= i; j++) {
                    cudaFree(nvjpeg_image.channel[j]);
                }
                return;
            }

            nvjpeg_image.pitch[i] = width;
        }

        cudaError_t cuda_status = cudaDeviceSynchronize();
        if (cuda_status != cudaSuccess) {
            std::cerr << "Error synchronizing device: " << cudaGetErrorString(cuda_status) << std::endl;
            for (int i = 0; i < 3; i++) {
                cudaFree(nvjpeg_image.channel[i]);
            }
            return;
        }

        std::cout << "Image data copied to device" << std::endl;

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
            for (int i = 0; i < 3; i++) {
                cudaFree(nvjpeg_image.channel[i]);
            }
            return;
        }

        status = nvjpegEncodeRetrieveBitstream(
            nvjpeg_handle,
            nvjpeg_state,
            nullptr,
            jpeg_length,
            stream
        );

        if (status != NVJPEG_STATUS_SUCCESS) {
            std::cerr << "Error retrieving bitstream length: " << get_nvjpeg_error_string(status) << std::endl;
            for (int i = 0; i < 3; i++) {
                cudaFree(nvjpeg_image.channel[i]);
            }
            return;
        }

        cuda_status = cudaStreamSynchronize(stream);
        if (cuda_status != cudaSuccess) {
            std::cerr << "Error synchronizing stream: " << cudaGetErrorString(cuda_status) << std::endl;
            for (int i = 0; i < 3; i++) {
                cudaFree(nvjpeg_image.channel[i]);
            }
            return;
        }

        *jpeg_output = (unsigned char*)malloc(*jpeg_length);
        if (*jpeg_output == nullptr) {
            std::cerr << "Error allocating host memory for JPEG output." << std::endl;
            for (int i = 0; i < 3; i++) {
                cudaFree(nvjpeg_image.channel[i]);
            }
            return;
        }

        status = nvjpegEncodeRetrieveBitstream(
            nvjpeg_handle,
            nvjpeg_state,
            *jpeg_output,
            jpeg_length,
            stream
        );

        if (status != NVJPEG_STATUS_SUCCESS) {
            std::cerr << "Error retrieving bitstream: " << get_nvjpeg_error_string(status) << std::endl;
            free(*jpeg_output);
            for (int i = 0; i < 3; i++) {
                cudaFree(nvjpeg_image.channel[i]);
            }
            return;
        }

        cuda_status = cudaStreamSynchronize(stream);
        if (cuda_status != cudaSuccess) {
            std::cerr << "Error synchronizing stream: " << cudaGetErrorString(cuda_status) << std::endl;
            free(*jpeg_output);
            for (int i = 0; i < 3; i++) {
                cudaFree(nvjpeg_image.channel[i]);
            }
            return;
        }

        for (int i = 0; i < 3; i++) {
            cudaFree(nvjpeg_image.channel[i]);
        }

        std::cout << "Image encoded successfully" << std::endl;
    }

    void cleanup_nvjpeg() {
        nvjpegEncoderStateDestroy(nvjpeg_state);
        nvjpegEncoderParamsDestroy(nvjpeg_params);
        nvjpegDestroy(nvjpeg_handle);
        cudaStreamDestroy(stream);
    }
}
