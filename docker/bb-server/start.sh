#!/bin/bash
set -e
test -n "$DEBUG_START_SH" && set -x

check_retcode() {
    if [ "$RETCODE" != "0" ]; then
        if [ -z "$BB_DATA" ]; then
            # We are building an image, not running a container
            exit $RETCODE
        fi
        echo
        echo "ERROR $CMD returned with $RETCODE."
        echo
        echo "Leaving container running, abort with CTRL-C or investigate:"
        echo
        echo "  docker exec -ti $COMPOSE_PROJECT_NAME bash"
        echo
        exec python -m SimpleHTTPServer
    fi
}

if [ $(stat -c "%G" $MARV_INSTANCE_PATH) != "$MARV_GROUP" ]; then
    sudo chown :$MARV_GROUP $MARV_INSTANCE_PATH
    sudo chmod g+w $MARV_INSTANCE_PATH
fi

marv init --symlink-frontend $DOCKER_IMAGE_MARV_SKEL_SITE/frontend $MARV_INSTANCE_PATH

if [ -n "$POSTGRES_PORT_5432_TCP_ADDR" ]; then
    echo "Waiting for Postgres..."
    echo "Postgres appeared at $POSTGRES_PORT_5432_TCP_ADDR"
    while :; do
        psql -h $POSTGRES_PORT_5432_TCP_ADDR -w bagbunker -c '\d' &> /dev/null && break
        sleep 0.1
    done
    echo "Done waiting for Postgresql."
    export PGHOSTADDR=$POSTGRES_PORT_5432_TCP_ADDR
fi

if [ ! -d "$MARV_INSTANCE_PATH/log" ]; then
    mkdir $MARV_INSTANCE_PATH/log
    sudo chown :www-data $MARV_INSTANCE_PATH/log
    sudo chmod g+w $MARV_INSTANCE_PATH/log
fi

if [ ! -f $MARV_INSTANCE_PATH/users.txt ]; then
    touch $MARV_INSTANCE_PATH/users.txt
    sudo chown root:$MARV_GROUP $MARV_INSTANCE_PATH/users.txt
    sudo chmod 640 $MARV_INSTANCE_PATH/users.txt
fi

set +e
CMD='bagbunker admin checkdb --quiet'
$CMD
RETCODE=$?
set -e

if [ "$RETCODE" = "2" ]; then
    echo "Initializing database"
    set +e
    CMD="bagbunker admin initdb"
    $CMD
    RETCODE=$?
    set -e
elif [ "$RETCODE" = "9" ]; then
    echo
    echo "Database needs migration!"
    echo
    echo "1. Stop docker-compose and make backup of $BB_DATA"
    echo
    echo "2. Start docker-compose again and run shell:"
    echo
    echo "   % docker exec -ti $COMPOSE_PROJECT_NAME bash"
    echo
    echo "3. Run migration inside docker container"
    echo
    echo "   % alembic upgrade head"
    echo
    echo "4. Check database:"
    echo
    echo "   % bagbunker admin checkdb"
    echo
    echo "5. Restart docker-compose"
    echo
    exec python -m SimpleHTTPServer
else
    check_retcode
fi


if [ "$1" = "apache2" ]; then
    echo "Running apache2 on ${BB_LISTEN} in foreground, press Ctrl-C to end."
    exec sudo apache2 -D FOREGROUND
fi

exec "$@"
