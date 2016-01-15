#!/bin/bash
set -e
test -n "$DEBUG_START_SH" && set -x

# For further variables see env.sh and Dockerfile
COMBINED_REQTXT="$STATE_DIR/requirements.txt"

# Install pip-tools
if [ ! -f "$STATE_DIR/pip-tools" ]; then
    pip install --upgrade 'pip-tools>=1.4.2'
    touch $STATE_DIR/pip-tools
fi

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

init_pkg() {
    pkg="$1"
    name=$(basename "$pkg")
    CMD="$pkg/init.sh"
    if [ ! -f "$CMD" ]; then
        echo "Nothing to initialize for $name in $pkg"
        return 0
    fi
    statefile="$STATE_DIR/${name}-initialized"
    if [ ! -f "$statefile" ] || [ "$CMD" -nt "$statefile" ]; then
        rm -f $STATE_DIR/${name}-installed
        echo "Initializing $name in $pkg..."
        set +e
        "$CMD"
        RETCODE=$?
        set -e
        check_retcode
        CMD="$(dirname "$CMD")"/env.sh
        if [ -e "$CMD" ]; then
            set +e
            source "$CMD"
            RETCODE=$?
            set -e
            check_retcode
        fi
        touch "$statefile"
        echo "Done initializing $name in $pkg."
    else
        echo "Init up-to-date for $name in $pkg"
    fi
}

install_pkg() {
    pkg="$1"
    name=$(basename "$pkg")
    setuppy="$pkg/setup.py"
    if [ ! -f "$setuppy" ]; then
        echo "No python package for $name in $pkg"
        return 0
    fi
    statefile="$STATE_DIR/${name}-installed"
    if [ ! -f "$statefile" ] || [ "$setuppy" -nt "$statefile" ]; then
        echo "Installing $name in $pkg..."
        egginfo="$pkg/${name}.egg-info"
        sudo mkdir -p "$egginfo"
        sudo chown -R :$MARV_GROUP "$egginfo"
        sudo chmod -R g+w "$egginfo"
        set -e
        CMD="pip install --no-index -e $pkg"
        $CMD
        RETCODE=$?
        set +e
        check_retcode
        touch "$statefile"
        echo "Done installing $name in $pkg..."
    else
        echo "Install up-to-date for $name in $pkg"
    fi
}

if [ -n "$BEFORE_INIT" ]; then
    if [ "$1" = "apache2" ]; then
        exec bash
    else
        exec "$@"
    fi
fi

if [ $(stat -c "%G" $MARV_INSTANCE_PATH) != "$MARV_GROUP" ]; then
    sudo chown :$MARV_GROUP $MARV_INSTANCE_PATH
    sudo chmod g+w $MARV_INSTANCE_PATH
fi

# Initialize packages to install system dependencies among others
for pkg in $MARV_PKGS_DIR/*; do
    init_pkg "$pkg"
done

if [ -n "$BEFORE_REQ_INSTALL" ]; then
    if [ "$1" = "apache2" ]; then
        exec bash
    else
        exec "$@"
    fi
fi

# concatenate all requirements.txt and synchronize virtualenv
NEEDS_SYNC=
for reqtxt in $MARV_PKGS_DIR/*/requirements.txt; do
    if [ "$reqtxt" -nt $COMBINED_REQTXT ]; then
        NEEDS_SYNC=1
        echo "Sync needed for $reqtxt"
    fi
done
if [ -n "$NEEDS_SYNC" ]; then
    cat $MARV_PKGS_DIR/*/requirements.txt |grep -v '^#' |cut -d' ' -f1 |sort -u > $COMBINED_REQTXT

    echo "Syncing venv..."
    pip-sync $COMBINED_REQTXT
    # XXX: pip-sync currently uninstalls them
    for pkg in "$MARV_PKGS_DIR"/*; do
        rm -f $STATE_DIR/"$(basename "$pkg")"-installed
    done
    echo "Done syncing venv."
fi

# Install python packages in development
install_pkg "$MARV_PKGS_DIR/marv"
for pkg in "$MARV_PKGS_DIR"/*; do
    if [ "$(basename "$pkg")" != "marv" ]; then
        install_pkg "$pkg"
    fi
done

if [ -n "$AFTER_INSTALL" ]; then
    if [ "$1" = "apache2" ]; then
        exec bash
    else
        exec "$@"
    fi
fi


# Initialize marv instance path and build frontend
marv init $MARV_INSTANCE_PATH
cd $MARV_INSTANCE_PATH/frontend
if [ ! -e dist/.built ]; then
    bungle-ember build
    touch dist/.built
fi
cd $MARV_ROOT


if [ -z "$BB_DATA" ]; then
    echo "start.sh called during image build - done"
    exit 0
fi


if [ -n "$POSTGRES_PORT_5432_TCP_ADDR" ]; then
    echo "Waiting for Postgres..."
    echo "Postgres appeared at $POSTGRES_PORT_5432_TCP_ADDR"
    while :; do
        psql -h $POSTGRES_PORT_5432_TCP_ADDR -w bagbunker -c '\d' &> /dev/null && break
        sleep 0.1
    done
    echo "Done waiting for Postgresql."
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


# Previously wrong permissions
sudo chown root:$MARV_GROUP $MARV_INSTANCE_PATH/users.txt
sudo chmod 640 $MARV_INSTANCE_PATH/users.txt


# Permission fixes for 65533 migration
sudo mkdir -p $MARV_INSTANCE_PATH/{jobruns,storage}
sudo chown -R $MARV_USER:$MARV_GROUP $MARV_INSTANCE_PATH/{jobruns,storage}


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
