FROM docker.ternaris.com/bagbunker-develop/bagbunker
MAINTAINER Ternaris

# kill env.sh and start.sh
RUN sudo bash -c "echo -n > /env.sh && echo -n > /start.sh"

# unset variables
ENV DOCKER_IMAGE_MARV_SKEL_SITE ""
ENV MARV_INSTANCE_PATH ""
ENV MARV_VENV ""
ENV MATPLOTLIBRC ""
ENV PGHOSTADDR ""
ENV PGPASSWORD ""
ENV PGUSER ""
ENV PIP_FIND_LINKS ""
ENV STATE_DIR ""
ENV VENV ""

###  Test manual installation steps
#
# bagbunker code is checked out at $BB_CODE

# env vars
ENV PIP_FIND_LINKS=https://ternaris.com/pypi
ENV PGUSER=bagbunker
ENV PGPASSWORD=bagbunker
# needs to be set inside container
#ENV PGHOSTADDR ""
ENV SITE=/home/$MARV_USER/site
ENV MARV_INSTANCE_PATH=$SITE
ENV MATPLOTLIBRC=$SITE
ENV MARV_VENV=$BB_CODE

# Fontend tooling
WORKDIR $HOME
RUN bash -c "curl https://ternaris.com/bngl.tar.gz |tar xz"
RUN bash -c "cd bngl/bungle-ember && npm --loglevel info install"

# virtualenv and install python packages
WORKDIR $BB_CODE
RUN bash -c "virtualenv --system-site-packages -p python2.7 ."
RUN bash -c "source bin/activate && \
    pip install pip-tools==1.4.4 && \
    pip-sync src/*/requirements.txt && \
    pip install src/marv src/bagbunker src/deepfield_jobs"

COPY env.sh /env.sh
COPY start.sh /start.sh

WORKDIR $HOME
RUN bash -c "marv init $SITE"
RUN bash -c "cd $SITE/frontend && bungle-ember build"

# Run manually inside container with postgres available
# bagbunker admin initdb
# bagbunker scan --read-pending example-bags
# bagbunker run-jobs --all

CMD bash -c "bagbunker webserver --public"
