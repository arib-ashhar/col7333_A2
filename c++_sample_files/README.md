#  C++ Sample Files

It contains following files. You are allowed to create the files of your own. But player file must be named at student_agent.py

- student_agent_cpp.py - Serves as a wrapper between python and c++.
- student_agent.cpp - Can be used to write your c++ code.
- CMakeLists.txt - CMake file

## Dependencies
pybind11

## Installation
```sh
pip install pybind11
```

## Setting up the C++ Agent
Run the following commands in the root folder
```sh
chmod +x compile.sh
./compile.sh
```
Run:

```sh
cd ..
```

## Running for a C++ program.

You need to use student_cpp rather than student for this case.
go to the /client_server and then run the following command

```sh
python gameEngine.py --mode aivai --circle random --square student_cpp
```

