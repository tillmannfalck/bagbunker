set -e
test -n "$DEBUG_START_SH" && set -x

if [ -z "$CENV" ]; then
    umask 002

    export PGHOSTADDR=$POSTGRES_PORT_5432_TCP_ADDR
    export PGUSER=bagbunker
    export PGPASSWORD=bagbunker
    export MATPLOTLIBRC=$MARV_INSTANCE_PATH

    # Python's urllib does not like these variables, if they are empty
    test -z "$http_proxy" && unset http_proxy
    test -z "$https_proxy" && unset https_proxy

    # Bagbunker specific
    if [ -e /opt/ros/indigo/setup.bash ]; then
        source /opt/ros/indigo/setup.bash
    fi

    # Activate virtualenv
    source $VENV/bin/activate

    if [ -n "$DEBUG_VENV" ]; then
        python -c 'import sys,pprint;pprint.pprint(sys.path)'
    fi

    if [ -n "$BB_DATA" ] && [ $(which bagbunker) ]; then
        set +e
        bagbunker admin checkdb --quiet
        RETCODE=$?
        set -e
        if [ "$RETCODE" = "9" ]; then
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
        elif [ "$RETCODE" == "2" ]; then
            echo "Database does not exist, yet."
        elif [ "$RETCODE" != "0" ]; then
            echo "ERROR occured: $RETCODE"
        fi
    fi

    cd $MARV_ROOT

    export CENV=1
fi
set +e
