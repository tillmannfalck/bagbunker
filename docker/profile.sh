# Adjust to the correct absolute path
#export COMPOSE_FILE=$HOME/bagbunker/docker/compose/development.yml
export COMPOSE_FILE=$HOME/bagbunker/docker/compose/production.yml

# This name needs to be unique among all docker-compose managed
# projects on your server. It will also be used as base for the
# container names.
#export COMPOSE_PROJECT_NAME=bb_dev    # development
export COMPOSE_PROJECT_NAME=bb_production

# By default the master branch is used, uncomment to test an upcoming release
# This only affects production.yml
#export BRANCH=release

# Listen address for apache
#export BB_LISTEN=127.0.0.1:8000       # development
export BB_LISTEN=80

# Additionally, it is possible to run a development webserver (see
# README). With development.yml, this variable is currently needed,
# independent of whether such a server will be started.
#export BB_DEV_LISTEN=127.0.0.1:5000   # development

# Absolute path to your bag files
#export BB_BAGS=$HOME/bagbunker/example-bags
export BB_BAGS=/mnt/bags

# Absolute path to your bagbunker data directory
#export BB_DATA=$HOME/bagbunker/data   # development
#export BB_DATA=$HOME/bagbunker_data
export BB_DATA=/var/lib/bagbunker
