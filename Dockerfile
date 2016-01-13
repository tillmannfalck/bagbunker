FROM ubuntu
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
ENV MARV_UID 65533
ENV MARV_GID 65533
ENV MARV_USER bagbunker
ENV MARV_GROUP bagbunker
ENV MARV_ROOT /opt/bagbunker
ENV MARV_ROOT_INSIDE_CONTAINER $MARV_ROOT/.inside-container
ENV BASH_ENV /env.sh
ENV DEBIAN_FRONTEND noninteractive

# Set proxy if needed, e.g. for a local cntlm proxy.
# Adjust to IP address of docker0 interface, where cntlm proxy is running.
# If needed, then only to build images. Images are usually fetched
# from a registry and environment variables can be set during runime
# (see README.md)
#ENV http_proxy http://172.17.0.1:3128/
#ENV https_proxy http://172.17.0.1:3128/

RUN groupadd -g $MARV_UID $MARV_GROUP && \
    useradd -m -u $MARV_UID -g $MARV_GID $MARV_USER

RUN echo 'Defaults env_keep += "APACHE_RUN_USER APACHE_RUN_GROUP APACHE_LOG_DIR APACHE_PID_FILE APACHE_RUN_DIR APACHE_LOCK_DIR APACHE_SERVERADMIN APACHE_SERVERNAME APACHE_SERVERALIAS IMAGE_TIMESTAMP MARV_INSTANCE_PATH MARV_UID MARV_GID MARV_USER MARV_GROUP MARV_ROOT MARV_PKGS_DIR POSTGRES_PORT_5432_TCP_ADDR http_proxy https_proxy"\nALL ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers

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

# Use system-wide pip only to install virtualenv, then deactivate it
RUN pip install --upgrade virtualenv
RUN chmod -x $(which pip)

RUN cd /opt && curl https://nodejs.org/dist/v5.2.0/node-v5.2.0-linux-x64.tar.gz |tar xz
RUN cd /usr/local/bin && ln -s /opt/node-v*/bin/node && ln -s /opt/node-v*/bin/npm
RUN node -v && npm -v
RUN cd /opt && curl https://ternaris.com/bngl.tar.gz |tar xz
RUN cd /opt/bngl/bungle-ember && npm install
RUN cd /usr/local/bin && ln -s /opt/bngl/bungle-ember/bin/bungle-ember

COPY .git /tmp/bb.git
RUN mkdir -p $MARV_ROOT && \
    cd $MARV_ROOT && \
    git init && \
    git remote add bb /tmp/bb.git && \
    git fetch bb && \
    git checkout $(cut -d/ -f3 < /tmp/bb.git/HEAD) && \
    git remote rm bb && \
    rm .git/FETCH_HEAD && \
    git gc --aggressive && \
    rm -rf /tmp/bb.git
RUN touch $MARV_ROOT_INSIDE_CONTAINER
RUN chown -R $MARV_USER:$MARV_GROUP $MARV_ROOT

COPY docker/bb-server/000-default.conf /etc/apache2/sites-available/
COPY docker/bb-server/env.sh /
RUN echo '. /env.sh' >> /etc/bash.bashrc
COPY docker/bb-server/start.sh /
RUN chmod 0755 /start.sh

USER $MARV_USER

WORKDIR $MARV_ROOT
ENTRYPOINT ["/start.sh"]
CMD ["apache2"]

RUN sudo touch $IMAGE_TIMESTAMP

# Initialize extensions
RUN /bin/bash -c /start.sh bash
