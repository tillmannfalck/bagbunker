Contributing
============

- Please do not prepend your branches with ``feature``. All branches except ``develop`` and those starting with ``hotfix-`` and ``release-`` are feature branches.
- Please make pull requests against ``develop``.


Try out Bagbunker in Sandbox
============================
See https://github.com/bosch-ros-pkg/bagbunker/wiki/Sandbox for details.


Getting started
===============

This document describes the setup using docker. For manual installation instructions without docker see `Manual Setup <./doc/manual-setup.rst>`_.


Using a proxy
-------------

All tools should honor the ``http_proxy`` and ``https_proxy`` environment variables. If this does not work, please open a `new issue <https://github.com/bosch-ros-pkg/bagbunker/issues/new>`_. Make sure the proxy variables point to an IP address that is reachable from within the docker container, ``127.0.0.1`` inside your docker container is a different ``127.0.0.1`` than outside. The IP address of the ``docker0`` interface works.


System requirements
-------------------

Bagbunker needs rosbag and uses a postgresql database. So far we support docker to take care of dependencies and service management. Alternatively, you can follow the `manual installation instructions <./doc/manual-setup.rst>`_.

Install docker either via system package management or as outlined in the `official instructions <https://docs.docker.com/installation/>`_. Make sure you have at least docker version 1.8.1::

  % docker --version
  Docker version 1.10.0, build a34a1d59

Add your user to the docker group as described in `Create a Docker group <https://docs.docker.com/installation/ubuntulinux/#create-a-docker-group>`_. Otherwise you will have to use ``sudo docker`` instead of just ``docker``. Relogin or use ``newgrp docker`` to start a new shell. Make sure ``docker`` is listed when running ``groups``.


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

Docker images
-------------

We use two docker containers: one for the postgres database and one for bagbunker itself. You can use docker images provided by us or build them yourself.

Postgres docker image
~~~~~~~~~~~~~~~~~~~~~

For postgres we use the official postgres images and publish a latest known good image::

  % docker pull docker.ternaris.com/bagbunker/postgres:latest
  % docker tag docker.ternaris.com/bagbunker/postgres:latest bagbunker-postgres:latest

To use the latest official image regardless of whether bagbunker was tested with it::

  % docker pull postgres:latest
  % docker tag postgres:latest bagbunker-postgres:latest

Bagbunker docker image - prebuilt
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To use the official stable bagbunker image::

  % docker pull docker.ternaris.com/bagbunker/bagbunker:latest
  % docker tag docker.ternaris.com/bagbunker/bagbunker:latest bagbunker:latest

During an upcoming release there is also a ``staging`` image build from the release branch and sometimes there is a ``develop`` image build from the develop branch. To use these replace above all 3 occurrences of ``latest`` accordingly.

Bagbunker docker image - custom built
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To build your own bagbunker image, checkout the desired branch and run make. Beware that only committed changes will make it into the image. To actually develop on bagbunker you'll mount the code from the outside and instruct the container to install the python packages in development mode (see Development below)::

  % git checkout develop
  % make
  docker build -t bagbunker:3.1.0-17-g11ad3b2 .
  Sending build context to Docker daemon 4.961 MB
  Step 1 : FROM ubuntu:trusty
  ---> 14b59d36bae0
  ...
  Image built: bagbunker:3.1.0-17-g11ad3b2

Note the image name and revision, you'll need it to create the container in the next step.


Create and run containers
-------------------------

First off, the postgres and bagbunker container need a shared environment file::

  % cat >bagbunker.env <<EOF
  PGDATA=/var/lib/postgresql/data/pgdata
  POSTGRES_PASSWORD=bagbunker
  POSTGRES_USER=bagbunker
  EOF
  % chmod 600 bagbunker.env

Containers are created using ``docker run``; see https://docs.docker.com/engine/reference/run/ for more information. Containers are started and stopped using ``docker start <name>`` and ``docker stop <name>``. The chosen restart policy will start previously running containers after a reboot.


Postgres container
~~~~~~~~~~~~~~~~~~

For **production**::

  % docker run --restart unless-stopped --detach \
      --name bbproduction-db \
      --volume /var/lib/bagbunker:/var/lib/postgresql/data \
      --env-file bagbunker.env \
      bagbunker-postgres:latest

For **development** you'll probably want to use a local folder instead of placing the database into ``/var/lib`` and give the container a different name::

  % docker run --restart unless-stopped --detach \
      --name bbdev-db \
      --volume $PWD/data:/var/lib/postgresql/data \
      --env-file bagbunker.env \
      bagbunker-postgres:latest

Bagbunker container
~~~~~~~~~~~~~~~~~~~

Independent of whether you use the ``latest``, ``staging``, or ``develop`` image or created one yourself, you can use this image to create a container for production, for production with the possibility to make hotfixes and for development. Replace ``bagbunker:latest`` with the desired image.

For **production**::
  
  % docker run --restart unless-stopped --detach \
      --name bbproduction \
      --link bbproduction-db:postgres \
      --volume /mnt/bags:/mnt/bags \
      --volume /var/lib/bagbunker:/var/lib/bagbunker \
      --publish 80:80 \
      --env-file bagbunker.env \
      bagbunker:latest

The container contains a copy of bagbunker's source and can be instructed to install this in editable mode - it uses ``pip install -e`` - which enables you to make changes e.g. for hotfixes::

  % docker run --restart unless-stopped --detach \
      --name bbproduction \
      --link bbproduction-db:postgres \
      --volume /mnt/bags:/mnt/bags \
      --volume /var/lib/bagbunker:/var/lib/bagbunker \
      --publish 80:80 \
      --env-file bagbunker.env \
      --env DEVELOP="code/bagbunker/src/bagbunker code/bagbunker/src/deepfield_jobs" \
      bagbunker:latest

**WARNING**: Changes inside the container will be gone if you remove and recreate the container. It is possible to `commit a container <https://docs.docker.com/engine/reference/commandline/commit/>`_ to an image.

For **development** the current working directory ``$PWD`` is mounted to hide the source checkout contained within the container ``/home/bagbunker/code/bagbunker`` and the container is instructed to install one or more of the python packages into develop mode; separated by spaces and enclosed in double quotes::

  docker run --rm \
    --name bbdev \
    --link bbdev-db:postgres \
    --volume /mnt/bags:/mnt/bags \
    --volume $PWD/data:/var/lib/bagbunker \
    --volume $PWD:/home/bagbunker/code/bagbunker \
    --publish 5000:5000 \
    --publish 8000:80 \
    --env-file bagbunker.env \
    --env DEVELOP="code/bagbunker/src/deepfield_jobs" \
    bagbunker:latest

For the development container is a throw-away container and will be removed when stopped.


Interacting with a container
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

While a container is running, commands can be executed within using ``docker exec``::

  % docker exec -it bbdev bash -c 'bagbunker --help'

To start a shell within a docker container use::

  % docker exec -it bbdev bash


Add users
---------

Create some bagbunker users for web login/access::

  % docker exec -it bbdev bash -c "sudo htpasswd -B /var/lib/bagbunker/users.txt john"

Scan bags
---------

::

  % docker exec -it bbdev bash -c "bagbunker scan /mnt/bags"

Read metadata from bags (especially over NFS this may take a while)::

  % docker exec -it bbdev bash -c "bagbunker read-pending"

And run jobs (this will take a while)::

  % docker exec -it bbdev bash -c "bagbunker run-jobs --all"

Between and during each of these steps you can visit bagbunker with your browser on the chosen port.


Add cronjob for periodic scanning (production-only)
---------------------------------------------------

Edit crontab::

  % crontab -e

and paste into crontab and adjust to your needs::

  */15 * * * * flock -n /tmp/bbproduction-cron docker exec bbproduction bash -c "bagbunker scan --read-pending --run-all-jobs /mnt/bags"


Backups
=======

All data that is extracted from bag files, generated by jobruns, and comments and tags created by users via web, is stored in ``/var/lib/bagbunker``, resp. ``$PWD/data``, resp. the directory you have chosen. In order to make a backup with minimum downtime::

  % rsync -n -vaHP --delete /var/lib/bagbunker/ /var/lib/bagbunker-backup/

Verify that everything is to your liking and rerun without ``-n``::

  % rsync -vaHP --delete /var/lib/bagbunker/ /var/lib/bagbunker-backup/
  % docker stop bbproduction
  % docker stop bbproduction-db
  % rsync -vaHP --delete /var/lib/bagbunker/ /var/lib/bagbunker-backup/
  % docker start bbproduction-db
  % docker start bbproduction

Upgrades
========

Before any upgrade make sure you have an up-to-date backup of your data directory and bagbunker is not running (see above). Pull or create new image and recreate containers like above.

After an upgrade a database migration might be needed. Check the database in a different terminal::

  % docker exec -ti bbproduction bash -c "bagbunker admin checkdb"

In case migration is needed you are greeted by instructions to perform the upgrade.



Development
===========

In addition to everything explained above, there are a couple of things relevant only for development.

Bagbunker group and adjust permissions for development
------------------------------------------------------

For development the repository is mounted into the docker container and some or all packages are installed manually into development mode (see next section). For this to succeed the user within the docker container needs to be able to write ``*.egg-info`` directories::

  % sudo chown :65533 src/*
  % sudo chmod g+w src/*

Check for existing directories and remove them if the permissions are wrong::

  % ls -l src/*/*.egg-info


Develop existing and new packages
---------------------------------

Using ``--env DEVELOP="code/bagbunker/src/deepfield_jobs`` for ``docker run`` will instruct the docker container to install ``deepfield_jobs`` into development mode (see above). Alternatively, you can do so manually::

  % docker exec -ti bbdev bash -c "pip install -e code/bagbunker/src/deepfield_jobs"

After that, changes to files within ``deepfield_jobs`` will be immediately available for job runs within the docker container. You can also create your own job package: take ``deepfield_jobs`` as an example and adjust setup.py accordingly.


Switching between branches and after upgrades
---------------------------------------------

Python creates bytecode versions of all modules. In case you or we removed a module or a module exists in one but not the other branch, this confuses python. Make sure to delete these files after pulls and branch switches or add the following code as ``.git/hooks/post-checkout`` and ``.git/hooks/post-merge``::

  #!/usr/bin/env bash

  # Change to project root
  cd ./$(git rev-parse --show-cdup)

  # Delete pyc files
  find . -name '*.pyc' -delete >/dev/null 2>&1 || true


Development webserver
---------------------

If you are developing on view code, you might want the development webserver which automatically reloads changed files. Run in separate terminal::

  % docker exec -ti bbdev bash -c "bagbunker webserver --public"

It is served by default at ``127.0.0.1:5000``.


Deleting database
-----------------

In order to delete the database just remove the data directory::

  % docker exec -ti bbdev bash -c 'sudo rm -fr /home/bagbunker/code/bagbunker/data'
  % docker stop bbdev
  % docker stop bbdev-db
  % docker start bbdev-db
  % docker start bbdev


Job development
===============

Jobs have a `__version__` which needs to be increased in order to run a job again for the same filesets. Especially for development you can force bagbunker to run a job, e.g.::

  % ./bin/bagbunker run-jobs --force deepfield::metadata

In order to develop your own jobs, add them to ``src/deepfield_jobs`` package with appropriate copyright headers and make sure to import your jobs from the package's ``__init__.py``. In the future we will rename ``deepfield_jobs`` to ``bagbunker_jobs``. Pull requests with new jobs are welcome! Creating your own jobs in a separate repository is in the development, see: https://github.com/bosch-ros-pkg/bagbunker/pull/91.


Coverage report
===============

To get a coverage report::

  % docker exec -it bbdev bash -c 'cd $BB_CODE && nosetests --with-coverage'

In development setups, the coverage report is created in ``./cover/index.html`` and a summary is displayed in the terminal. For this to succeed the bagbunker group (65533) needs to have write permissions on the repository checkout.

In order to access the coverage report in a production environment, you have to copy it out of the docker container::

  % docker cp bbdev:/opt/bagbunker/cover ./


Custom jobs in production / build docker image
==============================================

There is a Makefile to build and tag docker images for ``develop``, ``staging`` and ``latest`` (in line with docker nomenclature the latest stable image, i.e. master branch).

If you need a proxy to access the internet see https://github.com/bosch-ros-pkg/bagbunker/blob/master/Dockerfile#L30.



Python version
==============

For now, we only support the latest Python 2.7 release. If you need support for other versions, please let us know your reasons.


Supporters
==========

Bagbunker has been developed for `Deepfield Robotics <http://www.deepfield-robotics.com/>`_.
