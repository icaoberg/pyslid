"""
Authors: Ivan E. Cao-Berg (icaoberg@scs.cmu.edu)
Created: May 1, 2011

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

import omero, pyslic, pslid.utilities
import omero.callbacks

def calculate( session, iid, set="slf34", field=True, rid=None, pixels=0, zslice=0, timepoint=0, threshold=None ):
    """
    Calculates and returns a feature ids and features vectors given a valid
    image identification (iid). It currently calculates SLF33, SLF34, SLF35 and SLF36.
    @param session
    @param image id (iid)
    @param set slf set id
    @param pixels
    @param timepoint
    @return feature ids and values
    """
   
    #check input arguments
    if not pslid.utilities.hasImage( session, iid ):
        return []
    else:
        #get image information from omero
        image = pslid.utilities.getImage(session, iid)
        try:
            if threshold == None:
                threshold = 10*1024;

            #check if image size is greater than threshold value
            if image.getPixels(pixels).getSizeX().getValue() > threshold:
                return [[],[]]
            elif image.getPixels(pixels).getSizeY().getValue() > threshold:
                return [[],[]]
            else:
                #set scale value
                scale = image.getPixels(pixels).getPhysicalSizeX().getValue()        
        except:
            #if no scale value is present, pyslic will set a scale value of .23
            scale = None
 
    #create gateway
    gateway = session.createGateway()

    feature_ids = ["SLF27.66","SLF27.67","SLF27.68","SLF27.69","SLF27.70","SLF27.71","SLF27.72","SLF27.73","SLF27.74","SLF27.75","SLF27.76","SLF27.77","SLF27.78","SLF33.37","SLF33.38","SLF33.39","SLF33.40","SLF33.41","SLF33.42","SLF33.43","SLF33.44","SLF33.45","SLF33.46","SLF33.47","SLF33.48","SLF33.49","SLF33.50","SLF33.51","SLF33.52","SLF33.53","SLF33.54","SLF33.55","SLF33.56","SLF33.57","SLF33.58","SLF33.59","SLF33.60","SLF33.61","SLF33.62","SLF33.63","SLF33.64","SLF33.65","SLF33.66","SLF33.67","SLF33.68","SLF33.69","SLF33.70","SLF33.71","SLF33.72","SLF33.73","SLF33.74","SLF33.75","SLF33.76","SLF33.77","SLF33.78","SLF33.79","SLF33.80","SLF33.81","SLF33.82","SLF33.83","SLF33.84","SLF33.85","SLF33.86","SLF33.87","SLF33.88","SLF33.89","SLF33.90","SLF33.91","SLF33.92","SLF33.93","SLF33.94","SLF33.95","SLF33.96","SLF33.97","SLF33.98","SLF33.99","SLF33.100","SLF33.101","SLF33.102","SLF33.103","SLF33.104","SLF33.105","SLF33.106","SLF33.107","SLF33.108","SLF33.109","SLF33.110","SLF33.111","SLF33.112","SLF33.113","SLF33.114","SLF27.1","SLF27.2","SLF27.3","SLF27.4","SLF27.5","SLF27.89","SLF27.90","SLF27.9","SLF27.10","SLF27.11","SLF27.12","SLF27.13","SLF27.80","SLF27.81","SLF27.82","SLF27.83","SLF27.84","SLF27.79","SLF31.1","SLF31.2","SLF31.3","SLF31.4","SLF31.5","SLF31.6","SLF31.7","SLF31.8","SLF31.9","SLF31.10","SLF31.11","SLF31.12","SLF31.13","SLF31.14","SLF31.15","SLF31.16","SLF31.17","SLF31.18","SLF33.1","SLF33.2","SLF33.3","SLF33.4","SLF33.5","SLF33.6","SLF33.7","SLF33.8","SLF33.9","SLF33.19","SLF33.20","SLF33.21","SLF33.22","SLF33.23","SLF33.24","SLF33.25","SLF33.26","SLF33.27","SLF33.10","SLF33.11","SLF33.12","SLF33.13","SLF33.14","SLF33.15","SLF33.16","SLF33.17","SLF33.18","SLF33.28","SLF33.29","SLF33.30","SLF33.31","SLF33.32","SLF33.33","SLF33.34","SLF33.35","SLF33.36","SLF34.1","SLF34.2","SLF34.3","SLF34.4","SLF34.5","SLF34.6","SLF34.7","SLF34.8","SLF34.9","SLF34.10","SLF27.80","SLF27.81","SLF27.82","SLF27.83","SLF27.84","SLF27.79","SLF27.1","SLF27.2","SLF27.3","SLF27.4","SLF27.5","SLF27.6","SLF27.7","SLF27.8","SLF27.85","SLF27.86","SLF27.87","SLF27.88","SLF27.89","SLF27.90","SLF27.14","SLF27.15","SLF27.16","SLF27.17","SLF27.18","SLF27.19","SLF27.20","SLF27.21","SLF27.22","SLF27.23","SLF27.24","SLF27.25","SLF27.26","SLF27.27","SLF27.28","SLF27.29","SLF27.30","SLF27.31","SLF27.32","SLF27.33","SLF27.34","SLF27.35","SLF27.36","SLF27.37","SLF27.38","SLF27.39","SLF27.40","SLF27.41","SLF27.42","SLF27.43","SLF27.44","SLF27.45","SLF27.46","SLF27.47","SLF27.48","SLF27.49","SLF27.50","SLF27.51","SLF27.52","SLF27.53","SLF27.54","SLF27.55","SLF27.56","SLF27.57","SLF27.58","SLF27.59","SLF27.60","SLF27.61","SLF27.62","SLF27.63","SLF27.64","SLF27.65","SLF27.66","SLF27.67","SLF27.68","SLF27.69","SLF27.70","SLF27.71","SLF27.72","SLF27.73","SLF27.74","SLF27.75","SLF27.76","SLF27.77","SLF27.78","SLF27.9","SLF27.10","SLF27.11","SLF27.12","SLF27.13","SLF31.1","SLF31.2","SLF31.3","SLF31.4","SLF31.5","SLF31.6","SLF31.7","SLF31.8","SLF31.9","SLF31.10","SLF31.11","SLF31.12","SLF31.13","SLF31.14","SLF31.15","SLF31.16","SLF31.17","SLF31.18"]
    
    if set=="slf34":
        #make pyslic image container
        img=pyslic.Image()
        img.label=iid
        img.scale=scale
        channels=['protein','dna']

        for c in channels:
            channel_num=channels.index(c)
            img.channels[c]=channel_num
            img.channeldata[c]=pslid.utilities.getPlane(session,iid,zslice,channel_num,timepoint)
        
        img.loaded=True
        features = []    

        features = pyslic.computefeatures(img,'field-dna+')
        return [ids[0:173], features]
    elif set=="slf33":
        #make pyslic image container
        img=pyslic.Image()
        img.label=iid
        img.scale=scale

        channels=['protein']

        for c in channels:
            channel_num=channels.index(c)
            img.channels[c]=channel_num
            img.channeldata[c]=pslid.utilities.getPlane(session,iid,zslice,channel_num,timepoint)
        img.loaded=True
        ids = []
        features = []    

        indices=[1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,56,57,58,59,60,61,62,63,64,65,66,67,68,69,70,71,72,73,74,75,76,77,78,79,80,81,82,83,84,85,86,87,88,89,90,91,92,93,94,95,96,99,100,101,102,103,104,105,106,107,108,109,110,111,112,113,114,115,116,117,118,119,120,121,122,123,124,125,126,127,128,129,130,131,132,133,134,135,136,137,138,139,140,141,142,143,144,145,146,147,148,149,150,151,152,153,154,155,156,157,158,159,160,161,162,163]
        for i in range(len(indices)):
            ids.append( feature_ids[indices[i]-1] )    
        features = pyslic.computefeatures(img,'field+')
        return [ids, features]
    elif set=="slf36":
        #make pyslic image container
        img=pyslic.Image()
        img.label=iid
        img.scale=scale

        channels=['protein','dna']

        for c in channels:
            channel_num=channels.index(c)
            img.channels[c]=channel_num
            img.channeldata[c]=pslid.utilities.getPlane(session,iid,zslice,channel_num,timepoint)
        img.loaded=True
        ids = []
        features = []

        values = pyslic.computefeatures(img,'field-dna+')
        indices = [12,10,11,1,18,17,6,7,8,9,20,2,3,19,4,5,21,22,13,14,15,16]
        for i in range(len(indices)):
            ids.append( feature_ids[indices[i]-1] )
            values.append( values[indices[i]-1] )
        return [ids, values]
    elif set=="slf35":
        #make pyslic image container
        img=pyslic.Image()
        img.label=iid
        img.scale=scale

        channels=['protein','dna']

        for c in channels:
            channel_num=channels.index(c)
            img.channels[c]=channel_num
            img.channeldata[c]=pslid.utilities.getPlane(session,iid,zslice,channel_num,timepoint)
        img.loaded=True
        ids = []
        features = []

        values = pyslic.computefeatures(img,'field-dna+')
        indices =[170,77,119,13,25,100,167,85,173,160,3,165,83,82,30,16,134,96,114,35,94,98,168]
        for i in range(len(indices)):
            ids.append( feature_ids[indices[i]-1] )
            features.append( values[indices[i]-1] )
        return [ids, features]
    else:
        ids = []
        values = []
        return [ids, features]

def link( client, session, iid, feature_ids, features, set, field=True, rid=None, overwrite=False ):
    """
    Creates a table from the features vector and links
    the table to image with the given image id (iid). If the feature array is
    of size 2xN, then it assumes the first column corresponds to the feature ids 
    and the second column to the feature values. If the feature vector is of size 
    1xN, then it assumes the vector contains the feature values and it assigns 
    feature ids using the rule feature1, feature2,... featureN.
    @param session
    @param image id (iid)
    @param feature_ids a vector containing the feature names
    @param features a vector containing the features
    @param field true if field features, false otherwise
    @param region id (rid) must be non-empty if field is False
    @param overwrites
    @param table returns the OMERO Table object
    """
    
    #check if image exist
    if not pslid.utilities.hasImage( session, iid ):
        return False
         
    #check if there is already a feature table attached to the image
    if pslid.features.has( session, iid, set, field ) and not overwrite:
        return False

    if overwrite:
        pslid.features.unlink( client, session, iid, set, field, rid )

    try:
        columns = []
        for i in range(len(features)):
            if not feature_ids:
                try:
                    #create columns and append headers
                    columns.append(omero.grid.DoubleColumn(str(i), str(i), []));
                except:
                    return False
            else:
                try:
                    #create columns and append headers
                    columns.append(omero.grid.DoubleColumn(str(feature_ids[i]), str(feature_ids[i]), []));
                except:
                    return False
    except:
        return False
     
    #create shared resources
    resources = session.sharedResources()
    #create file repository
    repositories = resources.repositories()
    #create file link
    flink = omero.model.ImageAnnotationLinkI()
    
    # link features table
    try:
        if field==True:
            #table for field features
            table = resources.newTable( 1, 'iid-' + str(iid) + '_feature-' + set + '_field.h5' )
        else:
            #table for cell level features (roi == regions of interest)
            table = resources.newTable( 1, 'iid-' + str(iid) + '_feature-' + set + '_roi.h5' )
    except:
        return False    
   
    #create annotation 
    annotation = omero.model.FileAnnotationI()
    #link table to annotation object
    annotation.file = table.getOriginalFile()
    #create an annotation link between image and table
    flink.link( omero.model.ImageI(iid, False), annotation )
    #update service to reflect changes
    session.getUpdateService().saveObject(flink)
    
    #add column to table
    table.initialize(columns)

    for i in range(len(features)):
        #add data to the columns
        columns[i].values.append( float(features[i]) )  

    #add data to the columns
    table.addData( columns )
    
    #return true because it linked a table
    table.close()
    return True

def get( session, iid, set="slf34", field=True, rid=[], calculate=False, pixels=0, zslice=0, timepoint=0 ):
    """
    Returns a features vector given an image id (iid)
    @param session
    @param image id (iid)
    @param set name
    @return features vector
    """

    #features
    if field==True:
        filename = 'iid-' + str(iid) + '_feature-' + set + '_field.h5';
    else:
        filename = 'iid-' + str(iid) + '_feature-' + set + '_roi.h5';
    
    #determine if there is only one table
    if pslid.features.has( session, iid, set, field ):        
        fid = pslid.utilities.getFileID( session, iid, set, field )
        resources = session.sharedResources()
        table = resources.openTable( omero.model.OriginalFileI( fid, False ))
        values = table.read( range(len(table.getHeaders())), 0L, table.getNumberOfRows() );

        #converts a Data type to a python list
        values = values.columns

        ids = []
        features = []
      
        for value in values:
            ids.append( value.name )
            features.append( value.values[0] )
        table.close()
        return [ids, features]
    elif calculate:
        [ids,features] = pslid.features.calculate( session, iid, set, pixels, zslice, timepoint )
        return [ids, features]
    else:
        return [[],[]]

def clink( client, session, iid, set="slf34", field=True, rid=None, pixels=0, zslice=0, timepoint=0, threshold=None, overwrite=False ):
    """
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
    """
    
    if not pslid.utilities.hasImage( session, iid ):
        return False
            
    try:
        [ids, features] = pslid.features.calculate( session, iid, set, field, rid, pixels, zslice, timepoint, threshold )
    except:
        return False

    try:
        answer = pslid.features.link( client, session, iid, ids, features, set, field, rid, overwrite )
        return answer
    except:
        return False
    
def has( session, iid, set="slf34", field=True ):
    """
    Returns true if the image has a feature table attached to it.
    @param session
    @param iid
    @param set
    @param field
    @return True if there is an image attached to it, false otherwise
    """

    #casting to string prevents unicode errors when using django
    set = str(set)
    
    #create query service
    query = session.getQueryService()
    
    #create and populate parameter
    if field == True:
        filename = 'iid-' + str(iid) + '_feature-' + set + '_field.h5';
    else:
        filename = 'iid-' + str(iid) + '_feature-' + set + '_roi.h5';
    
    #casting to string prevents unicode errors when using django
    filename = str(filename)      

    #create and populate parameter
    params = omero.sys.ParametersI()
    
    try:
        params.addLong( "iid", iid );
    except TypeError:
        print "iid must be of type long"
    
    try:
        params.addString( "filename", filename );
    except TypeError:
        print "filename must be of type string"
    
    #hql string query
    string = "select iml from ImageAnnotationLink as iml join fetch iml.child as fileAnn join fetch fileAnn.file join iml.parent as img where img.id = :iid and fileAnn.file.name = :filename"
    
    #database query 
    result = query.findAllByQuery( string, params )  
    result = query.projection( string, params )
   
    #get answer
    answer = len(result)
    if answer == 0:
        return False
    else:
        return True
    
def unlink( client, session, iid, set="slf34", field=True, rid=None ):
    """
    Unlinks and removes feature tables. If more than one feature table with the same 
    name are found to be linked to the same image, this function removes them all.
    @param session
    @param iid
    @param set
    @param field
    @return True if the table was removed, false otherwise
    """
    
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
    string = "select iml from ImageAnnotationLink as iml join fetch iml.child as  fileAnn join fetch fileAnn.file join iml.parent as img where img.id = :iid and fileAnn.file.name = :filename"
    link = query.findByQuery(string, params)
    try:
        annotation = link.child
    except:
        return False

    #create delete service    
    deleteService = session.getDeleteService()

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
