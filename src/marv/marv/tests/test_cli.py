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

import sys
import unittest
from click.testing import CliRunner
#from unittest.mock import patch
from marv.cli import cli
from marv.testing import create_tempdir


CATCH_EXCEPTIONS = not set(['--pdb', '--ipdb']).intersection(set(sys.argv))


class TestCli(unittest.TestCase):
    def setUp(self):
        self.test_dir, self.cleanup_test_dir = create_tempdir()
        self.runner = CliRunner()

    def tearDown(self):
        self.cleanup_test_dir()

    def marv(self, cli_args, exit_code=0, env=None):
        cmd = self.runner.invoke(cli, cli_args, env=env,
                                 catch_exceptions=CATCH_EXCEPTIONS)
        if CATCH_EXCEPTIONS:
            traceback.print_exception(*cmd.exc_info, file=sys.stdout)
            sys.stdout.write(cmd.output_bytes)
        self.assertEqual(cmd.exit_code, exit_code)

    def test_marv(self):
        marv = self.marv
