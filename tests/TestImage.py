#!/usr/bin/env python
# -*- coding: utf-8 -*-

#
# Copyright (C) 2013 University of Dundee & Open Microscopy Environment.
# All rights reserved.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

#
#

import unittest
from ClientHelper import ClientHelper
import omero

from pyslid import image


class TestImage(ClientHelper):
    def setUp(self):
        super(TestImage, self).setUp()

    def test_getResolution(self):
        iid = self.createImageWithRes()
        r = image.getResolution(self.conn, iid)
        self.assertEqual(r, [10, 20, 30])

    def test_getNominalMagnification(self):
        iid = self.createImageWithRes()
        m = image.getNomimalMagnification(self.conn, iid)
        # TODO: This might be wrong- if physicalSizeX is the sample size as
        # opposed to the detector size then isn't the magnification irrelevant?

    def test_getScale(self):
        iid = self.createImageWithRes()
        s = image.getScale(self.conn, iid)
        self.assertEqual(s, [0.25, 0.5, 0.75])

    def test_imageWithoutResolution(self):
        iid = self.createImage()
        r = image.getResolution(self.conn, iid)
        self.assertEqual(r, [0., 0., 0.])



if __name__ == '__main__':
    unittest.main()
