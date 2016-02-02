Manual Setup
============

Requirements
------------

- PostgreSQL >=9.3.10 (lower might work, but untested)
- Nodejs 5.2.0
- Latest Python 2.7
- Python virtualenv >= 13.1.2 (lower might work, but untested)
- ROS: rosbag, rostest, common-msgs, cv-bridge
- optional: Apache or Nginx (as reverse proxy for offloading file serving via xsendfile)


Install frontend tooling
------------------------

::

   % cd
   % curl https://ternaris.com/bngl.tar.gz |tar xz
   % cd bngl/bungle-ember && npm install

Add ``$HOME/bngl/bungle-ember/bin`` to your ``$PATH`` or link ``$HOME/bngl/bungle-ember/bin/bungle-ember`` into a directory that is already in ``$PATH``.


Create virtualenv and install python packages
---------------------------------------------

::

   % export PIP_FIND_LINKS=https://ternaris.com/pypi        # fixed packages
   % git clone git@github.com:bosch-ros-pkg/bagbunker.git
   % cd bagbunker
   % virtualenv -p python2.7 .
   % source bin/activate
   % pip install pip-tools==1.4.4
   % pip-sync src/*/requirements.txt
   % pip install src/marv src/bagbunker src/deepfield_jobs

For ``pip-sync`` currently the virtualenv needs to be activated, it can't be called as ``./bin/pip-sync`` (see https://github.com/nvie/pip-tools/issues/296).


Set environment variables
-------------------------

``PHHOSTADDR=127.0.0.1:5432``
   Host address (with optional port) where postgresql is running
``PGUSER=bagbunker``
   Database user
``PGPASSWORD=secret``
   Database password
``MARV_INSTANCE_PATH=/path/to/your/site``
   Path to the site directory created in the next step
``MATPLOTLIBRC=$MARV_INSTANCE_PATH``
   Make matplotlibrc available from your site
``MARV_VENV=$HOME/bagbunker``
   Path to the virtual python environment, bagbunker is installed in. It is symlinked into the site directory
``MARV_SIGNAL_URL=http://127.0.0.1:80``
   URL to your instance used by the cli to signal the need for updating the listing cache


Create Marv site and build frontend
-----------------------------------

::

   % marv init /path/to/your/site
   % cd /path/to/your/site/frontend
   % bungle-ember build

See also ``marv --help``.

In the site directory a bb.wsgi file is created and used by the example apache config (see below).


Initialize database
-------------------

::

   % bagbunker admin --help
   % bagbunker admin initdb


Start bagbunker's development webserver
---------------------------------------

::

   % bagbunker webserver --help
   % bagbunker webserver

The internal webserver listens on port 5000.


Apache config
-------------

An example apache config is found here: `000-default.conf <../docker/bb-server/000-default.conf>`_.
