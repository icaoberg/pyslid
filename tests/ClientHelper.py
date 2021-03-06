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

import sys
if sys.version_info < (2, 7):
    import unittest2 as unittest
else:
    import unittest
import omero
import numpy as np


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


    def checkerboard(self, dx, dy, nx, ny, wave=None):
        """
        Create a 2D array with a checkerboard pattern
        dx, dy: The width and height of one square in the pattern
        nx, ny: Width and Height of the image
        wave: If given superimpose a sin wave with this period
        """
        t = np.vstack((
                np.hstack(( np.zeros((dy, dx)), np.ones((dy, dx)) )),
                np.hstack(( np.ones((dy, dx)), np.zeros((dy, dx)) ))
                ))
        im = np.tile(
            t, (np.ceil(float(ny) / dy / 2), np.ceil(float(nx) / dx / 2)))
        im = im[:ny, :nx]

        if wave:
            gridx = np.array([range(nx)] * ny)
            gridy = np.array([range(ny)] * nx).transpose()
            d = np.sqrt(np.power(gridx, 2) + np.power(gridy, 2))
            im = im * (1 + np.sin(d * np.pi * 2 / wave)) * 64

        return im


    def createImage(self, sizeX=10, sizeY=10, sizeZ=1, sizeC=1, sizeT=1,
                    reorder=None, check=True):
        """
        Create an image from scratch
        http://www.openmicroscopy.org/site/support/omero4/developers/Python.html#create-image

        reorder: An optional list of indicies giving the order in which the
        generated XY planes should be appended to form a multi Z/C/T image

        @return the image ID
        """
        if check:
            d = max(max(sizeX, sizeY) / 16, 1)
            planes = [
                self.checkerboard(d * zct, d * zct, sizeX, sizeY, zct * 4 * d)
                for zct in xrange(1, sizeZ * sizeC * sizeT + 1)]
        else:
            planes = [
                np.array([xrange(y, y + sizeX) for y in xrange(sizeY)],
                         dtype=np.int8) * (zct + 1)
                for zct in xrange(sizeZ * sizeC * sizeT)]

        if reorder:
            planes = [planes[r] for r in reorder]

        def planeGen():
            for p in planes:
                yield p

        desc = "Test image"
        im = self.conn.createImageFromNumpySeq(
            planeGen(), "numpy image", sizeZ, sizeC, sizeT,
            description=desc, dataset=None)

        iid = im.getId()
        print 'Created Image: %d' % iid
        return iid

    def createImageWithRes(self, sizeX=10, sizeY=10, sizeZ=1, sizeC=1, sizeT=1,
                           reorder=None, check=True):
        iid = self.createImage(sizeX, sizeY, sizeZ, sizeC, sizeT,
                               reorder, check)
        p = self.conn.getObject('Image', iid).getPrimaryPixels()
        p.setPhysicalSizeX(omero.rtypes.rdouble(10))
        p.setPhysicalSizeY(omero.rtypes.rdouble(20))
        p.setPhysicalSizeZ(omero.rtypes.rdouble(30))
        p.save()
        return iid

