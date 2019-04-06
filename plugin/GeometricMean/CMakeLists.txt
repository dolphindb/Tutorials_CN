cmake_minimum_required(VERSION 3.0)

project(PluginGeometricMean)

LINK_DIRECTORIES("../libs")
INCLUDE_DIRECTORIES("../include")
if(WIN32)
    add_definitions(-DWINDOWS)
elseif(UNIX)
    add_definitions(-DLINUX)
endif()

add_compile_options( "-std=c++11" "-fPIC" "-Wall" "-Werror")

add_library(PluginGeometricMean SHARED
    "./src/GeometricMean.cpp"
)
target_link_libraries(PluginGeometricMean DolphinDB)