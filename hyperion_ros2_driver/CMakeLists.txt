cmake_minimum_required(VERSION 3.8)
project(hyperion_ros2_driver)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(std_msgs REQUIRED)
find_package(rosidl_default_generators REQUIRED)
find_package(Threads REQUIRED)

set(HYPERION_SDK_DIR
  "${CMAKE_CURRENT_SOURCE_DIR}/../../../scripts/interrogator_si255/si255_Hyperion_CPP_hLibrary-0.9.5.1"
)

rosidl_generate_interfaces(${PROJECT_NAME}
  "msg/HyperionPeaks.msg"
  DEPENDENCIES std_msgs
)

add_library(hyperion_sdk STATIC
  "${HYPERION_SDK_DIR}/hCommLibrary.cpp"
  "${HYPERION_SDK_DIR}/hLibrary.cpp"
)
target_compile_features(hyperion_sdk PUBLIC cxx_std_17)
target_include_directories(hyperion_sdk PUBLIC "${HYPERION_SDK_DIR}")

add_executable(hyperion_driver_node src/hyperion_driver_node.cpp)
target_compile_features(hyperion_driver_node PUBLIC cxx_std_17)
target_include_directories(hyperion_driver_node PRIVATE "${HYPERION_SDK_DIR}")
ament_target_dependencies(hyperion_driver_node rclcpp std_msgs)
target_link_libraries(hyperion_driver_node hyperion_sdk Threads::Threads)

rosidl_get_typesupport_target(cpp_typesupport_target
  ${PROJECT_NAME}
  "rosidl_typesupport_cpp"
)
target_link_libraries(hyperion_driver_node "${cpp_typesupport_target}")

install(TARGETS
  hyperion_driver_node
  DESTINATION lib/${PROJECT_NAME}
)

install(DIRECTORY
  launch
  config
  DESTINATION share/${PROJECT_NAME}
)

ament_export_dependencies(rosidl_default_runtime)
ament_package()
