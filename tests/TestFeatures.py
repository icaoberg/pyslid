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
from omero.rtypes import unwrap
from numpy import array

from ClientHelper import ClientHelper
import re
import numpy

from pyslid import features
from pyslid.utilities import PyslidException



class TestFeatures(ClientHelper):
    """
    Test methods in pyslid.features using a fake featureset
    Only methods which appear to be useful are tested
    """

    def setUp(self):
        super(TestFeatures, self).setUp()
        self.fake_ftset = 'test'

    def tableImageAnnotation(self, table, iid):
        fa = omero.model.FileAnnotationI()
        fa.setFile(table.getOriginalFile())
        annLink = omero.model.ImageAnnotationLinkI()
        annLink.link(omero.model.ImageI(iid, False), fa)
        self.conn.getUpdateService().saveObject(annLink)

    def createImageAndFeatures(self):
        iid = self.createImageWithRes()
        scale = 0.5
        fids = ['f1', 'f2']
        feats = array([1.0, 2.0])
        px = 123
        ch = 0
        z = 5
        t = 41
        features.link(self.conn, iid, scale, fids, feats, self.fake_ftset,
                      field=True, rid=None, pixels=px, channel=ch,zslice=z,
                      timepoint=t)
        return iid

    def checkFeaturesTable(self, t):
        self.assertEqual([c.name for c in t.getHeaders()],
                         ['pixels', 'channel', 'zslice', 'timepoint', 'scale',
                          'f1', 'f2'])
        self.assertEqual(t.getNumberOfRows(), 1)
        self.assertEqual([c.values[0] for c in t.readCoordinates([0]).columns],
                         [123L, 0L, 5L, 41L, 0.5, 1.0, 2.0])


    def test_get_table(self):
        # Testing features.get()
        iid = self.createImage()
        option = 'table'
        self.assertRaises(PyslidException, features.get,
                          self.conn, option, iid, scale=0.5, set="test",
                          field=True, rid=None, pixels=123, channel=0,
                          zslice=5, timepoint=41)

        iid = self.createImageAndFeatures()
        t = features.get(self.conn, option, iid, scale=0.5, set="test",
                         field=True, rid=None, pixels=123, channel=0,
                         zslice=5, timepoint=41)
        self.assertIsNotNone(t)
        self.checkFeaturesTable(t)

    def test_get_vector(self):
        # Testing features.get()
        iid = self.createImageAndFeatures()
        option = 'vector'
        ids, feats = features.get(self.conn, option, iid, scale=0.5, set="test",
                                  field=True, rid=None, pixels=123, channel=0,
                                  zslice=5, timepoint=41)
        self.assertEqual(ids, ['pixels', 'channel', 'zslice', 'timepoint',
                               'scale', 'f1', 'f2'])
        self.assertEqual(feats, [(123L, 0L, 5L, 41L, 0.5, 1.0, 2.0)])

    def test_get_features(self):
        # Testing features.get()
        iid = self.createImageAndFeatures()
        option = 'features'
        ids, feats = features.get(self.conn, option, iid, scale=0.5, set="test",
                                  field=True, rid=None, pixels=123, channel=0,
                                  zslice=5, timepoint=41)
        self.assertEqual(ids, ['f1', 'f2'])
        self.assertEqual(feats, [1.0, 2.0])

    def test_hasTable(self):
        iid = self.createImageWithRes()

        b, r = features.hasTable(
            self.conn, iid, featureset=self.fake_ftset, field=True, rid=None)
        self.assertFalse(b)
        self.assertIsNone(r)

        filename = 'iid-%d_feature-%s_field.h5' % (iid, self.fake_ftset)
        table = self.conn.getSharedResources().newTable(1, filename)
        tid = table.getOriginalFile().getId()
        self.tableImageAnnotation(table, iid)
        table.close()

        b, r = features.hasTable(
            self.conn, iid, featureset=self.fake_ftset, field=True, rid=None)
        self.assertTrue(b)
        self.assertIsNotNone(r)
        self.assertEqual(tid, r.getId())

    def test_link(self):
        iid = self.createImageAndFeatures()
        im = self.conn.getObject('image', iid)
        anns = list(im.listAnnotations())
        self.assertEqual(len(anns), 1)
        self.assertIsInstance(anns[0], omero.gateway.FileAnnotationWrapper)
        self.assertEqual(anns[0].getFileName(),
                         'iid-%d_feature-test_field.h5' % iid)

        t = self.conn.getSharedResources().openTable(anns[0].getFile()._obj)
        self.assertIsNotNone(t)
        self.checkFeaturesTable(t)

    def test_getScales(self):
        iid = self.createImageWithRes()
        filename = 'iid-%d_feature-%s_field.h5' % (iid, self.fake_ftset)
        table = self.conn.getSharedResources().newTable(1, filename)
        cols = [
            omero.grid.LongColumn('pixels', '', [12, 14]),
            omero.grid.LongColumn('channel', '', [1, 5]),
            omero.grid.LongColumn('zslice', '', [42, 36]),
            omero.grid.LongColumn('timepoint', '', [12, 312]),
            omero.grid.DoubleColumn('scale', '', [0.2, 1.1])
            ]
        table.initialize(cols)
        table.addData(cols)
        self.tableImageAnnotation(table, iid)
        table.close()

        s = features.getScales(self.conn, iid, set=self.fake_ftset, field=True,
                               rid=None)
        self.assertTrue(all(s == array([0.2, 1.1])))

    def test_has(self):
        iid = self.createImageAndFeatures()

        b = features.has(self.conn, iid, scale=0.5, set="test",
                         field=True, rid=None, pixels=123, channel=0,
                         zslice=5, timepoint=41)
        self.assertTrue(b)

        b = features.has(self.conn, iid, scale=0.5, set="test",
                         field=True, rid=None, pixels=123, channel=0,
                         zslice=4, timepoint=41)
        self.assertFalse(b)



class TestFeaturesSlf33(ClientHelper):
    """
    Do some basic tests of the SLF33 feature calculation
    """

    def setUp(self):
        super(TestFeaturesSlf33, self).setUp()
        self.real_ftset = 'slf33'

    def test_calculate(self):
        iid = self.createImageWithRes()
        print iid
        scale = 1.0
        ch = [0]
        [ids, feats, scaleo] = features.calculate(
            self.conn, iid, scale=scale, set=self.real_ftset, channels=ch)

        self.assertEqual(len(ids), 161)
        self.assertEqual(len(ids), len(set(ids)))
        self.assertTrue(all([re.match('SLF\d\d\.\d+', i) for i in ids]))

        self.assertEqual(len(feats), len(ids))
        self.assertFalse(any(numpy.isnan(feats)))

        self.assertEqual(scaleo, scale)

    def test_calculate_fail(self):
        """
        If an image of all 0s is given PySLIC seems to return an array of NaNs
        which is shorter than the number of expected features (why?).
        This should be caught instead of returning invalid data to the caller.
        """
        iid = self.createImageWithRes(sizeX=1, sizeY=1)
        print iid
        scale = 1.0
        ch = [0]

        with self.assertRaises(PyslidException):
            [ids, feats, scaleo] = features.calculate(
                self.conn, iid, scale=scale, set=self.real_ftset, channels=ch)

    def test_getIds(self):
        ids = features.getIds(set=self.real_ftset)
        self.assertEqual(len(ids), 161)
        self.assertTrue(all([re.match('SLF\d\d\.\d+', i) for i in ids]))



class TestFeaturesSlf34(ClientHelper):
    """
    Do some basic tests of the SLF34 feature calculation
    """

    def setUp(self):
        super(TestFeaturesSlf34, self).setUp()
        self.real_ftset = 'slf34'

    def test_calculate(self):
        iid = self.createImageWithRes(sizeC=3)
        print iid
        scale = 1.0
        ch = [0, 2]
        [ids, feats, scaleo] = features.calculate(
            self.conn, iid, scale=scale, set=self.real_ftset, channels=ch)

        self.assertEqual(len(ids), 173)
        self.assertEqual(len(ids), len(set(ids)))
        self.assertTrue(all([re.match('SLF\d\d\.\d+', i) for i in ids]))

        self.assertEqual(len(feats), len(ids))
        self.assertFalse(any(numpy.isnan(feats)))

        self.assertEqual(scaleo, scale)

    def test_calculate_fail(self):
        """
        If an image of all 0s is given PySLIC seems to return an array of NaNs
        which is shorter than the number of expected features (why?).
        This should be caught instead of returning invalid data to the caller.
        """
        iid = self.createImageWithRes(sizeX=1, sizeY=1)
        print iid
        scale = 1.0
        ch = [0]

        with self.assertRaises(PyslidException):
            [ids, feats, scaleo] = features.calculate(
                self.conn, iid, scale=scale, set=self.real_ftset, channels=ch)

    def test_getIds(self):
        ids = features.getIds(set=self.real_ftset)
        self.assertEqual(len(ids), 173)
        self.assertTrue(all([re.match('SLF\d\d\.\d+', i) for i in ids]))





if __name__ == '__main__':
    unittest.main()
