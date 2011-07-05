"""
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
"""

import omero, pyslic
import omero.util.script_utils as utils

def connect( server, port ): 
    """
    Helper method that connects to an OMEPSLID server.
    @params server
    @params port
    @returns client
    """
    
    #connects to the server
    client = omero.client( server, port )
    #keeps the connection alive
    client.enableKeepAlive( 60 )
    #returns a client
    return client
    
def login( client, username, password ):
    """
    Login helper.
    @params client
    @params username
    @params password
    @return session
    """
     
    #login to the server
    session = client.createSession( username, password )
    
    #return session
    return session
    
def csv2features( filename ):
   """
   Opens a csv file and returns the feature array
   @param filename
   @return features array
   """
   
   file = open( filename, 'r' )
   features = []
   try:
       reader = csv.reader(file, delimiter=',')
       features = numpy.array([[float(col) for col in row] for row in reader])
   finally:
       file.close
       return features

def exportImage2Tif( session, iid ):
    """
    Exports an image in the database to OME TIFF.
    @param session
    @param location
    @param filename
    @param iid
    """
    
    f = None
    exporter = session.createExporter() # Stateful!
    try:
        exporter.addImage( iid )
        length = exporter.generateTiff()
        read = 0
        f = open("%s.ome.tif" % iid, "w")
        while True:
            buf = exporter.read(read, 1000000)
            f.write(buf)
            f.flush()
            # Store to file locally here
            if len(buf) < 1000000:
                break
            read += len(buf)
    finally:
        if f:
            f.close()
        exporter.close()
               
def exportPlanes2Tif( session, gateway, iid, slice, timepoint ):
    """
    Get an image from the OMERO database and saves a tif for 
    each channel present.
    @param session
    @gateway
    @image id (iid)
    @z-slice (slice)
    @time point (timepoint)
    """
 
    channels = getNumberOfChannels( gateway, iid )

    for channel in range(channels):
        plane = getPlane( session, gateway, iid, slice, channel, timepoint );
        mahotas.imsave( str(iid)+'-'+str(channel)+'.tif', plane )

def getDataset( session, did ):
    """
    Returns a dataset with the given dataset id (did).
    @param session
    @param dataset id (did)
    @return dataset
    """
    
    #create gateway
    gateway = session.createGateway()
    
    if hasDataset( session, did ):
        dataset = gateway.getDataset( did, True )
        gateway.close()
        return dataset
    else:
        print "No dataset exists with the given dataset id (did)"
        return []

def getFileID( session, iid, set, field=True ):

   #check input parameters
   if not hasImage( session, iid ):
        print "Nonexistent image given iid"
        return []
        
   if not isinstance( set, str ):
        print "Input argument set must be a string"
        return []
        
   if not isinstance( field, bool ):
        print "Input argument field must be a boolean"
        return []

   #create query service
   query = session.getQueryService()

   #create and populate parameter
   if field == True:
       filename = 'iid-' + str(iid) + '_feature-' + set + '_field.h5';
   else:
       filename = 'iid-' + str(iid) + '_feature-' + set + '_roi.h5';

   #create and populate parameter
   params = omero.sys.ParametersI()
   params.addLong( "iid", iid );
   params.addString( "filename", filename );

   #hql string query
   string = "select iml from ImageAnnotationLink as iml join fetch iml.child as fileAnn join fetch fileAnn.file join iml.parent as img where img.id = :iid and fileAnn.file.name = :filename"
  
   #database query 
   result =  query.findAllByQuery(string, params)  
   result = query.projection( string, params )
   
   #get answer
   fid = result.pop().pop()._val._child._file._id._val
   return fid
   
def getImage( session, iid ):
    """
    Returns an image with the given image id (iid).
    @param session
    @param image id (iid)
    @return image
    """
    
    #create gateway
    gateway = session.createGateway()
    
    if hasImage( session, iid ):
        image = gateway.getImage( iid )
        gateway.close()
        return image
    else:
        print "No image exists with the given iid"
        return []
        
def getListOfImages( session, did ):
    """
    Returns the list of images from the given
    dataset identification.
    @param gateway
    @param dataset identification
    @return a list of images
    """
    
    if hasDataset( session, did ):
        #create gateway
        gateway = session.createGateway()
    
        #retrieve dataset from server  
        dataset = gateway.getDataset( did, True )
        
        #get images as a list
        list = dataset.linkedImageList()
        iids = []
        for iid in list:
            iids.append( iid._id._val )
        
        iids.sort()
        
        #close gateway
        gateway.close()
        
        #return list of images
        return iids
    else:
        print "No dataset with the give did"
        return []


def getPlane( session, iid, slice, channel, timepoint ):

    #create gateway
    gateway = session.createGateway()
    
    #create pixel service (needed to extract pixels from image object)
    rawPixelsStore = session.createRawPixelsStore()
    
    #get image
    image = gateway.getImage( iid )
    
    #get plane id from image (we use zero because our images have only 
    #one pixel object per image object
    pid = image.getPixels( 0 ).getId().getValue();
    
    #retrieve pixel object
    pixels = session.getPixelsService().retrievePixDescription(pid);
   
    #update pixel service to match the current pixel object
    rawPixelsStore.setPixelsId( pid, True )
    
    #extract pixel object
    plane = utils.downloadPlane( rawPixelsStore, pixels, slice, channel, timepoint );
    
    #close services
    gateway.close()
    rawPixelsStore.close()
    
    #return plane
    return plane

def getProject( session, prid ):
    """
    Returns a project with the given project id (prid).
    @param session
    @param project id (prid)
    @return project
    """
    
    #create gateway
    gateway = session.createGateway()
    
    if hasDataset( session, did ):
        project = gateway.getProjects( [prid], True )
        gateway.close()
        return project
    else:
        print "No project exists with the given prid"
        return []

def getTable( session, iid, set="slf34", field=True ):
    """
    Returns a table from an image given a set name.
    @param session
    @param table id (tid)
    @return project
    """

    return []

def hasDataset( session, did ):
   """
   Determines if there is a dataset in the OMERO database with the given
   dataset id (did).
   @params session
   @params dataset id (did)
   @return true if dataset exists, false otherwise
   """

   #create query service
   query = session.getQueryService()

   #create and populate parameter
   params = omero.sys.ParametersI()
   params.addLong( "did", did );

   #hql string query
   string = "select count(*) from Dataset d where d.id = :did";

   #database query
   result = query.projection( string, params )

   #get answer
   answer = result.pop().pop()._val
   if answer == 0:
       return False
   else:
       return True
       
def hasFile( session, fid ):
  """
  Determines if there is a file annotation with file id (fid).
  @params session 
  @params file id (fid)
  @return true if there is a file annotation with file id (fid), false otherwise
  """

  #create query service
  query = session.getQueryService()

  #create and populate parameter
  params = omero.sys.ParametersI()
  params.addLong( "fid", fid );

  #hql string query
  string = "select count(*) from OriginalFile f where f.id = :fid";

  #database query
  result = query.projection( string, params )

  #get answer
  answer = result.pop().pop()._val
  if answer == 0:
     return False
  else:
     return True

def hasImage( session, iid ):
   """
   Determines if there is an image in the OMERO database with the given
   image id (iid).
   @params session
   @params image id (iid)
   @return true if image exists, false otherwise
   """

   #create query service
   query = session.getQueryService()

   #create and populate parameter
   params = omero.sys.ParametersI()
   params.addLong( "iid", iid );

   #hql string query
   string = "select count(*) from Image i where i.id = :iid";

   #database query
   result = query.projection( string, params )

   #get answer
   answer = result.pop().pop()._val
   if answer == 0:
       return False
   else:
       return True
       
def hasPlane( session, pid ):
   """
   Determines if there is a plane in the OMERO database with the given
   plane id (pid).
   @params session
   @params plane id (pid)
   @return true if plane exists, false otherwise
   """

   #create query service
   query = session.getQueryService()

   #create and populate parameter
   params = omero.sys.ParametersI()
   params.addLong( "pid", pid );

   #hql string query
   string = "select count(*) from Plane p where p.id = :pid";

   #database query
   result = query.projection( string, params )

   #get answer
   answer = result.pop().pop()._val
   if answer == 0:
       return False
   else:
       return True

def hasProject( session, prid ):
   """
   Determines if there is a project in the OMERO database with the given
   project id (prid).
   @params session
   @params project id (prid)
   @return true if project exists, false otherwise
   """

   #create query service
   query = session.getQueryService()

   #create and populate parameter
   params = omero.sys.ParametersI()
   params.addLong( "prid", prid );

   #hql string query
   string = "select count(*) from Project p where p.id = :prid";

   #database query 
   result = query.projection( string, params )

   #get answer
   answer = result.pop().pop()._val
   if answer == 0:
       return False
   else:
       return True

def hasTable( session, iid, set="slf34", field=True ):
   #create query service
   query = session.getQueryService()

   #create and populate parameter
   if field == True:
       filename = 'iid' + str(iid) + '_feature' + set + '_field.h5';
   else:
       filename = 'iid' + str(iid) + '_feature' + set + '_roi.h5';

   #create and populate parameters
   params = omero.sys.ParametersI()
   params.addLong( "iid", iid );
   params.addString( "filename", filename );

   #hql string query
   string = "select iml from ImageAnnotationLink as iml join fetch iml.child as fileAnn join fetch fileAnn.file join iml.parent as img where img.id = :iid and fileAnn.file.name = :filename"
  
   #database query
   result =  query.findAllByQuery(string, params)   

   #get answer
   answer = len(result)

   if answer == 0:
       return False
   else:
       return True
 
   