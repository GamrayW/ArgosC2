cmake_minimum_required(VERSION 3.26)
project(agent C)

set(CMAKE_C_STANDARD 11)

add_executable(agent main.c)
target_link_libraries(agent wsock32 ws2_32)

