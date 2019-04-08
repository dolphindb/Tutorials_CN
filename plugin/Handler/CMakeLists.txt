cmake_minimum_required(VERSION 3.0)

project(PluginHandler)

add_definitions(-D_GLIBCXX_USE_CXX11_ABI=0)

LINK_DIRECTORIES("../libs")
INCLUDE_DIRECTORIES("../include")
if(WIN32)
    add_definitions(-DWINDOWS)
elseif(UNIX)
    add_definitions(-DLINUX)
endif()

add_compile_options( "-std=c++11" "-fPIC" "-Wall" "-Werror")

add_library(PluginHandler SHARED
    "./src/Handler.cpp"
)
target_link_libraries(PluginHandler DolphinDB)