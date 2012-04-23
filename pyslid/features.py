'''
Authors: Ivan E. Cao-Berg (icaoberg@scs.cmu.edu)
Created: May 1, 2011

Copyright (C) 2011-2012 Murphy Lab
Lane Center for Computational Biology
School of Computer Science
Carnegie Mellon University

April 19, 2012 
* I. Cao-Berg Modified features.calculate so that if no
  scale information is available for the image, then the
  method returns an empty array rather than using pyslic
  default scale of 0.23.

April 20, 2012 
* I. Cao-Berg Modified features.link so that now has an extra
  argument called scale and will link a feature record with this
  information
* I. Cao-Berg Added debug input argument to method features.link
* I. Cao-Berg Updated documentation on method features.link
* I. Cao-Berg Added debug flag to every method
* I. Cao-Berg Added unable to connect statement to all methods

April 22, 2012
* I. Cao-Berg Modified features.get so that now it will query a scale as well

April 23, 2012
* I. Cao-Berg Modified features.unlink to reflect the changes in the new OMERO API

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

import omero, pyslic, pyslid.utilities
import omero.callbacks
from omero.gateway import BlitzGateway
import omero.util.script_utils as utils

def getTableInfo(conn, did, set="slf33", field=True, debug=False ):
    '''
    Returns the number of images in the dataset and the number of images that has the OMERO.tables attached.
    @param connection (conn)
    @param dataset id (did)
    @param feature set name (set)
    @param field true if field features, false otherwise
    @return num_image number of images
    @return num_image_table (number of image that has a attached table)
    '''
    
    if not conn.isConnected():
        if debug:
            print "Unable to connect to OMERO.server"
        return [0,0]

    if not pyslid.utilities.hasDataset( conn, did ):
        return [0,0]

    if not isinstance( field, bool ):
        return [0,0]

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

def calculate( conn, iid, scale=None, set="slf33", field=True, rid=None, pixels=0, channels=[], zslice=0, timepoint=0, threshold=None, debug=False ):
    '''
    Calculates and returns a feature ids and features vectors given a valid
    image identification (iid). It currently calculates SLF33, SLF34, SLF35 and SLF36.
    This method will try to retrieve the resolution of the image from the annotation. If 
    
    @param conn
    @param image id (iid)
    @param resolution (scale)
    @param slf set id (set)
    @param pixels
    @param timepoint
    @return feature ids and values
    '''
   
    #check input arguments
    image = conn.getObject("Image", long(iid))

    if image is None:
        if debug:
            print "Unable to retrieve image"
        return []
    else:
        try:
            #if threshold is empty use default value
            if threshold == None:
                threshold = 10*1024;

            #check if image size is greater than threshold value
            if image.getPixels(pixels).getSizeX().getValue() > threshold:
                if debug:
                    print "Image size is greater than threshold value"
                return []
            elif image.getPixels(pixels).getSizeY().getValue() > threshold:
                if debug:
                    print "Image size is greater than threshold value"
                return []
            else:
                #set scale value
                scale = image.getPixels(pixels).getPhysicalSizeX()        
        except:
            #if no scale value is present, pyslic will set a scale value of .23
            print "Unable to retrieve resolution of resolution was not set"
            return []

    #set resolution based on the scale
    if scale < 0.2299:
        resolution = 0.25
    elif scale < 0.46:
        resolution = 0.5
    else:
        resolution = 1

    #create gateway
    #gateway = session.createGateway()

    feature_ids = ["SLF27.66","SLF27.67","SLF27.68","SLF27.69","SLF27.70","SLF27.71","SLF27.72","SLF27.73","SLF27.74","SLF27.75","SLF27.76","SLF27.77","SLF27.78","SLF33.37","SLF33.38","SLF33.39","SLF33.40","SLF33.41","SLF33.42","SLF33.43","SLF33.44","SLF33.45","SLF33.46","SLF33.47","SLF33.48","SLF33.49","SLF33.50","SLF33.51","SLF33.52","SLF33.53","SLF33.54","SLF33.55","SLF33.56","SLF33.57","SLF33.58","SLF33.59","SLF33.60","SLF33.61","SLF33.62","SLF33.63","SLF33.64","SLF33.65","SLF33.66","SLF33.67","SLF33.68","SLF33.69","SLF33.70","SLF33.71","SLF33.72","SLF33.73","SLF33.74","SLF33.75","SLF33.76","SLF33.77","SLF33.78","SLF33.79","SLF33.80","SLF33.81","SLF33.82","SLF33.83","SLF33.84","SLF33.85","SLF33.86","SLF33.87","SLF33.88","SLF33.89","SLF33.90","SLF33.91","SLF33.92","SLF33.93","SLF33.94","SLF33.95","SLF33.96","SLF33.97","SLF33.98","SLF33.99","SLF33.100","SLF33.101","SLF33.102","SLF33.103","SLF33.104","SLF33.105","SLF33.106","SLF33.107","SLF33.108","SLF33.109","SLF33.110","SLF33.111","SLF33.112","SLF33.113","SLF33.114","SLF27.1","SLF27.2","SLF27.3","SLF27.4","SLF27.5","SLF27.89","SLF27.90","SLF27.9","SLF27.10","SLF27.11","SLF27.12","SLF27.13","SLF27.80","SLF27.81","SLF27.82","SLF27.83","SLF27.84","SLF27.79","SLF31.1","SLF31.2","SLF31.3","SLF31.4","SLF31.5","SLF31.6","SLF31.7","SLF31.8","SLF31.9","SLF31.10","SLF31.11","SLF31.12","SLF31.13","SLF31.14","SLF31.15","SLF31.16","SLF31.17","SLF31.18","SLF33.1","SLF33.2","SLF33.3","SLF33.4","SLF33.5","SLF33.6","SLF33.7","SLF33.8","SLF33.9","SLF33.19","SLF33.20","SLF33.21","SLF33.22","SLF33.23","SLF33.24","SLF33.25","SLF33.26","SLF33.27","SLF33.10","SLF33.11","SLF33.12","SLF33.13","SLF33.14","SLF33.15","SLF33.16","SLF33.17","SLF33.18","SLF33.28","SLF33.29","SLF33.30","SLF33.31","SLF33.32","SLF33.33","SLF33.34","SLF33.35","SLF33.36","SLF34.1","SLF34.2","SLF34.3","SLF34.4","SLF34.5","SLF34.6","SLF34.7","SLF34.8","SLF34.9","SLF34.10","SLF27.80","SLF27.81","SLF27.82","SLF27.83","SLF27.84","SLF27.79","SLF27.1","SLF27.2","SLF27.3","SLF27.4","SLF27.5","SLF27.6","SLF27.7","SLF27.8","SLF27.85","SLF27.86","SLF27.87","SLF27.88","SLF27.89","SLF27.90","SLF27.14","SLF27.15","SLF27.16","SLF27.17","SLF27.18","SLF27.19","SLF27.20","SLF27.21","SLF27.22","SLF27.23","SLF27.24","SLF27.25","SLF27.26","SLF27.27","SLF27.28","SLF27.29","SLF27.30","SLF27.31","SLF27.32","SLF27.33","SLF27.34","SLF27.35","SLF27.36","SLF27.37","SLF27.38","SLF27.39","SLF27.40","SLF27.41","SLF27.42","SLF27.43","SLF27.44","SLF27.45","SLF27.46","SLF27.47","SLF27.48","SLF27.49","SLF27.50","SLF27.51","SLF27.52","SLF27.53","SLF27.54","SLF27.55","SLF27.56","SLF27.57","SLF27.58","SLF27.59","SLF27.60","SLF27.61","SLF27.62","SLF27.63","SLF27.64","SLF27.65","SLF27.66","SLF27.67","SLF27.68","SLF27.69","SLF27.70","SLF27.71","SLF27.72","SLF27.73","SLF27.74","SLF27.75","SLF27.76","SLF27.77","SLF27.78","SLF27.9","SLF27.10","SLF27.11","SLF27.12","SLF27.13","SLF31.1","SLF31.2","SLF31.3","SLF31.4","SLF31.5","SLF31.6","SLF31.7","SLF31.8","SLF31.9","SLF31.10","SLF31.11","SLF31.12","SLF31.13","SLF31.14","SLF31.15","SLF31.16","SLF31.17","SLF31.18"]
    
    if set=="slf34":
        #make pyslic image container
        img=pyslic.Image()
        img.label=iid
        img.scale=scale
		
        if len(channels) != 2:
            channels = [ 0, 1 ]
        labels = [ 'protein', 'dna' ] 

        for channel in channels:
            img.channels[ labels[channel] ] = channel
            img.channeldata[ labels[channel] ] = pyslid.utilities.getPlane(conn,iid,pixels,channel,zslice,timepoint)
        
        img.loaded=True
        features = []

        try:
             features = pyslic.computefeatures(img,'field-dna+')
             return [feature_ids[0:173], features, scale]
        except:
             return [[],[]]
    elif set=="slf33":
        #make pyslic image container
        img=pyslic.Image()
        img.label=iid
        img.scale=scale

        img.channels[ 'protein' ] = channels[0]
        img.channeldata[ 'protein' ] = pyslid.utilities.getPlane(conn,iid,zslice,channels[0],timepoint)

        img.loaded=True
        ids = []
        features = []    

        indices=[1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,56,57,58,59,60,61,62,63,64,65,66,67,68,69,70,71,72,73,74,75,76,77,78,79,80,81,82,83,84,85,86,87,88,89,90,91,92,93,94,95,96,99,100,101,102,103,104,105,106,107,108,109,110,111,112,113,114,115,116,117,118,119,120,121,122,123,124,125,126,127,128,129,130,131,132,133,134,135,136,137,138,139,140,141,142,143,144,145,146,147,148,149,150,151,152,153,154,155,156,157,158,159,160,161,162,163]
        for i in range(len(indices)):
            ids.append( feature_ids[indices[i]-1] )

        try:
            features = pyslic.computefeatures(img,'field+')
            return [ids, features]
        except:
            return [[],[]]
    elif set=="slf36":
        #make pyslic image container
        img=pyslic.Image()
        img.label=iid
        img.scale=scale

        if len(channels) != 2:
           channels = [ 0, 1 ]
        labels = [ 'protein', 'dna' ] 

        for channel in channels:
            img.channels[ labels[channel] ] = channel
            img.channeldata[ labels[channel] ] = pyslid.utilities.getPlane(conn,iid,zslice,channel,timepoint)

        img.loaded=True
        ids = []
        features = []

        try:
            values = pyslic.computefeatures(img,'field-dna+')
            indices = [12,10,11,1,18,17,6,7,8,9,20,2,3,19,4,5,21,22,13,14,15,16]
            for i in range(len(indices)):
                ids.append( feature_ids[indices[i]-1] )
                values.append( values[indices[i]-1] )
            return [ids, values, scale]
        except:
            return [[],[]]
    elif set=="slf35":
        #make pyslic image container
        img=pyslic.Image()
        img.label=iid
        img.scale=scale

        if len(channels) != 2:
            channels = [0, 1]
        labels = [ 'protein', 'dna' ] 

        for channel in channels:
            img.channels[ labels[channel] ] = channel
            img.channeldata[ labels[channel] ] = pyslid.utilities.getPlane(conn,iid,zslice,channel,timepoint)

        img.loaded=True
        ids = []
        features = []

        try:
            values = pyslic.computefeatures(img,'field-dna+')
            indices =[170,77,119,13,25,100,167,85,173,160,3,165,83,82,30,16,134,96,114,35,94,98,168]
            for i in range(len(indices)):
                ids.append( feature_ids[indices[i]-1] )
                features.append( values[indices[i]-1] )
            return [ids, features]
        except:
            return [[],[]]
    else:
        ids = []
        features = []
        return [ids, features]
		
def clink( conn, iid, set="slf34", field=True, rid=None, pixels=0, zslice=0, timepoint=0, threshold=None, overwrite=False, debug=False ):
    '''
    Calculates and links features to an object type given a valid id for the object.
    @param session
    @param type The object type. Can be Image, Dataset or Object
    @param id a valid object id
    @param pixels
    @param timepoint
    @param set a valid feature set id
    @param field True if these are field features, False otherwise
    @param rid region of interest id
    @param thresold a threshold value that prevents feature calculation if image is too big
    @param overwrite False if you dont wish to overwrite the feature table, True otherwise
    @return true if table is linked, false otherwise
    '''

    if not conn.isConnected():
        if debug:
            print "Unable to connect to OMERO.server"
        return False
    
    if not pyslid.utilities.hasImage( session, iid ):
        if debug:
            print "No image found with the given image id"
        return False

    if not isinstance( set, str ):
        return False
 
    if not isinstance( field, bool ):
        return False

    if not isinstance( pixels, int ):
        return False

    if not isinstance( zslice, int ):
        return False

    if not isinstance( timepoint, int ):
        return False

    if not isinstance( overwrite, bool ):
        return False
            
    try:
        [fids, features] = pyslid.features.calculate( conn, iid, set, field, rid, pixels, channels, zslice, timepoint, threshold ) 
    except:
        return False

    try:
        answer = pyslid.features.link( conn, iid, fids, features, set, field, rid, pixels, channel, zslice, timepoint)
        return answer
    except:
        return False
        
def unlink( conn, iid, set="slf34", field=True, rid=None, debug=False ):
    '''
    Unlinks and removes feature tables. If more than one feature table with the same 
    name are found to be linked to the same image, this function removes them all.
    @param connection (conn)
    @param image id (iid)
    @param feature set (set)
    @param true if field level features, false otherwise (field)
    @param region id (rid)
    @return true if the table was removed, false otherwise
    '''
    
    #create query service
    query = conn.getQueryService()

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
    string = "select iml from ImageAnnotationLink as iml join fetch iml.child as  fileAnn join fetch fileAnn.file join iml.parent as img where img.id = :iid and fileAnn.file.name = :filename"
    link = query.findByQuery(string, params)
    try:
        annotation = link.child
    except:
        return False

    #create delete service    
    deleteService = conn.getDeleteService()

    #list of commands
    commands = []
    commands.append(omero.api.delete.DeleteCommand("/ImageAnnotationLink", link.id.val, None))
    commands.append(omero.api.delete.DeleteCommand("/Annotation", annotation.id.val, None))

    deleteHandlePrx = deleteService.queueDelete(commands)
    callback = omero.callbacks.DeleteCallbackI(client, deleteHandlePrx)

    try:
        try:
            callback.loop(10, 500)
            return True
        except omero.LockTimeout:
            print "Not finished in 5 seconds. Cancelling..."

            if not deleteHandlePrx.cancel():
                print "ERROR: Failed to cancel"

            reports = deleteHandlePrx.report()
            return False
    except:
        return False

def get( conn, option, iid, scale=[], set="slf33", field=True, rid=None, pixels=0, channel=0, zslice=0, timepoint=0, calculate=False, debug=False ):
    '''
    Returns a features vector given an image id (iid), pixels, channel, zslice, and timepoint
    @param connection (conn)
    @param option can be either 'table', 'vector' or 'features'
    @param image id (iid)
    @param feature set name (set)
    @param field features option (field)
    @param rid region id (rid) (not the same as region of interest id)
    @param pixels index (pixels)
    @param channel index (channel)
    @param zslice index (zslice)
    @param time point index (timepoint)
    @param calculate true if you want features to be calculated if a feature table is not present
    @return features vector
    '''

    #if option != 'table' or option != 'vector' or option != 'features':
    #    return None
           
    if not pyslid.utilities.hasImage( conn, iid ):
        if debug:
            print "No image found with the given image id"
        return None
        
    if not isinstance( set, str ):
           return None
        
    #features
    if field == True:
        filename = 'iid-' + str(iid) + '_feature-' + set + '_field.h5';
    else:
        filename = 'iid-' + str(iid) + '_feature-' + set + '_roi.h5';

    #determine if there is only one table
    [answer, result] = has( conn, iid, set, field )
        
    if answer:
        #returns the file id associated with the table
        fid = result.getId().getValue()
        #open the table given the file id
        table = conn.getSharedResources().openTable( omero.model.OriginalFileI( fid, False ) )
                
        if option == 'table':
            return table

        elif option == 'features':
            #query a specific line in the table
            query = "(pixels ==" + str(pixels) + ") & (scale ==" + str(scale) + ") & (channel ==" + str(channel) +") & (zslice ==" + str(zslice) + ") & (timepoint =="  + str(timepoint) + ")"
            try:
                #try to get the ids that match our query
                ids = table.getWhereList( query, None, 0, table.getNumberOfRows(), 1 )
                #get the values that match the ids
                values = table.read( range(len(table.getHeaders())), ids[0],ids[0]+1 );
                #converts a Data type to a python list
                values = values.columns
                ids = []
                features = []
                for value in values:
                    ids.append( value.name )
                    features.append( value.values[0] )
                table.close()
                #ignore the first four values of the record

                #icaoberg march 23, 2012
                ids = ids[6:len(ids)]
                features = features[6:len(features)]
                return [ids,features]
            except:
                if table is not None:
                    table.close()
                return [[],[]]
        elif option == 'vector':
            try:
                values = table.read( range(len(table.getHeaders())), 0,table.getNumberOfRows() );
                #converts a Data type to a python list
                values = values.columns
                ids = []
                features = []
                for col in values:
                    ids.append( col.name )
                    features.append( list(col.values) )
                features = zip(*features)

                table.close()
                return [ids,features]
            except:
                if table is not None:
                    table.close()
                return [[],[]]        
        else:
                return None
    elif calculate:
        # to do
        #[ids,features] = pyslid.features.calculate( session, iid, set, field, rid,pixels, channels, zslice, timepoint, None )
        #return [ids, features]
        return [[],[]]
    else:
        return [[],[]]

def has( conn, iid, featureset="slf33", field=True, rid=None, debug=False ):
    '''
    Returns a boleean flag and and results from the query  if the image 
    has a feature table attached to it.

    @param connection (conn)
    @param image id (iid)
    @param feature set (set)
    @param field true if field features, false if regions of interest
    @param region of interest id (rid)
    @return true if there is an image attached to it, false otherwise
    @return result (query result)
    '''

    if not conn.isConnected():
        if debug:
            print "Unable to connect to OMERO.server"
        return False

    if not pyslid.utilities.hasImage( conn, iid ):
        if debug:
            print "No image found with the given image id"
        return False

    if not isinstance( featureset, str ):
        return False
		
    if not isinstance( field, bool ):
        return False

    if field == True:
        filename = 'iid-' + str(iid) + '_feature-' + str(featureset) + '_field.h5';
    else:
	filename = 'iid-' + str(iid) + '_feature-' + str(featureset) + '_roi.h5';

    #create and populate parameter
    params = omero.sys.ParametersI()
    params.addLong( "iid", iid )
    params.addString( "filename", filename )

    #hql string query
    string = "select f from ImageAnnotationLink as iml join iml.child as fileAnn " + \
             "join fileAnn.file as f join iml.parent as img where img.id = :iid and f.name = :filename "+ \
             "order by f.id desc"

    #database query
    query = conn.getQueryService()
	
    try:
        result = query.findByQuery(string, params.page(0,1))
    except:
	result = None

    if result is None:
        return [False, result]
    else:
        return [True, result]

def getIds( set="slf33", debug=False ):
    '''
    Returns a list of feature ids given a valid feature set name. 
    The only recognized featured sets are SLF33, SLF34, SLF35 and SLF36.
    @param feature set name (set)
    @returns list of feature ids
    '''
	
    if not isinstance( set, str ):
        return None
	
    feature_ids = ["SLF27.66","SLF27.67","SLF27.68","SLF27.69","SLF27.70","SLF27.71","SLF27.72","SLF27.73","SLF27.74","SLF27.75","SLF27.76","SLF27.77","SLF27.78","SLF33.37","SLF33.38","SLF33.39","SLF33.40","SLF33.41","SLF33.42","SLF33.43","SLF33.44","SLF33.45","SLF33.46","SLF33.47","SLF33.48","SLF33.49","SLF33.50","SLF33.51","SLF33.52","SLF33.53","SLF33.54","SLF33.55","SLF33.56","SLF33.57","SLF33.58","SLF33.59","SLF33.60","SLF33.61","SLF33.62","SLF33.63","SLF33.64","SLF33.65","SLF33.66","SLF33.67","SLF33.68","SLF33.69","SLF33.70","SLF33.71","SLF33.72","SLF33.73","SLF33.74","SLF33.75","SLF33.76","SLF33.77","SLF33.78","SLF33.79","SLF33.80","SLF33.81","SLF33.82","SLF33.83","SLF33.84","SLF33.85","SLF33.86","SLF33.87","SLF33.88","SLF33.89","SLF33.90","SLF33.91","SLF33.92","SLF33.93","SLF33.94","SLF33.95","SLF33.96","SLF33.97","SLF33.98","SLF33.99","SLF33.100","SLF33.101","SLF33.102","SLF33.103","SLF33.104","SLF33.105","SLF33.106","SLF33.107","SLF33.108","SLF33.109","SLF33.110","SLF33.111","SLF33.112","SLF33.113","SLF33.114","SLF27.1","SLF27.2","SLF27.3","SLF27.4","SLF27.5","SLF27.89","SLF27.90","SLF27.9","SLF27.10","SLF27.11","SLF27.12","SLF27.13","SLF27.80","SLF27.81","SLF27.82","SLF27.83","SLF27.84","SLF27.79","SLF31.1","SLF31.2","SLF31.3","SLF31.4","SLF31.5","SLF31.6","SLF31.7","SLF31.8","SLF31.9","SLF31.10","SLF31.11","SLF31.12","SLF31.13","SLF31.14","SLF31.15","SLF31.16","SLF31.17","SLF31.18","SLF33.1","SLF33.2","SLF33.3","SLF33.4","SLF33.5","SLF33.6","SLF33.7","SLF33.8","SLF33.9","SLF33.19","SLF33.20","SLF33.21","SLF33.22","SLF33.23","SLF33.24","SLF33.25","SLF33.26","SLF33.27","SLF33.10","SLF33.11","SLF33.12","SLF33.13","SLF33.14","SLF33.15","SLF33.16","SLF33.17","SLF33.18","SLF33.28","SLF33.29","SLF33.30","SLF33.31","SLF33.32","SLF33.33","SLF33.34","SLF33.35","SLF33.36","SLF34.1","SLF34.2","SLF34.3","SLF34.4","SLF34.5","SLF34.6","SLF34.7","SLF34.8","SLF34.9","SLF34.10","SLF27.80","SLF27.81","SLF27.82","SLF27.83","SLF27.84","SLF27.79","SLF27.1","SLF27.2","SLF27.3","SLF27.4","SLF27.5","SLF27.6","SLF27.7","SLF27.8","SLF27.85","SLF27.86","SLF27.87","SLF27.88","SLF27.89","SLF27.90","SLF27.14","SLF27.15","SLF27.16","SLF27.17","SLF27.18","SLF27.19","SLF27.20","SLF27.21","SLF27.22","SLF27.23","SLF27.24","SLF27.25","SLF27.26","SLF27.27","SLF27.28","SLF27.29","SLF27.30","SLF27.31","SLF27.32","SLF27.33","SLF27.34","SLF27.35","SLF27.36","SLF27.37","SLF27.38","SLF27.39","SLF27.40","SLF27.41","SLF27.42","SLF27.43","SLF27.44","SLF27.45","SLF27.46","SLF27.47","SLF27.48","SLF27.49","SLF27.50","SLF27.51","SLF27.52","SLF27.53","SLF27.54","SLF27.55","SLF27.56","SLF27.57","SLF27.58","SLF27.59","SLF27.60","SLF27.61","SLF27.62","SLF27.63","SLF27.64","SLF27.65","SLF27.66","SLF27.67","SLF27.68","SLF27.69","SLF27.70","SLF27.71","SLF27.72","SLF27.73","SLF27.74","SLF27.75","SLF27.76","SLF27.77","SLF27.78","SLF27.9","SLF27.10","SLF27.11","SLF27.12","SLF27.13","SLF31.1","SLF31.2","SLF31.3","SLF31.4","SLF31.5","SLF31.6","SLF31.7","SLF31.8","SLF31.9","SLF31.10","SLF31.11","SLF31.12","SLF31.13","SLF31.14","SLF31.15","SLF31.16","SLF31.17","SLF31.18"]    
    if set=="slf34":
        return feature_ids[0:173]
    elif set=="slf33":
        indices=[1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,56,57,58,59,60,61,62,63,64,65,66,67,68,69,70,71,72,73,74,75,76,77,78,79,80,81,82,83,84,85,86,87,88,89,90,91,92,93,94,95,96,99,100,101,102,103,104,105,106,107,108,109,110,111,112,113,114,115,116,117,118,119,120,121,122,123,124,125,126,127,128,129,130,131,132,133,134,135,136,137,138,139,140,141,142,143,144,145,146,147,148,149,150,151,152,153,154,155,156,157,158,159,160,161,162,163]
        ids=[]
        for i in range(len(indices)):
            ids.append( feature_ids[indices[i]-1] )
        return ids
    elif set=="slf36":
        indices = [12,10,11,1,18,17,6,7,8,9,20,2,3,19,4,5,21,22,13,14,15,16]
        ids=[]
        for i in range(len(indices)):
            ids.append( feature_ids[indices[i]-1] )
        return ids
    elif set=="slf35":
        indices =[170,77,119,13,25,100,167,85,173,160,3,165,83,82,30,16,134,96,114,35,94,98,168]
        ids=[]
        for i in range(len(indices)):
            ids.append( feature_ids[indices[i]-1] )
        return ids
    else:
	return None
		
def link(conn, iid, scale, fids, features, set, field=True, rid=None, pixels=0, channel=0,zslice=0, timepoint=0, debug=False):
    '''
    Creates a table from the feature vector and links the table to image with the 
    given image id (iid). 

    @param connection (conn)
    @param image id (iid)
    @param features ids (fids)
    @param features (features) 
    @param image resolution (scale)
    @param field (field) true if field features, false otherwise
    @param region id (rid) must be non-empty if field is False
    @param pixels index (pixels)
    @param channel index (channel)
    @param zslice index (zslice)
    @param timepoint index (timepoint)
    @return true if feature table was linked, false otherwise
    '''
     
    if not pyslid.utilities.hasImage( conn, iid ):
        if debug:
            print "No image found with the given image id"
        return False
	
    # check if image exist
    image = conn.getObject("Image", long(iid))
    if image is None:
        if debug:
            print "Unable to retrieve image"
        return False

    # generate a row-worth data in the OMERO.tables format
    if not fids:
        fids = []
        for i in range(len(features)):
            fids.append(str(i))
        
    columns = []
    columns.append(omero.grid.LongColumn( 'pixels', 'Pixel Index', [] ))
    columns.append(omero.grid.LongColumn( 'channel', 'Channel Index', [] ))
    columns.append(omero.grid.LongColumn( 'zslice', 'zSlice Index', [] ))
    columns.append(omero.grid.LongColumn( 'timepoint', 'Time Point Index', [] ))
    #icaoberg april 20, 2012
    columns.append(omero.grid.DoubleColumn( 'scale', 'Scale', [] ))

    for fid in fids:
        columns.append(omero.grid.DoubleColumn( str(fid), str(fid), [] ))

    # if there is already a feature table attached to the image, this will add the features row to the table
    [answer, result] = has(conn, iid, set, field)
	
    if answer:
        fid = result.getId().getValue()

        table = conn.getSharedResources().openTable( omero.model.OriginalFileI( fid, False ) )

        # append the new data
        columns[0].values.append( long(pixels) )
        columns[1].values.append( long(channel) ) 
        columns[2].values.append( long(zslice) )  
        columns[3].values.append( long(timepoint) )
        #icaoberg april 20, 2012
        columns[4].values.append( float(scale) )
        for i in range(5, len(fids)+5):
            columns[i].values.append( float(features[i-5]) ) 

        table.addData(columns)
        table.close()
    else:
        # create a new table and link it to the image
        if field==True:
            #table for field features
            table = conn.getSharedResources().newTable( 1, 'iid-' + str(iid) + '_feature-' + str(set) + '_field.h5' )
        else:
            #table for cell level features (roi == regions of interest)
            table = conn.getSharedResources().newTable( 1, 'iid-' + str(iid) + '_feature-' + str(set) + '_roi.h5' )
        table.initialize(columns)

        try:
            #create file link
            flink = omero.model.ImageAnnotationLinkI()
            #create annotation
            annotation = omero.model.FileAnnotationI()
            #link table to annotation object
            annotation.file = table.getOriginalFile()
            #create an annotation link between image and table
            flink.link( omero.model.ImageI(iid, False), annotation )
            conn.getUpdateService().saveObject(flink)
        except:
            table.close()
            return False

        # append the new data
        columns[0].values.append( long(pixels) )
        columns[1].values.append( long(channel) ) 
        columns[2].values.append( long(zslice) )  
        columns[3].values.append( long(timepoint) )
        #icaoberg april 20, 2012
        columns[4].values.append( float(scale) )
        for i in range(5, len(fids)+5):
            columns[i].values.append( float(features[i-5]) )

        try:
            table.addData( columns )
        except:
            table.close()
            return False

        #return true because it linked/update a table
        table.close()
        return True
		
def calculateOnDataset( conn, did, set="slf33", field=True, debug=False):
    '''
    calculate/link features on/to images in the dataset
    @param conn (Blitzgateway)
    @param set name
    @param field true if field features, false otherwise    
    @did dataset id
    @return number of image (num_image)
    @return number of images that feature calculation was performed with (num_image_calculate)
    '''
	
    if not conn.isConnected():
        if debug:
            print "Unable to connect to OMERO.server"
        return [0,0]
		
    if not pyslid.utilities.hasDataset( conn, did ):
        return [0,0]
		
    if not isinstance( set, str ):
        return [0,0]
		
    if not isinstance( field, bool ):
        return [0,0]
	
    num_image = 0
    num_image_calculate = 0
    
    ds = conn.getObject("Dataset", long(did))
    img_gen = ds.getChildLinks()
    for im in img_gen:
        num_image +=1
        iid = long(im.getId())
        [answer, result] = has(conn, iid, featureset, field)
        session = conn.c.sf
        if not answer:
            num_image_calculate +=1
            print iid
            image = conn.getObject("Image", long(iid))
            sizeC = image.getSizeC()

            field = True
            rid = []
            pixel = 0
            zslice = 0    #Currently, this code does NOT deal with 3D stack images yet.
            timepoint = 0 #Currently, this code does NOT deal with time-series images yet.
            threshold = None
            for channel in range(sizeC):
                [ids, feats] = calculate(conn, long(iid), featureset, field, rid, pixel, [channel], zslice, timepoint, threshold);
                print len(feats)
                #the following line should be changed with a regular pslid package function
                answer2 = link(conn, long(iid), ids, feats,  featureset, field, rid, pixel, channel,zslice, timepoint)
                print answer2

    return [num_image, num_image_calculate]

def delete(conn,iid,set="slf34",field=True):
    getFileID( conn, iid, set, field=True )
