cmake_minimum_required(VERSION 3.8)
project(my_robot_nav)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)

install(PROGRAMS scripts/qos_relay.py scripts/lifecycle_activator.py DESTINATION lib/${PROJECT_NAME})

install(
  DIRECTORY config launch maps
  DESTINATION share/${PROJECT_NAME}
  FILES_MATCHING PATTERN "*"
)

ament_package()
