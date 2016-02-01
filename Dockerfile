# the latest ubuntu ROS indigo supports
FROM ubuntu:trusty
MAINTAINER Ternaris

EXPOSE 80
VOLUME ["/mnt/bags", "/var/lib/bagbunker"]

RUN locale-gen en_US.UTF-8; dpkg-reconfigure -f noninteractive locales
RUN echo "Europe/Berlin" > /etc/timezone; dpkg-reconfigure -f noninteractive tzdata
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US.UTF-8
ENV LC_ALL en_US.UTF-8

ENV APACHE_RUN_USER www-data
ENV APACHE_RUN_GROUP www-data
ENV APACHE_LOG_DIR /var/lib/bagbunker/log
ENV APACHE_PID_FILE /var/run/apache2.pid
ENV APACHE_RUN_DIR /var/run/apache2
ENV APACHE_LOCK_DIR /var/lock/apache2
ENV APACHE_SERVERADMIN admin@localhost
ENV APACHE_SERVERNAME localhost
ENV APACHE_SERVERALIAS docker.localhost
ENV IMAGE_TIMESTAMP /.image-timestamp
ENV MARV_INSTANCE_PATH /var/lib/bagbunker
ENV MARV_USER bagbunker
ENV MARV_GROUP bagbunker
ENV BASH_ENV /env.sh
ENV DEBIAN_FRONTEND noninteractive

# Set proxy if needed, e.g. for a local cntlm proxy.
# Adjust to IP address of docker0 interface, where cntlm proxy is running.
# If needed, then only to build images. Images are usually fetched
# from a registry and environment variables can be set during runime
# (see README.md)
#ENV http_proxy http://172.17.0.1:3128/
#ENV https_proxy http://172.17.0.1:3128/

RUN groupadd -g 65533 $MARV_GROUP && \
    useradd -m -u 65533 -g 65533 $MARV_USER

RUN echo 'Defaults env_keep += "APACHE_RUN_USER APACHE_RUN_GROUP APACHE_LOG_DIR APACHE_PID_FILE APACHE_RUN_DIR APACHE_LOCK_DIR APACHE_SERVERADMIN APACHE_SERVERNAME APACHE_SERVERALIAS IMAGE_TIMESTAMP MARV_INSTANCE_PATH MARV_UID MARV_GID MARV_USER MARV_GROUP MARV_PKGS_DIR PGHOSTADDR PGUSER PGPASSWORD POSTGRES_PORT_5432_TCP_ADDR PYTHONPATH http_proxy https_proxy"\nALL ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers

# Latest python2.7 for trusty
RUN bash -c 'echo "deb http://ppa.launchpad.net/fkrull/deadsnakes-python2.7/ubuntu trusty main" \
    > /etc/apt/sources.list.d/python2.7.list'
RUN apt-key adv --keyserver hkp://pool.sks-keyservers.net --recv-key 0xDB82666C

RUN apt-get update && \
    apt-get install -y \
        apache2 \
        apache2-utils \
        curl \
        git \
        libapache2-mod-wsgi \
        libapache2-mod-xsendfile \
        mailutils \
        postgresql-client \
        python-pip \
        vim

RUN a2enmod rewrite


# Include bagbunker init.sh for the time being
RUN bash -c 'echo "deb http://packages.ros.org/ros/ubuntu $(lsb_release -sc) main" \
    > /etc/apt/sources.list.d/ros-latest.list'
RUN apt-key adv --keyserver hkp://pool.sks-keyservers.net --recv-key 0xB01FA116
RUN apt-get update && \
    apt-get install -y \
     ros-indigo-rosbag \
     ros-indigo-rostest \
     ros-indigo-common-msgs \
     ros-indigo-cv-bridge
RUN rosdep init
RUN su -c "rosdep update" $MARV_USER


# Use system-wide pip only to install virtualenv, then deactivate it
RUN pip install --upgrade virtualenv==13.1.2
RUN chmod -x $(which pip)


# Frontend tooling -- should this happen as non-root?
RUN cd /opt && curl https://nodejs.org/dist/v5.2.0/node-v5.2.0-linux-x64.tar.gz |tar xz
RUN cd /usr/local/bin && ln -s /opt/node-v*/bin/node && ln -s /opt/node-v*/bin/npm
RUN node -v && npm -v
RUN cd /opt && curl https://ternaris.com/bungle/bngl-20160201.tar.gz |tar xz
RUN cd /opt/bngl/bungle-ember && npm --loglevel info install
RUN cd /usr/local/bin && ln -s /opt/bngl/bungle-ember/bin/bungle-ember
RUN rm -Rf /tmp/npm-*


ENV PIP_FIND_LINKS https://ternaris.com/pypi https://ternaris.com/wheels


# This speeds up the build somewhat as a changed git dir does not mean rebuilding the venv
COPY src/marv/requirements.txt /requirements/req-marv.txt
COPY src/bagbunker/requirements.txt /requirements/req-bagbunker.txt
COPY src/deepfield_jobs/requirements.txt /requirements/req-deepfield.txt
ENV VENV /opt/bagbunker-venv
# MARV_VENV is linked into site dir
ENV MARV_VENV $VENV
ENV STATE_DIR $VENV/.state
RUN mkdir -p $VENV $STATE_DIR && \
    chown -R $MARV_USER:$MARV_GROUP $VENV $STATE_DIR && \
    chmod -R g+w $VENV $STATE_DIR
RUN su -c "virtualenv --system-site-packages -p python2.7 $VENV" $MARV_USER
# For some reason this currently claims to fail, might be pip-7.1.2 coming with virtualenv 13.1.2
#RUN su -c "$VENV/bin/pip install --upgrade 'pip==8.0.0'" $MARV_USER || true
RUN su -c "$VENV/bin/pip install --upgrade 'pip-tools==1.4.4'" $MARV_USER
RUN su -c "source $VENV/bin/activate && pip-sync /requirements/req-*.txt" $MARV_USER


# Copy code into home dir
RUN mkdir -p /home/$MARV_USER/code; chown $MARV_USER:$MARV_GROUP /home/$MARV_USER/code
ENV BB_CODE /home/$MARV_USER/code/bagbunker
COPY .git /tmp/bb.git
RUN mkdir -p $BB_CODE && cd $BB_CODE && \
    git init && \
    git remote add bb /tmp/bb.git && \
    git fetch bb && \
    git checkout $(cut -d/ -f3 < /tmp/bb.git/HEAD) && \
    git remote rm bb && \
    rm .git/FETCH_HEAD && \
    git gc --aggressive && \
    rm -rf /tmp/bb.git
RUN chown -R $MARV_USER:$MARV_GROUP $BB_CODE


# Install python packages into virtual env
RUN su -c "$VENV/bin/pip install --no-index $BB_CODE/src/marv $BB_CODE/src/bagbunker $BB_CODE/src/deepfield_jobs" $MARV_USER
RUN su -c "source $VENV/bin/activate && marv --help && bagbunker --help"
RUN su -c "touch $STATE_DIR/pip-tools $STATE_DIR/venv" $MARV_USER


# Create skeleton site and build its frontend
ENV DOCKER_IMAGE_MARV_SKEL_SITE /opt/bagbunker-skel-site
RUN mkdir -p $DOCKER_IMAGE_MARV_SKEL_SITE && chown $MARV_USER:$MARV_GROUP $DOCKER_IMAGE_MARV_SKEL_SITE
RUN su -c "$VENV/bin/marv init $DOCKER_IMAGE_MARV_SKEL_SITE" $MARV_USER
RUN su -c "cd $DOCKER_IMAGE_MARV_SKEL_SITE/frontend && \
    bungle-ember build" $MARV_USER
RUN rm -rf /tmp/bagbunker


COPY docker/bb-server/000-default.conf /etc/apache2/sites-available/
COPY docker/bb-server/env.sh /
RUN echo '. /env.sh' >> /etc/bash.bashrc
COPY docker/bb-server/start.sh /
RUN chmod 0755 /start.sh

USER $MARV_USER
WORKDIR /home/$MARV_USER

RUN bash -c "nosetests -v $VENV/lib/python2.7/site-packages/{marv,bagbunker,deepfield_jobs}"

ENTRYPOINT ["/start.sh"]
CMD ["apache2"]

RUN sudo touch $IMAGE_TIMESTAMP
