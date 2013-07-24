'''
Authors: Ivan E. Cao-Berg (icaoberg@scs.cmu.edu)
Created: May 1, 2011
Last Update: May 16, 2011

Copyright (C) 2011 Murphy Lab
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
import omero.util.script_utils as utils
from omero.rtypes import *
from omero.gateway import BlitzGateway


class PyslidException(Exception):
    pass

def connect( server, port, username, password ): 
    '''
    Helper method that connects to an OMERO.searcher server.
    @param server
    @param port
    @param username
    @param password
    @returns connection
    '''
    
    try:
        conn = BlitzGateway( username, password, host=server, port=int(port))
        conn.connect()
        return conn
    except:
        return None

def getDataset( conn, did ):
    '''
    Returns a dataset with the given dataset id (did).
    @param connection (conn)
    @param dataset id (did)
    @return dataset
    '''
    
    try:
        dataset = conn.getObject("Dataset", long(did))
    except:
        dataset = []
	
    return dataset	
	
def getScreen( conn, sid ):
    '''
    Returns a screen with the given screen id (sid).
    @param connection (conn)
    @param screen id (sid)
    @return screen
    '''
    
    if not conn.isConnected():
        return None

    try:
        screen = conn.getObject("Screen", long(sid))
    except:
        screen = None
	
    return screen
	
def getPlate( conn, plid ):
    '''
    Returns a plate with the given plate id (plid).
    @param connection (conn)
    @param plate id (plid)
    @return plate
    '''
    
    if not conn.isConnected():
        return None

    try:
        plate = conn.getObject("Plate", long(plid))
    except:
        plate = None

    return plate
    
def getFileID( conn, iid, set, field=True ):
    '''
    Returns the file id (fid) of an attached feature table 
    given an image id (iid) and a setname.

    (DEPRECATED) This method has been replaced by table.getFileID

    @param connection (conn)
    @param image id (iid)
    @param set
    @param field
    @return file id (fid)
    '''

    #check input parameters
    if not hasImage( conn, iid ):
        return None
        
    if not isinstance( set, str ):
        return None
        
    if not isinstance( field, bool ):
        return None

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
       result = query.projection(string, params, conn.SERVICE_OPTS)
   
       #get answer
       fid = result.pop().pop()._val._child._file._id._val
    except:
       fid = None
   
    return fid
   
def getImage( conn, iid ):
    '''
    Returns an image with the given image id (iid).
    @param connection (conn)
    @param image id (iid)
    @return image
    '''

    if not conn.isConnected():
       return None    

    try:
        image = conn.getObject( "Image", long(iid) )
    except:
        image = None
		
    return image 
        
def getPlane( conn, iid, pixels=0, channel=0, zslice=0, timepoint=0 ):
    '''
    Returns a plane with the given image id (iid) as well as pixels, channels, zslice and timepoint index.
    @param connection (conn)
    @param image id (iid)
    @param pixels index
    @param channel index
    @param zslice index
    @param timepoint index
    @return plane
    '''
	
    if not conn.isConnected():
        return None

    if not hasImage( conn, iid ):
        return None
	
    #create pixel service (needed to extract pixels from image object)
    rawPixelsStore = conn.createRawPixelsStore()
    
    #get image
    image = conn.getObject( "Image", long(iid) )
    
    #get plane id from image (we use zero because our images have only 
    #one pixel object per image object
    pid = image.getPixelsId();
    
    #retrieve pixel object
    pixels = conn.getPixelsService().retrievePixDescription(pid);
    
    #update pixel service to match the current pixel object
    rawPixelsStore.setPixelsId( pid, True )
    
    try:
        #extract pixel object
        plane = utils.downloadPlane( rawPixelsStore, pixels, zslice, channel, timepoint );
    except:
        plane = None   

    #close services
    rawPixelsStore.close()
    
    #return plane
    return plane

def getProject( conn, prid ):
    '''
    Returns a project with the given project id (prid).
    @param connection (conn)
    @param project id (prid)
    @return project
    '''

    if not conn.isConnected():
        return None    

    try:
        project = conn.getObject( "Project", long(prid) )
    except:
        project = []
	
    return project
    
def hasDataset( conn, did ):
    '''
    Determines if there is a dataset in the OMERO database with the given dataset id (did).
    @params connection (conn)
    @params dataset id (did)
    @return true if dataset exists, false otherwise
    '''

    if not conn.isConnected():
        return False

    if not conn.getObject( "Dataset", long(did) ):
        return False
    else:
        return True
    
def hasFile( conn, fid ):
    """
    Determines if there is a file annotation with file id (fid).
    @params connection (conn) 
    @params file id (fid)
    @return true if there is a file annotation with file id (fid), false otherwise
    """
    
    #create query service
    query = conn.getQueryService()
    
    #create and populate parameter
    params = omero.sys.ParametersI()
    params.addLong( "fid", fid );
    
    #hql string query
    string = "select count(*) from OriginalFile f where f.id = :fid";
    
    #database query
    result = query.projection(string, params, conn.SERVICE_OPTS)
    
    #get answer
    answer = result.pop().pop()._val
    
    if answer == 0:
        return False
    else:
        return True
    
def hasImage( conn, iid ):
    '''
    Determines if there is an image in the OMERO database with the given
    image id (iid).
    @params connection (conn)
    @params image id (iid)
    @return true if image exists, false otherwise
    '''

    if not conn.isConnected():
        return False
    
    if not conn.getObject( "Image", long(iid) ):
        return False
    else:
        return True
		
def hasPlate( conn, pid ):
    '''
    Determines if there is an image in the OMERO database with the given
    plate id (pid).
    @params conn
    @params plate id (pid)
    @return true if plate exists, false otherwise
    '''

    if not conn.isConnected():
        return False
    
    if not conn.getObject( "Plate", long(pid) ):
        return False
    else:
        return True
    
def hasPlane( conn, plid ):
    '''
    Determines if there is a plane in the OMERO database with the given
    plane id (pid).
    @params conn
    @params plane id (plid)
    @return true if plane exists, false otherwise
    '''

    if not conn.isConnected():
        return False    

    #create query service
    query = conn.getQueryService()
    
    #create and populate parameter
    params = omero.sys.ParametersI()
    params.addLong( "plid", plid );
    
    #hql string query
    string = "select count(*) from Plane p where p.id = :plid";
    
    #database query
    result = query.projection(string, params, conn.SERVICE_OPTS)
    
    #get answer
    answer = result.pop().pop()._val
    
    if answer == 0:
        return False
    else:
        return True
    
def hasProject( conn, prid ):
    '''
    Determines if there is a project in the OMERO database with the given
    project id (prid).
    @params session
    @params project id (prid)
    @return true if project exists, false otherwise
    '''

    if not conn.isConnected():
        return False
	
    if not conn.getObject( "Project", long(prid) ):
        return False
    else:
        return True
    
def hasScreen( conn, sid ):
    '''
    Determines if there is a project in the OMERO database with the given
    screen id (sid).
    @params conn
    @params screen id (sid)
    @return true if screen exists, false otherwise
    '''

    if not conn.isConnected():
        return False
	
    if not conn.getObject( "Scree", long(sid) ):
        return False
    else:
        return True
	
def createDataset( conn, name ):
    '''
    Create a dataset with the given name and returns the dataset id for that dataset.
    @param session
    @param name 
    @return dataset id (did)
    '''

    dataset = omero.model.DatasetI()
    dataset.name = omero.rtypes.rstring( name )

    try:
        dataset = conn.getUpdateService().saveAndReturnObject(dataset)
        did = dataset.id.val
    except:
        did = None
    
    return did

def addImage2Dataset( conn, iid, did ):


    '''
    Add an existing image to an existing dataset
    @param connection (conn)
    @param image id (iid)
    @param dataset id (did)
    @return true if image is added, false otherwise
    '''
    
    if not hasImage( conn, iid ):
        return False

    if not hasDataset( conn, did ):
        return False    

    link = omero.model.DatasetImageLinkI()
    link.parent = omero.model.DatasetI(did, False)
    link.child = omero.model.ImageI(iid, False)
 
    try:
       conn.getUpdateService().saveAndReturnObject(link)
       return True
    except:
       return False
	   
def getListOfImages( conn, did ):
    '''
    Returns a list of image ids for a given dataset id (did).
    @param connection (conn)
    @param dataset id (did)
    @return list of image ids
    '''
	
    if not conn.isConnected():
        return None
	   
    if not hasDataset( conn, did ):
        return None
		
    try:
        dataset = conn.getObject("Dataset", long(did))
        links = dataset.getChildLinks()
	iids = []
        for image in links:
            iids.append(long(image.getId()))
     
        return iids
    except:
        return None 
