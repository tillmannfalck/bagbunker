set -e
test -n "$DEBUG_START_SH" && set -x

if [ -e /opt/ros/indigo/setup.bash ]; then
    source /opt/ros/indigo/setup.bash
fi
