CXX = g++
CXXFLAGS = -fPIC -std=c++11 -I/usr/local/cuda/include `pkg-config --cflags opencv4`
LDFLAGS = -L/usr/local/cuda/lib64 -lnvjpeg -lcudart `pkg-config --libs opencv4`

all: libnvjpeg_encoder.so tests/test_nvjpeg.out

libnvjpeg_encoder.so: jpeg_base64.o base64.o
	$(CXX) -shared -o $@ $^ $(LDFLAGS)

jpeg_base64.o: jpeg_base64.cpp
	$(CXX) $(CXXFLAGS) -c $<

base64.o: cpp-base64/base64.cpp
	$(CXX) $(CXXFLAGS) -c $<

tests/test_nvjpeg.out: tests/jpeg_base64_test.o libnvjpeg_encoder.so
	$(CXX) -o $@ $^ -L. -lnvjpeg_encoder $(LDFLAGS)

tests/jpeg_base64_test.o: tests/jpeg_base64_test.cpp
	$(CXX) $(CXXFLAGS) -c $< -o $@

clean:
	rm -f *.o *.so tests/test_nvjpeg.out

