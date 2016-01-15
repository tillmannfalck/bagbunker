#!/bin/bash
set -e
test -n "$DEBUG_START_SH" && set -x

### Included in Dockerfile for the time being
# sudo bash -c 'echo "deb http://packages.ros.org/ros/ubuntu $(lsb_release -sc) main" \
#      > /etc/apt/sources.list.d/ros-latest.list'
# sudo apt-key adv --keyserver hkp://pool.sks-keyservers.net --recv-key 0xB01FA116
# sudo apt-get update
# sudo apt-get install -y \
#      ros-indigo-rosbag \
#      ros-indigo-rostest \
#      ros-indigo-common-msgs \
#      ros-indigo-cv-bridge
#
# sudo rm -f /etc/ros/rosdep/sources.list.d/20-default.list
# sudo rosdep init
# rosdep update

exit 0
