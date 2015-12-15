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

import bcrypt
import os
import sys
import traceback
import unittest
from click.testing import CliRunner
from pkg_resources import resource_filename

from bagbunker.cli import cli
from marv.testing import create_tempdir, list_nondot


TEST_BAG = resource_filename(__name__, os.sep.join(('bags', 'test.bag')))
CATCH_EXCEPTIONS = not set(['--pdb', '--ipdb']).intersection(set(sys.argv))

BASEDIR1 = resource_filename(__name__, 'bags')
BASEDIR2 = resource_filename(__name__, 'bags2')


@unittest.skip
class TestCase(unittest.TestCase):
    def setUp(self):
        self.instance_path, self.tempdir_cleanup = create_tempdir()
        with open(os.sep.join([self.instance_path, 'users.txt']), 'wb') as f:
            f.write('m:{}\n'.format(bcrypt.hashpw('m', bcrypt.gensalt())))
        self.runner = CliRunner()

    def tearDown(self):
        self.tempdir_cleanup()

    def bagbunker(self, cli_args, exit_code=0):
        bagbunker = self.runner.invoke(cli, cli_args,
                                       catch_exceptions=CATCH_EXCEPTIONS)
        if CATCH_EXCEPTIONS:
            traceback.print_exception(*bagbunker.exc_info, file=sys.stdout)
            sys.stdout.write(bagbunker.output_bytes)
        self.assertEqual(bagbunker.exit_code, exit_code)

    def test_scan(self):
        bagbunker = lambda *args: \
            self.bagbunker(('--instance-path', self.instance_path) + args,
                           exit_code=0)

        bagbunker('initdb')
        bagbunker('scan', BASEDIR1, BASEDIR2)
        storagepath = os.sep.join([self.instance_path, 'storage'])
        self.assertEqual(list_nondot(storagepath),
                         ['1f1771610d4a7bf9444f206415733be5',
                          '21ad742152a53d3786e329e264bd240a',
                          '3544aad5c20f5d80b30472c2fa8bdc06',
                          '5cb751ab514b946cb9d1a72ea77c5f32',
                          '6eeaf7aacc7004f75da6f432f2a69703',
                          '8d15321bdd5e19c4d952a7986b858ae8',
                          'aed68c401fedcb04fc0c856ca68661ed'])
