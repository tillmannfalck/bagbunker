Changelog (Bagbunker)
=====================

x.y.z (unreleased)
------------------

3.2.0 (2016-06-29)
------------------

- [BUGFIX] fix gps plot memory leak
  `#84 https://github.com/bosch-ros-pkg/bagbunker/pull/84`_
- [BUGFIX] update .dockerignore for docker 1.11.1
  `#87 https://github.com/bosch-ros-pkg/bagbunker/pull/87`_
- [FEATURE] add 4dscan sanity check job
  `#85 https://github.com/bosch-ros-pkg/bagbunker/pull/85`_
- [FEATURE] add cpu diagnostics job
  `#88 https://github.com/bosch-ros-pkg/bagbunker/pull/88`_
- [FEATURE] reduce camera preview images resolution & quality
  `#90 https://github.com/bosch-ros-pkg/bagbunker/pull/88`_
- replace docker-compose with basic docker commands


3.1.0 (2016-04-27)
------------------

- [BUGFIX] add missing api endpoint to query jobruns
  `#70 <https://github.com/bosch-ros-pkg/bagbunker/issues/70>`_
- [BUGFIX] warn about discarded incomplete filesets
  `#66 <https://github.com/bosch-ros-pkg/bagbunker/issues/66>`_
- [BUGFIX] do not feed jobs that have finished early
- [BUGFIX] only update fileset with changed missing state
  `#71 <https://github.com/bosch-ros-pkg/bagbunker/issues/71>`_
- [FEATURE] verify md5 files
  `#60 <https://github.com/bosch-ros-pkg/bagbunker/issues/60>`_
- [FEATURE] update gps job to work with more topics and message types
  `#72 <https://github.com/bosch-ros-pkg/bagbunker/pull/72>`_
  `#68 <https://github.com/bosch-ros-pkg/bagbunker/issues/68>`_
- [FEATURE] camera topics update for deepfield
  `#74 <https://github.com/bosch-ros-pkg/bagbunker/pull/74>`_
- [FEATURE] metadata robot_name read from topic
  `#73 <https://github.com/bosch-ros-pkg/bagbunker/pull/73>`_
  `#69 <https://github.com/bosch-ros-pkg/bagbunker/issues/69>`_
- [FEATURE] remove deprecated force flag from docker tag
  `#64 <https://github.com/bosch-ros-pkg/bagbunker/pull/64>`_
- setuptool-20.10.1, pip-8.1.1, pip-tools-1.6.1
- [BUGFIX] silence INFO logging of requests lib


3.0.0 (2016-02-03)
------------------

- [BUGFIX] Fix bulk tagging
- Added changelog
- Added Makefile for docker image build and release management
- [BUGFIX] bbmsg fixes, tool for playing ROS messages directly from bagbunker (formerly bbat)
  `#4 <https://github.com/bosch-ros-pkg/bagbunker/issues/4>`_
  `#8 <https://github.com/bosch-ros-pkg/bagbunker/issues/8>`_
  `#9 <https://github.com/bosch-ros-pkg/bagbunker/issues/9>`_
  Still careful with it, will receive more love during 3.1.
- run tests as part of docker image build
- [CLEANUP] docker setup, repository
- python package updates
- docker image: Python 2.7.11
- [FEATURE] introduce ``marv init`` for site management (frontend, wsgi file, venv, matplotlibrc, alembic)
- [FEATURE] simplify filter API
- [FEATURE] simplify listing API and cache in memory, base for synchronization of bagbunker instances
- properly install python packages, install in development mode manually
- [FEATURE] docker image runs out-of-the-box without additional initialization, cheap throw-a-way containers
- [FEATURE[ enable building docker images for currently checked out branch
- [FEATURE] Support and document manual installation
  `#7 <https://github.com/bosch-ros-pkg/bagbunker/issues/7>`_
- basic sphinx setup
- [FEATURE] enable scanner to match on full path
- [FEATURE] add c3_widget decorator
- only show bags in listing, prepare for app-specific listing
- [BUGFIX] fix for filesets other than bags
- [FEATURE] load add-on apps via entry point
- [BUGFIX] tooling fixes
- [BUGFIX] fix broken test


3.0.dev0.2015-12-15
-------------------

- initial release of complete rewrite
- flask-based backend
- emberjs-based frontend
