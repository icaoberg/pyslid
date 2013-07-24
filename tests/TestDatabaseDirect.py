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
from omero.rtypes import unwrap, wrap
from numpy import array
import os
import pickle
import shutil
import tempfile

from ClientHelper import ClientHelper

from pyslid.database import direct as pysliddb



class TestDatabaseDirect(ClientHelper):
    """
    Test methods in pyslid.database
    WARNING: This will delete annotations belonging to the current user/group.
    You should create a dedicated user and use ICE_CONFIG to provide the login
    """

    def setUp(self):
        super(TestDatabaseDirect, self).setUp()
        self.fake_ftset = 'test'
        self.fake_did = 999999
        self.gid = self.conn.getGroupFromContext().getId()
        self.tempdir = tempfile.mkdtemp(prefix='omero_searcher_content_db-')

        # Override the OMERO.searcher contentdb path
        pysliddb.set_contentdb_path(self.tempdir)

    def tearDown(self):
        shutil.rmtree(self.tempdir)

    def getNames(self, did=None):
        """
        The namespace and database file names that we're expecting.
        """
        did = 'all' if did is None else str(did)
        ns = 'direct.edu.cmu.cs.compbio.omepslid:%s_%s' % (did, self.fake_ftset)
        dbn = '%d_%s_%s_content_db_%020d.pkl' % (
            self.gid, did, self.fake_ftset, 1)
        return ns, dbn

    def createNameTag(self, did=None):
        """
        Creates a tag object with the expected namespace and database name.
        """
        ns, dbn = self.getNames(did)
        tag = omero.model.TagAnnotationI()
        tag.setNs(wrap(ns))
        tag.setTextValue(wrap(dbn))
        return tag

    def saveAndLinkTag(self, tag):
        """
        Saves a tag and links it to the current group.
        """
        tag = self.conn.getUpdateService().saveAndReturnObject(tag)
        link = omero.model.ExperimenterGroupAnnotationLinkI()
        link.link(omero.model.ExperimenterGroupI(self.gid, False), tag)
        link = self.conn.getUpdateService().saveAndReturnObject(link)
        return link.getId(), link.getChild().getId()

    def createFileFromNameTag(self, tag):
        """
        Creates an empty file which corresponds to the expected database file.
        """
        p = os.path.join(self.tempdir, unwrap(tag.getTextValue()))
        with open(p, 'w') as f:
            pass
        return p

    def createNonNsTag(self):
        """
        Creates a tag in an unrelated namespace.
        Use this to check only the relevant tags are deleted.
        """
        tag = omero.model.TagAnnotationI()
        tag.setNs(wrap('/other/namespace'))
        tag.setTextValue(wrap('x'))
        return self.saveAndLinkTag(tag)

    def getGroupTags(self):
        """
        Gets a list of all tags linked to a group irrespective of namespace.
        """
        query_string = (
            'select ann from ExperimenterGroupAnnotationLink as gal'
            ' join gal.child as ann'
            ' where gal.parent.id = :gid'
            ' order by ann.id desc')
        params = omero.sys.ParametersI()
        params.addLong('gid', self.gid)
        r = self.conn.getQueryService().findAllByQuery(query_string, params)
        return r

    def countTags(self):
        """
        Counts the number of tags linked to the current group.
        @return total number of tags, number of tags in the non-dataset
        namespace, number of tags in the fake dataset ID namespace
        """
        ns, dbn = self.getNames()
        nsd, dbnd = self.getNames(self.fake_did)
        r = self.getGroupTags()
        tn = 0 if r is None else len(r)
        tns = 0
        tnsd = 0
        for t in r:
            if unwrap(t.getNs()) == ns:
                #print 'ns %s' % unwrap(t.getNs())
                tns += 1
            elif unwrap(t.getNs()) == nsd:
                #print 'nsd %s' % unwrap(t.getNs())
                tnsd += 1
            else:
                #print 'unmatched %s' % unwrap(t.getNs())
                pass

        return (tn, tns, tnsd)

    def createFeatures(self, ioffset = 0, foffset=0.0):
        """
        Creates a set of features and image ID metadata.
        Use ioffset and foffset to create features with different values
        """
        iid = self.createImageWithRes()
        scale = 0.5
        px = 123 + ioffset
        ch = 0 + ioffset
        z = 5 + ioffset
        t = 41 + ioffset
        fids = ['f1', 'f2']
        feats = array([1.0, 2.0]) + foffset

        return iid, scale, px, ch, z, t, fids, feats, self.fake_ftset


    def test_set_contentdb_path(self):
        tempdir = tempfile.mkdtemp(prefix='omero_searcher_content_db-')
        pysliddb.set_contentdb_path(tempdir)
        self.assertEqual(pysliddb.OMERO_CONTENTDB_PATH,
                         os.path.join(tempdir, ''))
        os.rmdir(tempdir)

        nonexistent = os.path.join(tempdir, 'non', 'existent')
        self.assertRaises(Exception, pysliddb.set_contentdb_path, nonexistent)

    def test_initializeNameTag(self):
        g = self.conn.getObject('ExperimenterGroup', self.gid)
        self.assertIsNotNone(g)

        expectedns, expecteddbn = self.getNames()
        r = self.getGroupTags()
        ntags0 = 0 if r is None else len(r)

        # Non-dataset
        ns, dbname = pysliddb.initializeNameTag(self.conn, self.fake_ftset,
                                                did=None)
        self.assertEqual(ns, expectedns)
        self.assertEqual(dbname, expecteddbn)
        # This always throws
        # AttributeError: 'NoneType' object has no attribute 'id'
        #anns = list(g.listAnnotations())

        r = self.getGroupTags()
        ntags1 = len(r)
        self.assertEqual(ntags1, ntags0 + 1)
        self.assertEqual(unwrap(r[0].getNs()), expectedns)
        self.assertEqual(unwrap(r[0].getTextValue()), expecteddbn)

    def test_initializeNameTag_did(self):
        g = self.conn.getObject('ExperimenterGroup', self.gid)
        self.assertIsNotNone(g)

        expectedns, expecteddbn = self.getNames(self.fake_did)
        r = self.getGroupTags()
        ntags0 = 0 if r is None else len(r)

        ns, dbname = pysliddb.initializeNameTag(self.conn, self.fake_ftset,
                                                did=self.fake_did)
        self.assertEqual(ns, expectedns)
        self.assertEqual(dbname, expecteddbn)

        r = self.getGroupTags()
        ntags1 = len(r)
        self.assertEqual(ntags1, ntags0 + 1)
        self.assertEqual(unwrap(r[0].getNs()), expectedns)
        self.assertEqual(unwrap(r[0].getTextValue()), expecteddbn)

    def test_updateNameTag(self):
        tag = omero.model.TagAnnotationI()
        tag.setNs(wrap('foo'))
        tag.setTextValue(wrap('bar'))
        tag = self.conn.getUpdateService().saveAndReturnObject(tag)

        pysliddb.updateNameTag(self.conn, tag, 'baz')
        tag2 = self.conn.getObject('TagAnnotation', unwrap(tag.getId()))._obj
        self.assertEqual(tag2.getNs(), tag.getNs())
        self.assertEqual(unwrap(tag2.getTextValue()), 'baz')

    def test_deleteNameTag(self):
        # Note this will delete pre-existing tags in addition to those
        # created in this method

        ntags0, ntags0ns, ntags0nsd = self.countTags()

        self.saveAndLinkTag(self.createNameTag())
        self.saveAndLinkTag(self.createNameTag())
        self.saveAndLinkTag(self.createNameTag())
        self.saveAndLinkTag(self.createNameTag(self.fake_did))
        self.saveAndLinkTag(self.createNameTag(self.fake_did))

        # This is just a sanity check for the internal test method
        ntags1, ntags1ns, ntags1nsd = self.countTags()
        #print 1, ntags1, ntags1ns, ntags1nsd
        self.assertEqual(ntags1, ntags0 + 5)
        self.assertEqual(ntags1ns, ntags0ns + 3)
        self.assertEqual(ntags1nsd, ntags0nsd + 2)

        # Non-dataset
        pysliddb.deleteNameTag(self.conn, self.fake_ftset, did=None)
        ntags2, ntags2ns, ntags2nsd = self.countTags()
        #print 2, ntags2, ntags2ns, ntags2nsd
        self.assertEqual(ntags2, ntags1 - ntags1ns)
        self.assertEqual(ntags2ns, 0)
        self.assertEqual(ntags2nsd, ntags1nsd)

        # Dataset
        pysliddb.deleteNameTag(self.conn, self.fake_ftset, did=self.fake_did)
        ntags3, ntags3ns, ntags3nsd = self.countTags()
        #print 3, ntags3, ntags3ns, ntags3nsd
        self.assertEqual(ntags3, ntags1 - ntags1ns - ntags1nsd)
        self.assertEqual(ntags3ns, 0)
        self.assertEqual(ntags3nsd, 0)

    def test_getRecentName(self):
        # Non-dataset
        tag1 = self.createNameTag()
        self.saveAndLinkTag(tag1)
        tag2 = self.createNameTag()
        dbn2 = '%d_%s_%s_content_db_%020d.pkl' % (
            self.gid, 'all', self.fake_ftset, 2)
        tag2.setTextValue(wrap(dbn2))
        self.saveAndLinkTag(tag2)

        dbn0, dbn1, r = pysliddb.getRecentName(
            self.conn, self.fake_ftset, did=None)
        self.assertEqual(dbn0, dbn2)

        dbn3 = '%d_%s_%s_content_db_%020d.pkl' % (
            self.gid, 'all', self.fake_ftset, 3)
        self.assertEqual(dbn1, dbn3)

    def test_getRecentName_did(self):
        tag1 = self.createNameTag(did=self.fake_did)
        self.saveAndLinkTag(tag1)
        tag2 = self.createNameTag(did=self.fake_did)
        dbn2 = '%d_%s_%s_content_db_%020d.pkl' % (
            self.gid, str(self.fake_did), self.fake_ftset, 2)
        tag2.setTextValue(wrap(dbn2))
        self.saveAndLinkTag(tag2)

        dbn0, dbn1, r = pysliddb.getRecentName(
            self.conn, self.fake_ftset, did=self.fake_did)
        self.assertEqual(dbn0, dbn2)

        dbn3 = '%d_%s_%s_content_db_%020d.pkl' % (
            self.gid, str(self.fake_did), self.fake_ftset, 3)
        self.assertEqual(dbn1, dbn3)

    def noautorun_has(self):
        # Run by test_has_deleteTableLink()
        a, r = pysliddb.has(self.conn, self.fake_ftset, did=None)
        self.assertFalse(a)
        self.assertIsNone(r)

        tag = self.createNameTag()
        self.saveAndLinkTag(tag)
        self.createFileFromNameTag(tag)

        a, r = pysliddb.has(self.conn, self.fake_ftset, did=None)
        self.assertTrue(a)
        self.assertEqual(os.path.basename(r), unwrap(tag.getTextValue()))
        self.assertTrue(os.path.isfile(r))

        return r

    def noautorun_has_did(self):
        # Run by test_has_deleteTableLink_did()
        a, r = pysliddb.has(self.conn, self.fake_ftset, did=self.fake_did)
        self.assertFalse(a)
        self.assertIsNone(r)

        tag = self.createNameTag(did=self.fake_did)
        self.saveAndLinkTag(tag)
        self.createFileFromNameTag(tag)

        a, r = pysliddb.has(self.conn, self.fake_ftset, did=self.fake_did)
        self.assertTrue(a)
        self.assertEqual(os.path.basename(r), unwrap(tag.getTextValue()))
        self.assertTrue(os.path.isfile(r))

        return r

    def noautorun_deleteTableLink(self, r):
        # Run by test_has_deleteTableLink()
        ntags0, ntags0ns, ntags0nsd = self.countTags()
        a = pysliddb.deleteTableLink(self.conn, self.fake_ftset, did=None)
        self.assertTrue(a)

        ntags1, ntags1ns, ntags1nsd = self.countTags()
        self.assertEqual(ntags1, ntags0 - ntags0ns)
        self.assertEqual(ntags1ns, 0)
        self.assertEqual(ntags1nsd, ntags0nsd)
        self.assertFalse(os.path.exists(r))

    def noautorun_deleteTableLink_did(self, r):
        # Run by test_has_deleteTableLink_did()
        ntags0, ntags0ns, ntags0nsd = self.countTags()
        a = pysliddb.deleteTableLink(
            self.conn, self.fake_ftset, did=self.fake_did)
        self.assertTrue(a)

        ntags1, ntags1ns, ntags1nsd = self.countTags()
        self.assertEqual(ntags1, ntags0 - ntags0nsd)
        self.assertEqual(ntags1ns, ntags0ns)
        self.assertEqual(ntags1nsd, 0)
        self.assertFalse(os.path.exists(r))

    def test_has_deleteTableLink(self):
        r = self.noautorun_has()
        self.noautorun_deleteTableLink(r)

    def test_has_deleteTableLink_did(self):
        r = self.noautorun_has_did()
        self.noautorun_deleteTableLink_did(r)

    def test_createColumns(self):
        feature_ids = ['f1', 'f2']
        cols = pysliddb.createColumns(feature_ids)
        expectednames = ['INDEX', 'server', 'username', 'iid', 'pixels',
                         'channel', 'zslice', 'timepoint',
                         'f1', 'f2']
        self.assertEqual([c.name for c in cols], expectednames)

    def test_initialize(self):
        feature_ids = ['f1', 'f2']

        a = pysliddb.initialize(
            self.conn, feature_ids, self.fake_ftset, did=None)
        self.assertTrue(a)

        expectedns, expecteddbn = self.getNames()
        expectedpath = os.path.join(self.tempdir, expecteddbn)
        a, r = pysliddb.has(self.conn, self.fake_ftset, did=None)
        self.assertTrue(a)
        self.assertEqual(r, expectedpath)

        with open(expectedpath) as f:
            d = pickle.load(f)
        self.assertEqual(d.keys(), ['info'])

    def test_initialize_did(self):
        feature_ids = ['f1', 'f2']

        a = pysliddb.initialize(
            self.conn, feature_ids, self.fake_ftset, did=self.fake_did)
        self.assertTrue(a)

        expectedns, expecteddbn = self.getNames(did=self.fake_did)
        expectedpath = os.path.join(self.tempdir, expecteddbn)
        a, r = pysliddb.has(self.conn, self.fake_ftset, did=self.fake_did)
        self.assertTrue(a)
        self.assertEqual(r, expectedpath)

        with open(expectedpath) as f:
            d = pickle.load(f)
        self.assertEqual(d.keys(), ['info'])


    @unittest.skip('todo (not used?)')
    def test_updatePerDataset(self):
        pysliddb.updatePerDataset(conn, server, username, dataset_id_list, featureset, field=True, did=None)


    def test_update(self):
        iid, scale, px, ch, z, t, fids, feats, fts = self.createFeatures()
        a, m = pysliddb.update(self.conn, 'host', 'user', scale,
                               iid, px, ch, z, t, fids, feats, fts, did=None)
        self.assertTrue(a)
        a, r = pysliddb.has(self.conn, self.fake_ftset, did=None)
        self.assertTrue(a)

        with open(r) as f:
            d = pickle.load(f)
        self.assertEqual(sorted(d.keys()), sorted([0.5, 'info']))
        self.assertEqual(len(d[0.5]), 1)
        d0 = d[0.5][0]
        self.assertEqual(len(d0), 13)
        self.assertEqual(d0[0:3], [1, 'host', 'user'])
        self.assertTrue(d0[3].startswith('host/'))
        self.assertTrue(d0[4].startswith('host/'))
        self.assertTrue(d0[5].startswith('host/'))
        self.assertEqual(d0[6:11], [iid, px, ch, z, t])
        self.assertTrue(all(array(d0[11:]) == feats))

    def test_update_did(self):
        iid, scale, px, ch, z, t, fids, feats, fts = self.createFeatures()
        a, m = pysliddb.update(self.conn, 'host', 'user', scale,
                               iid, px, ch, z, t, fids, feats, fts,
                               did=self.fake_did)
        self.assertTrue(a)
        a, r = pysliddb.has(self.conn, self.fake_ftset, did=self.fake_did)
        self.assertTrue(a)

        with open(r) as f:
            d = pickle.load(f)
        self.assertEqual(sorted(d.keys()), sorted([0.5, 'info']))
        self.assertEqual(len(d[0.5]), 1)
        d0 = d[0.5][0]
        self.assertEqual(len(d0), 13)
        self.assertEqual(d0[0:3], [1, 'host', 'user'])
        self.assertTrue(d0[3].startswith('host/'))
        self.assertTrue(d0[4].startswith('host/'))
        self.assertTrue(d0[5].startswith('host/'))
        self.assertEqual(d0[6:11], [iid, px, ch, z, t])
        self.assertTrue(all(array(d0[11:]) == feats))

    def test_updateDataset(self):
        iid, scale, px, ch, z, t, fids, feats, fts = zip(
            self.createFeatures(0, 0.0), self.createFeatures(1, 1.0))
        scale = scale[0]
        fids = fids[0]
        fts = fts[0]

        a, m = pysliddb.updateDataset(self.conn, 'host', 'user', scale,
                             iid, px, ch, z, t, fids, feats, fts, did=None)
        self.assertTrue(a)
        a, r = pysliddb.has(self.conn, self.fake_ftset, did=None)
        self.assertTrue(a)

        with open(r) as f:
            d = pickle.load(f)
        self.assertEqual(sorted(d.keys()), sorted([0.5, 'info']))
        self.assertEqual(len(d[0.5]), 2)
        d0 = d[0.5][0]
        self.assertEqual(len(d0), 13)
        self.assertEqual(d0[0:3], [1, 'host', 'user'])
        self.assertTrue(d0[3].startswith('host/'))
        self.assertTrue(d0[4].startswith('host/'))
        self.assertTrue(d0[5].startswith('host/'))
        self.assertEqual(d0[6:11], [iid[0], px[0], ch[0], z[0], t[0]])
        self.assertTrue(all(array(d0[11:]) == feats[0]))

        d1 = d[0.5][1]
        self.assertEqual(len(d1), 13)
        self.assertEqual(d1[0:3], [2, 'host', 'user'])
        self.assertTrue(d1[3].startswith('host/'))
        self.assertTrue(d1[4].startswith('host/'))
        self.assertTrue(d1[5].startswith('host/'))
        self.assertEqual(d1[6:11], [iid[1], px[1], ch[1], z[1], t[1]])
        self.assertTrue(all(array(d1[11:]) == feats[1]))

    def test_updateDataset_did(self):
        iid, scale, px, ch, z, t, fids, feats, fts = zip(
            self.createFeatures(0, 0.0), self.createFeatures(1, 1.0))
        scale = scale[0]
        fids = fids[0]
        fts = fts[0]

        a, m = pysliddb.updateDataset(self.conn, 'host', 'user', scale,
                             iid, px, ch, z, t, fids, feats, fts,
                                      did=self.fake_did)
        self.assertTrue(a)
        a, r = pysliddb.has(self.conn, self.fake_ftset, did=self.fake_did)
        self.assertTrue(a)

        with open(r) as f:
            d = pickle.load(f)
        self.assertEqual(sorted(d.keys()), sorted([0.5, 'info']))
        self.assertEqual(len(d[0.5]), 2)
        d0 = d[0.5][0]
        self.assertEqual(len(d0), 13)
        self.assertEqual(d0[0:3], [1, 'host', 'user'])
        self.assertTrue(d0[3].startswith('host/'))
        self.assertTrue(d0[4].startswith('host/'))
        self.assertTrue(d0[5].startswith('host/'))
        self.assertEqual(d0[6:11], [iid[0], px[0], ch[0], z[0], t[0]])
        self.assertTrue(all(array(d0[11:]) == feats[0]))

        d1 = d[0.5][1]
        self.assertEqual(len(d1), 13)
        self.assertEqual(d1[0:3], [2, 'host', 'user'])
        self.assertTrue(d1[3].startswith('host/'))
        self.assertTrue(d1[4].startswith('host/'))
        self.assertTrue(d1[5].startswith('host/'))
        self.assertEqual(d1[6:11], [iid[1], px[1], ch[1], z[1], t[1]])
        self.assertTrue(all(array(d1[11:]) == feats[1]))

    def test_chunks(self):
        l = range(5)
        n = 2
        x = pysliddb.chunks(l, n)
        self.assertEqual(x, [[0, 1], [2, 3], [4]])

    def test_retrieve(self):
        tag = self.createNameTag()
        self.saveAndLinkTag(tag)
        p = self.createFileFromNameTag(tag)
        with open(p, 'w') as f:
            pickle.dump([1, 2, 3], f)

        d, m = pysliddb.retrieve(self.conn, self.fake_ftset, did=None)
        self.assertEqual(d, [1, 2, 3])

    def test_retrieve_did(self):
        tag = self.createNameTag(did=self.fake_did)
        self.saveAndLinkTag(tag)
        p = self.createFileFromNameTag(tag)
        with open(p, 'w') as f:
            pickle.dump([4, 5, 6], f)

        d, m = pysliddb.retrieve(self.conn, self.fake_ftset, did=self.fake_did)
        self.assertEqual(d, [4, 5, 6])


    @unittest.skip('todo')
    def test_retrieveRemote(self):
        pysliddb.retrieveRemote(conn_local, conn_remote, featureset, did=None)


    def test_processOMEIDs(self):
        cr = [1, 'host', 'user', 'metadata_url', 'img_url', 'render_url',
              1, 2, 3, 4, 5,
              5.1, 5.2]
        self.assertEqual(pysliddb.processOMEIDs(cr),
                         ['1.2.3.4.5', 'user', 'host'])

    def test_processOMESearchSet(self):
        scale = 0.5
        cdb = {}
        cdb[scale] = [
            [
                1, 'host', 'user', 'metadata_url', 'img_url', 'render_url',
                1, 0, 0, 0, 0,
                5.1, 5.2,
                ],
            [
                2, 'host', 'user', 'metadata_url', 'img_url', 'render_url',
                2, 0, 0, 0, 0,
                1.0, 1.0,
                ],
            ]
        im_ref_dict = {
            '2.0.0.0.0': [(scale, ''), 1],
            }

        r = pysliddb.processOMESearchSet(cdb, im_ref_dict, scale)
        self.assertEqual(len(r), 1)
        self.assertEqual(r[0], ['2.0.0.0.0', 1, [1.0, 1.0]])


    def test_removeDuplicates(self):
        iid, scale, px, ch, z, t, fids, feats, fts = zip(
            self.createFeatures(0, 0.0),
            self.createFeatures(1, 1.0),
            self.createFeatures(0, 2.0))
        iid = (iid[0], iid[1], iid[0])
        scale = scale[0]
        fids = fids[0]
        fts = fts[0]

        a, m = pysliddb.updateDataset(self.conn, 'host', 'user', scale,
                             iid, px, ch, z, t, fids, feats, fts, did=None)
        self.assertTrue(a)
        a, r = pysliddb.has(self.conn, self.fake_ftset, did=None)
        self.assertTrue(a)

        with open(r) as f:
            d = pickle.load(f)
        self.assertEqual(sorted(d.keys()), sorted([0.5, 'info']))
        self.assertEqual(len(d[0.5]), 3)

        d0 = d[0.5][0]
        self.assertEqual(len(d0), 13)
        self.assertEqual(d0[0:3], [1, 'host', 'user'])
        self.assertTrue(d0[3].startswith('host/'))
        self.assertTrue(d0[4].startswith('host/'))
        self.assertTrue(d0[5].startswith('host/'))
        self.assertEqual(d0[6:11], [iid[0], px[0], ch[0], z[0], t[0]])
        self.assertTrue(all(array(d0[11:]) == feats[0]))

        d1 = d[0.5][1]
        self.assertEqual(len(d1), 13)
        self.assertEqual(d1[0:3], [2, 'host', 'user'])
        self.assertTrue(d1[3].startswith('host/'))
        self.assertTrue(d1[4].startswith('host/'))
        self.assertTrue(d1[5].startswith('host/'))
        self.assertEqual(d1[6:11], [iid[1], px[1], ch[1], z[1], t[1]])
        self.assertTrue(all(array(d1[11:]) == feats[1]))

        d2 = d[0.5][2]
        self.assertEqual(len(d2), 13)
        self.assertEqual(d2[0:3], [3, 'host', 'user'])
        self.assertTrue(d2[3].startswith('host/'))
        self.assertTrue(d2[4].startswith('host/'))
        self.assertTrue(d2[5].startswith('host/'))
        self.assertEqual(d2[6:11], [iid[2], px[2], ch[2], z[2], t[2]])
        self.assertTrue(all(array(d2[11:]) == feats[2]))

        a, r = pysliddb.removeDuplicates(self.conn, scale, fts, did=None)
        self.assertTrue(a)
        a, r = pysliddb.has(self.conn, self.fake_ftset, did=None)
        self.assertTrue(a)

        with open(r) as f:
            d = pickle.load(f)
        self.assertEqual(sorted(d.keys()), sorted([0.5, 'info']))
        self.assertEqual(len(d[0.5]), 2)

        d0 = d[0.5][0]
        d1 = d[0.5][1]

        self.assertEqual(len(d0), 13)
        self.assertEqual(d0[0:3], [1, 'host', 'user'])
        self.assertTrue(d0[3].startswith('host/'))
        self.assertTrue(d0[4].startswith('host/'))
        self.assertTrue(d0[5].startswith('host/'))

        self.assertEqual(len(d1), 13)
        self.assertEqual(d1[0:3], [2, 'host', 'user'])
        self.assertTrue(d1[3].startswith('host/'))
        self.assertTrue(d1[4].startswith('host/'))
        self.assertTrue(d1[5].startswith('host/'))

        # Remember, ordering is not preserved
        if d0[6] > d1[6]:
            d1, d0 = d0, d1

        self.assertEqual(d0[6:11], [iid[2], px[2], ch[2], z[2], t[2]])
        self.assertTrue(all(array(d0[11:]) == feats[2]))

        self.assertEqual(d1[6:11], [iid[1], px[1], ch[1], z[1], t[1]])
        self.assertTrue(all(array(d1[11:]) == feats[1]))





if __name__ == '__main__':
    unittest.main()
