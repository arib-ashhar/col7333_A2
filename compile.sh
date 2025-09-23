#!/bin/bash
set -e  # exit immediately on error

# Go into the C++ folder
cd c++_sample_files

# Clean and rebuild
rm -rf build
mkdir build && cd build

# Configure with CMake (ensure pybind11 is installed)
cmake .. -Dpybind11_DIR=$(python3 -m pybind11 --cmakedir) \
    -DCMAKE_C_COMPILER=gcc \
    -DCMAKE_CXX_COMPILER=g++

# Build
make

# Back to repo root
cd ../..

# Copy wrapper and build artifacts into client_server/
cp c++_sample_files/student_agent_cpp.py client_server/
cp -r c++_sample_files/build client_server/