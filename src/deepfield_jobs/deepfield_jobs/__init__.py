# -*- coding: utf-8 -*-
#
# Copyright 2015 Ternaris, Munich, Germany
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

from __future__ import absolute_import, division

# import os
# from pkgutil import iter_modules

# # autoload public submodules
# path = __file__.rsplit(os.sep, 1)[0]
# for importer, name, ispkg in iter_modules([path]):
#     if ispkg or name[0] == '_':
#         continue

#     fullname = '.'.join([__package__, name])
#     mod = importer.find_module(fullname).load_module(fullname)

from . import view  # noqa

from . import annotations  # noqa
from . import camera_frames  # noqa
from . import cpu_diagnostics  # noqa
from . import diagnostics  # noqa
from . import events  # noqa
from . import extract_trajectories  # noqa
from . import gps_track  # noqa
from . import metadata  # noqa
from . import onewire_temperature  # noqa
from . import sanity_check_job  # noqa
