cmake_minimum_required(VERSION 3.13.1)
project(app)

# OpenCV libraries
find_package(OpenCV REQUIRED)
include_directories(${CMAKE_SOURCE_DIR} ${OpenCV_INCLUDE_DIRS})

if (UNIX)
     include_directories(/usr/local/include)
     link_directories(/usr/local/lib)
endif (UNIX)

# Platform-specific settings
if (WIN32)
    # Define necessary macros for Windows
    add_definitions(-D_WIN32_WINNT=0x0601)
    # Set platform-specific libraries
    set(PLATFORM_LIBS ws2_32 ${OpenCV_LIBS})
else()
    # Set platform-specific libraries for Linux
    set(PLATFORM_LIBS pthread ${OpenCV_LIBS})
endif()

# Source files
set(SOURCE_FILES
    sources/main.cpp
    sources/mongoose.c
    # Add other source files here
)

# Add the executable
add_executable(app ${SOURCE_FILES})

# Link platform-specific libraries
target_link_libraries(app ${PLATFORM_LIBS})