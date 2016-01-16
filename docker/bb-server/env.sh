set -e
test -n "$DEBUG_START_SH" && set -x

if [ -z "$CENV" ]; then
    umask 002

    export PGHOSTADDR=$POSTGRES_PORT_5432_TCP_ADDR
    export PGUSER=bagbunker
    export PGPASSWORD=bagbunker
    export MATPLOTLIBRC=$MARV_INSTANCE_PATH
    export MARV_PKGS_DIR="$MARV_ROOT/src"

    # Python's urllib does not like these variables, if they are empty
    test -z "$http_proxy" && unset http_proxy
    test -z "$https_proxy" && unset https_proxy

    # If /home is coming via volume, $HOME might not exist, yet.
    if [ ! -d "$HOME" ]; then
        sudo mkdir -p $HOME
        sudo chown $MARV_USER:$MARV_GROUP $HOME
        sudo chmod 775 $HOME
    fi

    # Invalidate state and venv if docker image is newer than venv
    if [ -f "$STATE_DIR/venv" ] && [ "$IMAGE_TIMESTAMP" -nt "$STATE_DIR/venv" ]; then
        echo "Invalidating outdated venv..."
        rm -f $STATE_DIR/*
        rm -fR $VENV/bin $VENV/lib
        echo "Done invalidating outdated venv."
    fi

    # Create virtual env if it is mounted as volume
    if [ ! -f "$STATE_DIR/venv" ]; then
        echo "Creating venv..."
        sudo mkdir -p $VENV $STATE_DIR
        sudo chown -R :$MARV_GROUP $VENV $STATE_DIR
        sudo chmod -R g+w $VENV $STATE_DIR
        virtualenv --system-site-packages -p python2.7 $VENV
        touch $STATE_DIR/venv
        echo "Done creating venv."
    fi

    # Activate virtualenv
    source $VENV/bin/activate

    if [ -n "$DEBUG_VENV" ]; then
        python -c 'import sys,pprint;pprint.pprint(sys.path)'
    fi

    # Load package environments
    cd $MARV_ROOT
    for envsh in $MARV_PKGS_DIR/*/env.sh; do
        source "$envsh"
    done

    if [ $(which bagbunker) ]; then
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
