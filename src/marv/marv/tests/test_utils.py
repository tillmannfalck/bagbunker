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

import inspect
import unittest
from logging import getLogger
from testfixtures import LogCapture

from .._utils import multiplex


class TestCase(unittest.TestCase):
    def test_multiplex(self):
        def double(inputs):
            return (2*x for x in inputs)

        def square(inputs):
            return (x*x for x in inputs)

        def fail(_):
            raise Exception("Failing before becoming a generator")

        def fail_later(inputs):
            for x in inputs:
                if x % 2:
                    raise Exception
                else:
                    yield 100 + x

        inputs = range(4)
        processors = [double, square]
        outputs = multiplex(inputs, processors)
        self.assertTrue(inspect.isgenerator(outputs))
        self.assertEquals(list(outputs), [0, 0, 2, 1, 4, 4, 6, 9])

        processors = [double, fail, fail_later]
        outputs = multiplex(inputs, processors, logger=getLogger(self.id()))
        self.assertTrue(inspect.isgenerator(outputs))
        with LogCapture(self.id()) as log:
            self.assertEquals(list(outputs), [0, 100, 2, 4, 6])
            self.assertEquals(len(log.records), 2)
