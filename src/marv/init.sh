#!/bin/bash
set -e
test -n "$DEBUG_START_SH" && set -x

# An alternative would be -e and a repo url in requirements.txt
# This here is more efficient and can be cached
pip install --upgrade https://github.com/ternaris/flask-restless/archive/0.17.0-45-fix.tar.gz

exit 0
