cmake_minimum_required(VERSION 3.8)
project(tb4_simulation_lab)

find_package(ament_cmake REQUIRED)

install(DIRECTORY config launch maps
  DESTINATION share/${PROJECT_NAME}
  PATTERN "__pycache__" EXCLUDE
  PATTERN "*.pyc" EXCLUDE
)

install(PROGRAMS
  scripts/check_topics.sh
  scripts/navigation_node.py
  scripts/yolo_detection_node.py
  scripts/send_nav_goals.py
  DESTINATION lib/${PROJECT_NAME}
)

ament_package()
