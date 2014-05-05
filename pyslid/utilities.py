'''
Authors: Jennifer Bakal and Ivan E. Cao-Berg
Created: May 1, 2011

Copyright (C) 2011-2014 Murphy Lab
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
from os.path import isfile

class PyslidException(Exception):
    pass

def connect( server, port, username, password ): 
    '''
    Helper method that connects to an OMERO.searcher server.

    :param server: server name
    :type server: string
    :param port: port
    :type port: long
    :param user: username
    :type user: string
    :param password: password
    :type password: string
    :rtype: BlitzGateway connection
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

    :param conn: connection
    :type conn: BlitzGateway connection
    :param did: dataset id
    :type did: long
    :rtype: dataset object
    '''
    
    if not conn.isConnected():
        raise PyslidException("Unable to connect to OMERO.server")

    try:
        dataset = conn.getObject("Dataset", long(did))
    except:
        raise PyslidException("Unable to retrieve dataset")
	
    return dataset	
	
def getScreen( conn, sid ):
    '''
    Returns a screen with the given screen id (sid).

    :param conn: connection
    :type conn: BlitzGateway connection
    :param sid: screen id
    :type sid: long
    :rtype: screen object
    '''
    
    if not conn.isConnected():
        raise PyslidException("Unable to connect to OMERO.server")

    try:
        screen = conn.getObject("Screen", long(sid))
    except:
        raise PyslidException("Unable to retrieve screen")
	
    return screen
	
def getPlate( conn, plid ):
    '''
    Returns a plate with the given plate id (plid).

    :param conn: connection
    :type conn: BlitzGateway connection
    :param plid: plate id
    :type sid: long
    :rtype: plate object
    '''
    
    if not conn.isConnected():
        raise PyslidException("Unable to connect to OMERO.server")

    try:
        plate = conn.getObject("Plate", long(plid))
    except:
        raise PyslidException("Unable to retrieve plate")

    return plate
    
def getFileID( conn, iid, set, field=True ):
    '''
    Returns the file id (fid) of an attached feature table 
    given an image id (iid) and a setname.

    (DEPRECATED) This method has been replaced by table.getFileID

    :param conn: connection
    :type conn: BlitzGateway connection
    :param iid: image id
    :type iid: long
    :param set: feature set name
    :type set: string
    :param field: true if field features, false otherwise
    :type field: boolean
    :rtype: file id
    '''

    if not conn.isConnected(): 
        raise PyslidException( "Unable to connect to OMERO.server" )

    if not hasImage( conn, iid ):
        raise PyslidException( "Unable to find image with image id:" + str(iid) )
        
    if not isinstance( set, str ):
        raise PyslidException( "Input argument feature set name must be a string" )
        
    if not isinstance( field, bool ):
        raise PyslidException( "Input argument field must be boolean" )

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

    :param conn: connection
    :type conn: BlitzGateway connection
    :param iid: image id
    :type iid: long
    :rtype: image object
    '''

    if not conn.isConnected(): 
        raise PyslidException( "Unable to connect to OMERO.server" )   

    if not hasImage( conn, iid ):
        raise PyslidException( "Unable to find image with image id:" + str(iid) )

    try:
        image = conn.getObject( "Image", long(iid) )
    except:
        raise PyslidException( "Unable to retrive image with image id:" + str(iid) )
		
    return image 
        
def getPlane( conn, iid, pixels=0, channel=0, zslice=0, timepoint=0 ):
    '''
    Returns a plane with the given image id (iid) as well as pixels, channels, zslice and timepoint index.

    :param conn: connection
    :type conn: BlitzGateway connection
    :param iid: image id
    :type iid: long
    :param pixels: pixel index
    :type pixels: integer
    :param channel: channel index
    :type channel: integer
    :param zslice: zslice index
    :type zslice: integer
    :param timepoint: timepoint index
    :type timepoint: integer
    :rtype: plane
    '''
	
    if not conn.isConnected(): 
        raise PyslidException( "Unable to connect to OMERO.server" )   

    if not hasImage( conn, iid ):
        raise PyslidException( "Unable to find image with image id:" + str(iid) )
	
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

    :param conn: connection
    :type conn: BlitzGateway connection
    :param prid: project id
    :type prid: long
    :rtype: project object
    '''

    if not conn.isConnected(): 
        raise PyslidException( "Unable to connect to OMERO.server" )   

    try:
        project = conn.getObject( "Project", long(prid) )
    except:   
        project = []
	
    return project
    
def hasDataset( conn, did ):
    '''
    Determines if there is a dataset in the OMERO database with the given dataset id (did).
    
    :param conn: connection
    :type conn: BlitzGateway connection
    :param did: dataset id
    :type did: long
    :rtype: true if dataset exists, false otherwise
    '''

    if not conn.isConnected(): 
        raise PyslidException( "Unable to connect to OMERO.server" )   

    if not conn.getObject( "Dataset", long(did) ):
        return False
    else:
        return True
    
def hasFile( conn, fid ):
    '''
    Determines if there is a file annotation with file id (fid).

    :param conn: connection
    :type conn: BlitzGateway connection
    :param fid: file id
    :type fid: long
    :rtype: true if file exists, false otherwise
    '''
    
    if not conn.isConnected(): 
        raise PyslidException( "Unable to connect to OMERO.server" )   

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
    Determines if there is an image in the OMERO database with the given image id (iid).

    :param conn: connection
    :type conn: BlitzGateway connection
    :param plid: plane id
    :type plid: long
    :rtype: true if plane exists, false otherwise
    '''

    if not conn.isConnected(): 
        raise PyslidException( "Unable to connect to OMERO.server" )   
    
    if not conn.getObject( "Image", long(iid) ):
        return False
    else:
        return True
		
def hasPlate( conn, pid ):
    '''
    Determines if there is an image in the OMERO database with the given plate id (pid).

    :param conn: connection
    :type conn: BlitzGateway connection
    :param pid: plate id
    :type pid: long
    :rtype: true if plate exists, false otherwise
    '''

    if not conn.isConnected(): 
        raise PyslidException( "Unable to connect to OMERO.server" )   
    
    if not conn.getObject( "Plate", long(pid) ):
        return False
    else:
        return True
    
def hasPlane( conn, plid ):
    '''
    Determines if there is a plane in the OMERO database with the given plane id (pid).

    :param conn: connection
    :type conn: BlitzGateway connection
    :param plid: plane id
    :type plid: long
    :rtype: true if plane exists, false otherwise
    '''

    if not conn.isConnected(): 
        raise PyslidException( "Unable to connect to OMERO.server" )       

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
    Determines if there is a project in the OMERO database with the given project id (prid).

    :param conn: connection
    :type conn: BlitzGateway connection
    :param prid: project id
    :type prid: long
    :rtype: true if project exists, false otherwise
    '''

    if not conn.isConnected(): 
        raise PyslidException( "Unable to connect to OMERO.server" )   
	
    if not conn.getObject( "Project", long(prid) ):
        return False
    else:
        return True
    
def hasScreen( conn, sid ):
    '''
    Determines if there is a project in the OMERO database with the given screen id (sid).

    :param conn: connection
    :type conn: BlitzGateway connection
    :param sid: screen id
    :type sid: long
    :rtype: true if screen exists, false otherwise
    '''

    if not conn.isConnected(): 
        raise PyslidException( "Unable to connect to OMERO.server" )   
	
    if not conn.getObject( "Screen", long(sid) ):
        return False
    else:
        return True
	
def createDataset( conn, name, force=False ):
    '''
    Create a dataset with the given name and returns the dataset id for that dataset.

    :param conn: connection
    :type conn: BlitzGateway connection
    :param name: dataset name
    :type name: string
    :rtype: dataset id (did) for the new dataset
    '''

    if not conn.isConnected(): 
        raise PyslidException( "Unable to connect to OMERO.server" )

    dataset = omero.model.DatasetI()
    dataset.name = omero.rtypes.rstring( name )

    try:
        dataset = conn.getUpdateService().saveAndReturnObject( dataset )
        did = dataset.id.val
    except:
        raise PyslidException( "Unable to create dataset" )
        did = None
    
    return did

def createProject( conn, name ):
    '''
    Create a project with the given name and returns the project id for that project.

    :param conn: connection
    :type conn: BlitzGateway connection
    :param name: project name
    :type name: string
    :rtype: project id (prid) for the new dataset
    '''

    if not conn.isConnected(): 
        raise PyslidException( "Unable to connect to OMERO.server" )   

    project = omero.model.ProjectI()
    project.name = omero.rtypes.rstring( name )

    try:
        project = conn.getUpdateService().saveAndReturnObject( project )
        prid = project.id.val
    except:
        raise PyslidException( "Unable to create project" )
        prid = None
    
    return prid

def addImage2Dataset( conn, iid, did ):
    '''
    Add an existing image to an existing dataset.

    :param conn: connection
    :type conn: BlitzGateway connection
    :param iid: image id
    :type iid: long
    :param did: dataset id
    :type did: long
    :rtype: true if successfully added image to dataset, false otherwise
    '''

    #@icaoberg
    #technically, all i am doing is linking one object to the other

    answer = False
    if not conn.isConnected(): 
        raise PyslidException( "Unable to connect to OMERO.server" )   

    if not hasImage( conn, iid ):
        raise PyslidException( "Unable to find image with image id:" + str(iid) )

    if not hasDataset( conn, did ):
        raise PyslidException( "Unable to find dataset with dataset id:" + str(did) ) 

    link = omero.model.DatasetImageLinkI()
    link.parent = omero.model.DatasetI(did, False)
    link.child = omero.model.ImageI(iid, False)
 
    try:
        conn.getUpdateService().saveAndReturnObject(link)
        answer = True
        return answer
    except:
        raise PyslidException( "Unable to link image " + str(iid) + " to dataset " + str(did) )
        return answer

def addDataset2Project( conn, did, prid ):
    '''
    Add an existing dataset to an existing project.

    :param conn: connection
    :type conn: BlitzGateway connection
    :param did: dataset id
    :type did: long
    :param prid: project id
    :type prid: long
    :rtype: true if successfully added dataset to project, false otherwise
    '''
    
    #@icaoberg
    #technically, all i am doing is linking one object to the other

    answer = False
    if not conn.isConnected(): 
        raise PyslidException( "Unable to connect to OMERO.server" )   

    if not hasDataset( conn, did ):
        raise PyslidException( "Unable to find dataset with dataset id:" + str(did) )

    if not hasProject( conn, prid ):
        raise PyslidException( "Unable to find project with project id:" + str(prid) ) 

    link = omero.model.ProjectDatasetLinkI()
    link.parent = omero.model.ProjectI(prid, False)
    link.child = omero.model.DatasetI(did, False)
 
    try:
        conn.getUpdateService().saveAndReturnObject(link)
        answer = True
        return answer
    except:
        raise PyslidException( "Unable to link dataset " + str(did) + " to project " + str(prid) )
        return answer
	   
def get_list_of_images( conn, did ):
    '''
    Returns the list of image ids (iids) from a given dataset id (did).

    :param conn: connection
    :type conn: BlitzGateway connection
    :param did: dataset id
    :type did: long
    :rtype: list of image ids
    '''
	
    if not conn.isConnected(): 
        raise PyslidException( "Unable to connect to OMERO.server" )   
	   
    if not hasDataset( conn, did ):
        raise PyslidException( "Unable to find dataset with dataset id:" + str(did) )
		
    try:
        dataset = conn.getObject("Dataset", long(did))
        links = dataset.getChildLinks()
        iids = []
        for image in links:
            iids.append(long(image.getId()))
     
        return iids
    except:
        raise PyslidException( "Unable to retrieve list of image from dataset with dataset id:" + str(did) )
        return None 

def get_list_of_projects( conn ):
    '''
    Returns the list of project ids (prids) associated with the current user.

    :param conn: connection
    :type conn: BlitzGateway connection
    :param prid: project id
    :type prid: long
    :rtype: list of project ids and names
    '''
    
    if not conn.isConnected(): 
        raise PyslidException( "Unable to connect to OMERO.server" )   
        
    try:
        names = []
        prids = []
        # connect as above
        for project in conn.listProjects():
            names.append(project.getName())
            prids.append(project.getId())

        return [prids, names]

    except:
        names = []
        prids = []
        raise PyslidException( "Unable to retrieve list of projects" )
        return [prids, names] 

def get_list_of_datasets( conn ):
    '''
    Returns the list of dataset ids (dids) associated with the current user.

    :param conn: connection
    :type conn: BlitzGateway connection
    :rtype: list of dataset ids and names
    '''
    
    if not conn.isConnected(): 
        raise PyslidException( "Unable to connect to OMERO.server" )   
        
    try:
        names = []
        dids = []
        # connect as above
        for project in conn.listProjects():
            for dataset in project.listChildren():
                names.append(dataset.getName())
                dids.append(dataset.getId())

        return [dids, names]
    except:
        names = []
        dids = []
        raise PyslidException( "Unable to retrieve list of datasets" )
        return [dids, names] 

def get_list_of_all_images( conn ):
    '''
    Returns the list of all images ids (iids) associated with the current user.

    :param conn: connection
    :type conn: BlitzGateway connection
    :rtype: list of images ids
    '''
    
    if not conn.isConnected(): 
        raise PyslidException( "Unable to connect to OMERO.server" )   
        
    try:
        iids = []
        # connect as above
        for project in conn.listProjects():
            for dataset in project.listChildren():
                links = dataset.getChildLinks()
                for image in links:
                    iids.append(long(image.getId()))
                     
        return iids
    except:
        idds = []
        raise PyslidException( "Unable to retrieve list of images" )
        return iids

def has_dataset_with_name( conn, name ):
    '''
    Determines if there is a dataset in the OMERO database with the 
    given name.
    
    :param conn: connection
    :type conn: BlitzGateway connection
    :param name: dataset name
    :type name: string
    :rtype: true if dataset exists, false otherwise
    '''

    if not conn.isConnected(): 
        raise PyslidException( "Unable to connect to OMERO.server" )   

    try:
        if not conn.getObject( "Dataset", attributes={'name': name } ):
            return False
        else:
            return True
    except:
        print "Found more than one dataset with the matching name"
        return True

def has_project_with_name( conn, name ):
    '''
    Determines if there is a project in the OMERO database with the 
    given name.
    
    :param conn: connection
    :type conn: BlitzGateway connection
    :param name: project name
    :type name: string
    :rtype: true if project exists, false otherwise
    '''

    if not conn.isConnected(): 
        raise PyslidException( "Unable to connect to OMERO.server" )   

    try:
        if not conn.getObject( "Project", attributes={'name': name } ):
            return False
        else:
            return True
    except:
        print "Found more than one project with the matching name"
        return True

def link_file_to_image(conn, iid, filename, namespace=None, description=None, debug=False):
    '''
    Links local file to image.

    :param conn: connection
    :type conn: BlitzGateway connection
    :param iid: image id
    :type iid: long
    :param filename: 
    :type filename: string
    :param debug: debug flag
    :type debug: boolean
    :rtype: true if feature if it successfully added feature vector to feature table, false otherwise
    '''
    
    #checking connection to omero.server
    if debug:
        print "Checking connection to OMERO.server."
    answer = False
    if not conn.isConnected():
        print "Unable to connect to OMERO.server"
        return answer

    # checking if image exist
    if debug:
        print "Checking if image " + str(iid) + " exists."
    if not hasImage( conn, iid ):
        raise PyslidException("No image found with the given image id:%s", iid)
        return answer
    
    print "Image found. Attempting to retrieve image."
    image = conn.getObject( "Image", long(iid) )
    if image is None:
        raise PyslidException("Unable to retrieve image with id:%s", iid)
        return answer

    #check filename
    if debug:
        print "Checking if file " + filename + " exists on local disk."
    if not isfile(filename):
        raise PyslidException("File " +  filename + " not found on disk")
        return answer

    file_annotation = conn.createFileAnnfromLocalFile(filename, ns=namespace, desc=description)

    if debug:
        print "Attaching FileAnnotation to Dataset: ", "File ID:", fileAnn.getId(), ",", file_annotation.getFile().getName(), "Size:", file_annotation.getFile().getSize()
    image.linkAnnotation(file_annotation)

    answer = True
    return answer