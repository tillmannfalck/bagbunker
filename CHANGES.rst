Changelog (Bagbunker)
=====================


3.0.0 (unreleased)
------------------

- [BUGFIX] Fix bulk tagging
- Added changelog
- Added Makefile for docker image build and release management
- [BUGFIX] bbmsg fixes, tool for playing ROS messages directly from bagbunker (formerly bbat)
  [#4](https://github.com/bosch-ros-pkg/bagbunker/issues/4)
  [#8](https://github.com/bosch-ros-pkg/bagbunker/issues/8)
  [#9](https://github.com/bosch-ros-pkg/bagbunker/issues/9)
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
  [#7](https://github.com/bosch-ros-pkg/bagbunker/issues/7)
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
