#!/bin/bash
set -e
test -n "$DEBUG_START_SH" && set -x

# An alternative would be -e and a repo url in requirements.txt
# This here is more efficient and can be cached
pip install --upgrade https://github.com/ternaris/flask-restless/archive/0.17.0-45-fix.tar.gz

FRONTEND="$(readlink -f "$(dirname "$0")")"/frontend
cd $FRONTEND

# temporary hack, will be handled by bungle-ember
sudo touch app/pods/index/template.hbs.new
sudo chown :$MARV_GROUP app/pods/index/template.hbs.new
sudo chmod g+w app/pods/index/template.hbs.new
./gen-index-template-hbs.py ../../*/frontend > app/pods/index/template.hbs.new
if [ ! -e app/pods/index/template.hbs ]; then
    sudo cp app/pods/index/template.hbs.new app/pods/index/template.hbs
    sudo chown :$MARV_GROUP app/pods/index/template.hbs
    sudo chmod g+x app/pods/index/template.hbs
    rm -f dist/.built
fi
if ! diff -q app/pods/index/template{.hbs.new,.hbs}; then
    sudo cp app/pods/index/template{.hbs.new,.hbs}
    rm -f dist/.built
fi
sudo rm -f app/pods/index/template.hbs.new

# temporary hack, will be handled by bungle-ember
sudo touch be.json.new
sudo chown :$MARV_GROUP be.json.new
sudo chmod g+w be.json.new
./gen-be-json.py ../../*/frontend > be.json.new
if [ ! -e be.json ]; then
    sudo cp be.json.new be.json
    sudo chown :$MARV_GROUP be.json
    sudo chmod g+w be.json
    rm -f dist/.built
fi
if ! diff -q be.json.new be.json; then
    sudo cp be.json.new be.json
    rm -f dist/.built
fi
sudo rm -f be.json.new

if [ ! -e dist/.built ]; then
    sudo mkdir -p bower_components dist
    sudo chown -R :$MARV_USER bower_components dist
    sudo chmod -R g+w bower_components dist
    bungle-ember build
    touch dist/.built
fi
