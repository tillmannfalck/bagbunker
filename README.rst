Getting started
===============

Using a proxy
-------------

All tools should honor the ``http_proxy`` and ``https_proxy`` environment variables. If this does not work, please open a `new issue <https://github.com/bosch-ros-pkg/bagbunker/issues/new>`_. Make sure the proxy variables point to an IP address that is reachable from within the docker container, ``127.0.0.1` inside your docker container is a different ``127.0.0.1`` than outside. The IP address of the ``docker0`` interface works.


System requirements
-------------------

Bagbunker needs rosbag and uses a postgresql database. So far we support docker and docker-compose to take care of dependencies, and systemd for service management in server setups. If you cannot use these tools, please open a `new issue <https://github.com/bosch-ros-pkg/bagbunker/issues/new>`_ describing your desired deployment.

Install docker either via system package management or as outlined in the `official instructions <https://docs.docker.com/installation/>`_. Make sure you have at least docker version 1.8.1::

  % docker --version
  Docker version 1.8.1, build d12ea79

Add your user to the docker group as described in `Create a Docker group <https://docs.docker.com/installation/ubuntulinux/#create-a-docker-group>`_. Otherwise you will have to use ``sudo docker`` instead of just ``docker``. Relogin or use ``newgrp docker`` to start a new shell. Make sure ``docker`` is listed when running ``groups``.

Install docker-compose >=1.5.2 for example via python pip, on a debian-based system::

  % sudo apt-get install python-pip
  % sudo pip install 'docker-compose>=1.5.2'
  % docker-compose --version
  docker-compose version: 1.5.2


Fetching the sources
--------------------

With ssh access::

  % git clone git@github.com:bosch-ros-pkg/bagbunker.git

or without ssh access::

  % git clone https://github.com/bosch-ros-pkg/bagbunker.git


Branches
--------

master
  is our production-ready branch, which you should also use for development of new jobs

develop
  reflects development targeted for the next release

release*
  release branches to prepare releases

hotfix*
  hotfix branches to prepare hotfixes

All other branches are feature branches and are likely to be rebased. For your changes, create a feature branch based on ``master`` or if needed ``develop``.

Branching model based on http://nvie.com/posts/a-successful-git-branching-model/.

The docker image contains the latest master branch of the bagbunker repository, suitable for production. For development setups, the bagbunker repository is mounted as a volume which gives you full control over which branch is used and enables you to develop new jobs (more on this further down).


Setup
=====

docker-compose is used to start and link two containers, one for a postgres database and one for bagbunker itself. There are two configurations, one for `development <docker/compose/development.yml>`_ and for `production <docker/compose/production.yml>`_.

The configurations use environment variables (see below).


Create and source profile
-------------------------

While it is possible to pass all configuration variables on the command-line, it is recommended to create a profile that is sourced, here by example of profile named for your production setup::

  % cp docker/profile.sh bb_production-profile.sh

Adjust the variables to your needs and then source the profile::

  % source bb_production-profile.sh


Create and run containers
-------------------------

Fetch all needed images and create and run containers::

  % docker-compose up

After this has finished without errors, bagbunker should be running on the ``$BB_LISTEN`` address you specified in the profile.

While ``docker-compose up`` is running, commands can be executed within the docker container using ``docker exec`` in a different terminal::

  % docker exec -it $COMPOSE_PROJECT_NAME bash -c 'bagbunker --help'

To start a shell within a docker container use::

  % docker exec -it $COMPOSE_PROJECT_NAME bash


Run tests
---------

Make sure to run tests after the containers have been created::

  % docker exec -ti $COMPOSE_PROJECT_NAME bash -c 'nosetests'


Add users
---------

Create some bagbunker users for web login/access::

  % docker exec -it $COMPOSE_PROJECT_NAME bash -c "sudo htpasswd -B /var/lib/bagbunker/users.txt john"


Add startup config (production-only)
------------------------------------

Abort docker-compose, copy systemd service description, and start again via systemd::

  CTRL-C
  % sudo cp docker/bb-server/bagbunker@bb_production.service /etc/systemd/system/
  % sudo cp docker/bb-server/bagbunker-database@bb_production.service /etc/systemd/system/
  % sudo systemctl start bagbunker-database@bb_production bagbunker@bb_production

Enable to start on boot::

  % sudo systemctl enable bagbunker-database@bb_production bagbunker@bb_production

The systemd service description files assume docker is installed in ``/usr/bin``, depending on how you installed docker you might need to adjust the path::

  % which docker
  /usr/bin/docker

Starting services::

  % sudo systemctl start bagbunker@bb_production bagbunker-database@bb_production

Stoping services::

  % sudo systemctl stop bagbunker@bb_production bagbunker-database@bb_production


Scan bags
---------

The ``$BB_BAGS`` volume is mounted at /mnt/bags::

  % docker exec -it $COMPOSE_PROJECT_NAME bash -c "bagbunker scan /mnt/bags"

Read metadata from bags (especially over NFS this may take a while)::

  % docker exec -it $COMPOSE_PROJECT_NAME bash -c "bagbunker read-pending"

And run jobs (this will take a while)::

  % docker exec -it $COMPOSE_PROJECT_NAME bash -c "bagbunker run-jobs --all"

Between and during each of these steps you can visit bagbunker with your browser at the ``$BB_LISTEN`` address to check the progress.


Add cronjob for periodic scanning (production-only)
---------------------------------------------------

Edit crontab::

  % crontab -e

and paste into crontab and adjust to your needs::

  # read new files once a day (during off hours due to high network traffic)
  0 20 * * * flock -n /tmp/bb_production-scan docker exec bb_production bash -c "bagbunker scan --read-pending --run-all-jobs /mnt/bags"


Backups
=======

All data that is extracted from bag files, generated by jobruns, and comments and tags created by users via web, is stored stored in the directory you configured as ``$BB_DATA``. In order to make a backup, stop backup services::

  % sudo systemctl stop bagbunker@bb_production bagbunker-database@bb_production

And double check that they are not listed as running services anymore with ``docker ps``.

After that you can make a copy of your ``$BB_DATA`` directory and start bagbunker again.


Upgrades
========

Before any upgrade make sure you have an up-to-date backup of your ``$BB_DATA`` directory and bagbunker is not running (see above).

Source the profile you want to manage::

  % source production-profile.sh

Pull new images, delete old containers and create and run new containers::

  % docker-compose pull
  % docker-compose rm
  % docker-compose up

After an upgrade a database migration might be needed. Check the database in a different terminal::

  % docker exec -ti $COMPOSE_PROJECT_NAME bash -c "bagbunker admin checkdb"

In case migration is needed you are greeted by instructions to perform the upgrade.

Stop again and start via systemd::

  CTRL-C
  % sudo systemctl start bagbunker-database@bb_production bagbunker@bb_production


Development
===========

In addition to everything explained above, there are a couple of things relevant for development.

As mentioned earlier the development setup uses your local clone of the bagbunker repository (in contrast to the one contained in the pre-built docker image).

As a reminder, source the profile before running docker commands::

  % source bb_dev-profile.sh


Switching between branches and after upgrades
---------------------------------------------

Python creates bytecode versions of all modules. In case you or we removed a module or a module exists in one but not the other branch, this confuses python. Make sure to delete these files after upgrade and branch switches::

  % find $(ls |grep -v $BB_DATA) -name '*.pyc' -delete


Bagbunker group
---------------

All files created by bagbunker from within the docker container will be uid/gid 65533/65533. For less need of ``sudo``, you might want to create a corresponding group and add your user to it::

  % sudo groupadd -g 65533 bb
  % sudo gpasswd -a <UID> bb

After that enter a new shell with ``newgrp bb`` or relogin.


Development webserver
---------------------

If you are developing on view code, you might want the development webserver which automatically reloads changed files. Run in separate terminal::

  % docker exec -ti bb_dev bash -c "bagbunker webserver --public"

It is served at ``$BB_DEV_LISTEN``, by default ``127.0.0.1:5000``.


Deleting database
-----------------

In order to delete the database just remove the data directory::

  % docker exec -ti bb_dev bash -c 'sudo rm -fr /opt/bagbunker/data'

abort ``docker-compose`` with CTRL-C and start it again::

  % docker-compose up
  ...
  CTRL-C
  % docker-compose up


Job development
===============

Jobs have a `__version__` which needs to be increased in order to run a job again for the same filesets. Especially for development you can force bagbunker to run a job, e.g.::

  % ./bin/bagbunker run-jobs --force deepfield::metadata

In order to develop your own jobs, please use the ``src/deepfield_jobs`` package as an example or add your jobs in there. Make sure to import your job from the package's ``__init__.py``. 


Coverage report
===============

To get a coverage report::

  % docker exec -it bb_dev bash -c 'nosetests --with-coverage'

In development setups, the coverage report is created in ``./cover/index.htm``l and a summary is displayed in the terminal. In order to access the coverage report in a production environment, you have to copy it out of the docker container::

  % docker cp $COMPOSE_PROJECT_NAME:/opt/bagbunker/cover ./


Build docker image
==================

In case you want to build the docker image yourself, see the instructions in `base.yml <docker/compose/base.yml>`_. If you need a proxy to access the internet see https://github.com/bosch-ros-pkg/bagbunker/blob/master/Dockerfile#L35.


Python version
==============

For now, we only support the latest Python 2.7 release. If you need support for other versions, please let us know your reasons.


Supporters
==========

Bagbunker has been developed for `Deepfield Robotics <http://www.deepfield-robotics.com/>`_.
