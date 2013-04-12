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
import omero
from numpy import array, int8


class ClientHelper(unittest.TestCase):

    def create_client(self):
        cli = omero.client()
        sess = cli.createSession()
        conn = omero.gateway.BlitzGateway(client_obj=cli)
        return (cli, sess, conn)

    def setUp(self):
        """
        Create a connection for creating the test tables.
        ICE_CONFIG must be set.
        """
        self.cli, self.sess, self.conn = self.create_client()

    def tearDown(self):
        self.cli.closeSession()


    def createImage(self, sizeX=5, sizeY=4):
        """
        Create an image from scratch
        http://www.openmicroscopy.org/site/support/omero4/developers/Python.html#create-image
        @return the image ID
        """
        sizeZ, sizeC, sizeT = 1, 1, 1
        plane1 = array([xrange(y, y + sizeX) for y in xrange(sizeY)],
                       dtype=int8)
        planes = [plane1]

        def planeGen():
            for p in planes:
                yield p

        desc = "Test image"
        im = self.conn.createImageFromNumpySeq(
            planeGen(), "numpy image", sizeZ, sizeC, sizeT,
            description=desc, dataset=None)
        return im.getId()

    def createImageWithRes(self):
        iid = self.createImage()
        p = self.conn.getObject('Image', iid).getPrimaryPixels()
        p.setPhysicalSizeX(omero.rtypes.rdouble(10))
        p.setPhysicalSizeY(omero.rtypes.rdouble(20))
        p.setPhysicalSizeZ(omero.rtypes.rdouble(30))
        p.save()
        return iid

