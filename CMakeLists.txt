cmake_minimum_required(VERSION 3.10)
project(your_project_core)

set(CMAKE_C_STANDARD 11)

# Platform-specific configurations
if(WIN32)
    add_definitions(-DWIN32 -D_WINDOWS)
    set(PLATFORM_LIBS advapi32 psapi)
else()
    set(PLATFORM_LIBS)
endif()

# Create shared library
add_library(native_monitor SHARED src/native/system_monitor.c)
target_link_libraries(native_monitor ${PLATFORM_LIBS})