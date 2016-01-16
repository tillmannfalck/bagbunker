Manual Setup
============

Requirements
------------

- PostgreSQL >=9.3.10 (lower might work, but untested)
- Nodejs 5.2.0
- Latest Python 2.7
- Python virtualenv >= 13.1.2 (lower might work, but untested)


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

   % export PIP_FIND_LINKS=https://ternaris.com/pypi
   % cd bagbunker
   % virtualenv -p python2.7 .
   % source bin/activate
   % pip install -U 'pip-tools>=1.4.2'
   % pip-sync src/*/requirements.txt
   % pip install -e src/marv
   % pip install -e src/bagbunker
   % pip install -e src/deepfield_jobs

Make sure ``pip-sync`` is not installed system-wide. There are open bugs, regarding that. Also for ``pip-sync`` currently the virtualenv needs to be activated, it can't be called as ``./bin/pip-sync`` (see https://github.com/nvie/pip-tools/issues/296).


Create Marv site and build frontend
-----------------------------------

::

   % marv init /path/to/your/site
   % cd /path/to/your/site/frontend
   % bungle-ember build


Initialize database
-------------------

::

   % cd /path/to/your/site
   % bagbunker admin initdb


Start bagbunker's development webserver
---------------------------------------

::

   % cd /path/to/your/site
   % bagbunker webserver

The internal webserver listens on port 5000


Apache config
-------------

See the apache configuration used within the docker setup `000-default.conf <../docker/bb-server/000-default.conf>`_.


Environment variables
---------------------

TODO
