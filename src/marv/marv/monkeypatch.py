# -*- coding: utf-8 -*-

from __future__ import absolute_import, division

import math
import os
import watchdog.observers
from flask.ext.restless import views
from flask.ext.restless.helpers import count
from flask import request


def _paginated(self, instances, deep):
    """Returns a paginated JSONified response from the specified list of
    model instances.

    `instances` is either a Python list of model instances or a
    :class:`~sqlalchemy.orm.Query`.

    `deep` is the dictionary which defines the depth of submodels to output
    in the JSON format of the model instances in `instances`; it is passed
    directly to :func:`helpers.to_dict`.

    The response data is JSON of the form:

    .. sourcecode:: javascript

       {
         "page": 2,
         "total_pages": 3,
         "num_results": 8,
         "objects": [{"id": 1, "name": "Jeffrey", "age": 24}, ...]
       }

    """
    if isinstance(instances, list):
        num_results = len(instances)
    else:
        num_results = count(self.session, instances)
    results_per_page = self._compute_results_per_page()
    if results_per_page > 0:
        # get the page number (first page is page 1)
        page_num = int(request.args.get('page', 1))
        start = (page_num - 1) * results_per_page
        end = min(num_results, start + results_per_page)
        total_pages = int(math.ceil(num_results / results_per_page))
    else:
        page_num = 1
        start = 0
        end = num_results
        total_pages = 1
    objects = [self.serialize(x) for x in instances[start:end]]
    return dict(page=page_num, objects=objects, total_pages=total_pages,
                num_results=num_results)

views.API._paginated = _paginated


def _add_dir_watch(self, path, recursive, mask):
    """
    Adds a watch (optionally recursively) for the given directory path
    to monitor events specified by the mask.

    :param path:
        Path to monitor
    :param recursive:
        ``True`` to monitor recursively.
    :param mask:
        Event bit mask.
    """
    if not os.path.isdir(path):
        raise OSError('Path is not a directory')
    self._add_watch(path, mask)
    if recursive:
        try:
            for root, dirnames, _ in os.walk(path):
                for dirname in dirnames:
                    full_path = os.path.join(root, dirname)
                    if os.path.islink(full_path):
                        continue
                    self._add_watch(full_path, mask)
        except OSError:
            pass

watchdog.observers.inotify_c.Inotify._add_dir_watch = _add_dir_watch
