cmake_minimum_required(VERSION 3.13.1)

project(app)
add_executable(app "sources/main.cpp")

if(NOT TARGET app)
     message(FATAL_ERROR "Please create a target named 'app' (ex: add_executable(app)) before adding this file")
endif()

# OpenCV libraries
find_package(OpenCV REQUIRED)
include_directories(${OpenCV_INCLUDE_DIRS})

target_include_directories(app PRIVATE .)
if (UNIX)
     include_directories(/usr/local/include)
     link_directories(/usr/local/lib)
endif (UNIX)

# add all sources to the project
target_link_libraries(app ${OpenCV_LIBS})
target_sources(app PRIVATE ${MODEL_SOURCE})