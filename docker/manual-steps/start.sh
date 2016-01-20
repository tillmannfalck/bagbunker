#!/bin/bash

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

exec "$@"
