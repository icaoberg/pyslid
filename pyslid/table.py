'''
Authors: Ivan E. Cao-Berg (icaoberg@scs.cmu.edu)
Created: April 26, 2012

Copyright (C) 2012 Murphy Lab
Lane Center for Computational Biology
School of Computer Science
Carnegie Mellon University

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published
by the Free Software Foundation; either version 2 of the License,
or (at your option) any later version.

This program is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
02110-1301, USA.

For additional information visit http://murphylab.web.cmu.edu or
send email to murphy@cmu.edu
'''

import omero, pyslic
from utilities import PyslidException
import omero.util.script_utils as utils
from omero.rtypes import *
from omero.gateway import BlitzGateway

def getInfo(conn, did, set="slf33", field=True, debug=False ):
    '''
    Returns the number of images in the dataset and the number of images that has the OMERO.tables attached.

    If the method is unable to connect to the OMERO.server, then the method will return None.
    If the method doesn't find an image associated with the given image id (iid), then the
    method will return None.

    For detailed outputs, set debug flag to True.

    @param connection (conn)
    @param dataset id (did)
    @param feature set name (set)
    @param field true if field features, false otherwise
    @return num_image number of images
    @return num_image_table (number of image that has a attached table)
    '''
    
    if not conn.isConnected():
        raise PyslidException("Unable to connect to OMERO.server")

    if not pyslid.utilities.hasDataset( conn, did ):
        raise PyslidException("No dataset found with the given dataset id")

    if not isinstance( field, bool ):
        raise PyslidException("Input parameter field must be a boolean")

    ds = conn.getObject("Dataset", long(did))
    img_gen = ds.getChildLinks()
    num_image = 0
    num_image_table = 0
    for im in img_gen:
        num_image +=1
        iid = long(im.getId())
        answer, result = has(conn, iid, set, field)
        if answer:
            num_image_table +=1

    return [num_image, num_image_table]

def getFileID( conn, iid, set, field=True, debug=False ):
    '''
    Returns the file id (fid) of an attached feature table given an image id (iid) and a setname.
    @param connection (conn)
    @param image id (iid)
    @param set
    @param field
    @return file id (fid)
    '''
    #check input parameters
    if not conn.isConnected():
        raise PyslidException("Unable to connect to OMERO.server")

    if not hasImage( conn, iid ):
        raise PyslidException("Image not found")
        
    if not isinstance( set, str ):
        raise PyslidException("Parameter set should be a string")
        
    if not isinstance( field, bool ):
        raise PyslidException("Parameter field should be a bool")

    #create query service
    query = conn.getQueryService()

    #create and populate parameter
    if field == True:
       filename = 'iid-' + str(iid) + '_feature-' + set + '_field.h5';
    else:
       filename = 'iid-' + str(iid) + '_feature-' + set + '_roi.h5';
    #create and populate parameter
    params = omero.sys.ParametersI()
    params.addLong( 'iid', iid );
    params.addString( 'filename', filename );
    #hql string query
    string = "select iml from ImageAnnotationLink as iml join fetch iml.child as fileAnn join fetch fileAnn.file join iml.parent as img where img.id = :iid and fileAnn.file.name = :filename"
  
    try:
       #database query
       result = query.projection( string, params )
   
       #get answer
       fid = result.pop().pop()._val._child._file._id._val
    except:
        raise PyslidException("Unable to retrieve query")
   
    return fid
 
