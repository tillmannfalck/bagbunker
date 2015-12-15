#!/bin/bash
set -e
test -n "$DEBUG_START_SH" && set -x

FRONTEND="$(readlink -f "$(dirname "$0")")"/frontend

# An alternative would be -e and a repo url in requirements.txt
# This here is more efficient and can be cached
pip install --upgrade https://github.com/ternaris/flask-restless/archive/0.17.0-45-fix.tar.gz

NODE_VERSION=5.2.0
cd $HOME
test -d node-v${NODE_VERSION}-linux-x64 || \
    curl https://nodejs.org/dist/v5.2.0/node-v5.2.0-linux-x64.tar.gz |tar xz

cd $HOME/bin
test -e node || ln -s ../node-v*/bin/node
test -e npm || ln -s ../node-v*/bin/npm
echo node-$(./node -v)
echo npm-$(./npm -v)

# XXX: switch to https
cd $HOME
test -d bngl || curl http://ternaris.com/bngl.tar.gz |tar xz
cd $HOME/bngl/bungle-ember
if [ ! -d .built ]; then
    echo $PATH
    npm install
    touch .built
fi

cd $HOME/bin
test -e bungle-ember || ln -s $HOME/bngl/bungle-ember/bin/bungle-ember

cd $FRONTEND
if [ ! -e dist/.built ]; then
    sudo mkdir -p dist
    sudo chown -R :$MARV_USER dist
    sudo chmod -R g+w dist
    bungle-ember build
    touch dist/.built
fi
