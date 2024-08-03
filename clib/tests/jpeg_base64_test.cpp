#include <iostream>
#include <opencv2/opencv.hpp>
#include "../cpp-base64/base64.h"

extern "C" {
    void initialize_nvjpeg();
    void encode_image(unsigned char* d_image, int width, int height, char** base64_output);
    void cleanup_nvjpeg();
}

int main() {
    initialize_nvjpeg();

    // Example image data
    int width = 1920;
    int height = 1080;
    unsigned char* d_image = new unsigned char[width * height * 3];  // Simulate an image buffer

    // Fill the image buffer with sample data (e.g., a gradient)
    for (int y = 0; y < height; ++y) {
        for (int x = 0; x < width; ++x) {
            int index = (y * width + x) * 3;
            d_image[index] = static_cast<unsigned char>(x % 256);        // Red
            d_image[index + 1] = static_cast<unsigned char>(y % 256);    // Green
            d_image[index + 2] = static_cast<unsigned char>((x + y) % 256); // Blue
        }
    }

    char* base64_output = nullptr;
    encode_image(d_image, width, height, &base64_output);

    if (base64_output) {
        std::cout << "Base64 Output: " << base64_output << std::endl;
        free(base64_output);
    }

    delete[] d_image;
    cleanup_nvjpeg();

    return 0;
}

