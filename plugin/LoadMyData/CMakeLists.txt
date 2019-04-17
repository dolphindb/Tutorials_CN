cmake_minimum_required(VERSION 3.0)

project(PluginLoadMyData)

add_definitions(-D_GLIBCXX_USE_CXX11_ABI=0)

LINK_DIRECTORIES("../libs")
INCLUDE_DIRECTORIES("../include")
if(WIN32)
    add_definitions(-DWINDOWS)
elseif(UNIX)
    add_definitions(-DLINUX)
endif()

add_compile_options( "-std=c++11" "-fPIC" "-Wall" "-Werror")

add_library(PluginLoadMyData SHARED
    "./src/LoadMyData.cpp"
)
target_link_libraries(PluginLoadMyData DolphinDB)