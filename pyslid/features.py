'''
'''

'''
Authors: Ivan E. Cao-Berg (icaoberg@scs.cmu.edu)
Created: May 1, 2011

Copyright (C) 2011-2013 Murphy Lab
Lane Center for Computational Biology
School of Computer Science
Carnegie Mellon University

April 19, 2012 

* I. Cao-Berg Modified features.calculate so that if no scale information is available for the image, then the method returns an empty array rather than using pyslic default scale of 0.23.

April 20, 2012  

* I. Cao-Berg Modified features.link so that now has an extra argument called scale and will link a feature record with this information 

* I. Cao-Berg Added debug input argument to method features.link 

* I. Cao-Berg Updated documentation on method features.link 

* I. Cao-Berg Added debug flag to every method 

* I. Cao-Berg Added unable to connect statement to all methods

April 22, 2012
* I. Cao-Berg Modified features.get so that now it will query a scale as well

April 23, 2012
* I. Cao-Berg Modified features.unlink to reflect the changes in the new OMERO API
* J. Bakal Improved features.has by setting the results to None when answer is False.

April 24, 2012
* I. Cao-Berg Modified features.calculate so that it returns the scale as well
* I. Cao-Berg Added debugging statements to features.getTableInfo
* I. Cao-Berg Updated features.clink to reflect changes in features.link and features.calculate
* I. Cao-Berg Added debugging statements and updated documentation to features.clink
* I. Cao-Berg Modified features.unlink to reflect the new changes in the API

April 26, 2012
* I. Cao-Berg Added getScales method that retrieves a list of unique scales for a feature table
* I. Cao-Berg Deprecated method getTableInfo

April 30, 2012
* I. Cao-Berg Changed query in method features.get

May 2, 2012
* I. Cao-Berg Renamed features.has to features.hasTable
* I. Cao-Berg Made features.has which now checks for a specific feature vector

May 7, 2012
* I. Cao-Berg Added try catch statement on features.getScales so that it returns an empty vector if it fails at reading values from a table
* I. Cao-Berg Fixed bug in features.unlink where it was still referencing the old API

February 19, 2013
* I. Cao-Berg Made changes to method to reflect changes to the OMERO API
* I. Cao-Berg Included the import of scipy

February 27, 2013
* I. Cao-Berg Fixed small bug were method was returning None when successfully linking
a table

March 1, 2013
* I. Cao-Berg Fixed small bug in calculate where the method was returning two values instead of three when a feature set name is unknown or unrecognized

This program is free software; you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation; either version 2 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with this program; if not, write to the Free Software Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.

For additional information visit http://murphylab.web.cmu.edu or send email to murphy@cmu.edu
'''

import omero, pyslic, pyslid.utilities, pyslid.image
from utilities import PyslidException
import omero.callbacks
from omero.gateway import BlitzGateway
import omero.util.script_utils as utils
import numpy, scipy

def getTableInfo(conn, did, set="slf33", field=True, debug=False ):
    '''
    Returns the number of images in the dataset and the number of images that has the OMERO.tables attached.

    If the method is unable to connect to the OMERO.server, then the method will return None.

    If the method doesn't find an image associated with the given image id (iid), then the
    method will return None.

    For detailed outputs, set debug flag to True.

    :param connection: connection
    :param did: dataset id
    :type did: long
    :param set: feature set name
    :type set: string
    :param field: true if field features, false otherwise
    :type field: boolean
    :rtype: number of images and number of images that has an attached table
    '''
    
    if not conn.isConnected():
        print "Unable to connect to OMERO.server"
        return [None,None]

    if not pyslid.utilities.hasDataset( conn, did ):
        print "No dataset found with the given dataset id:" +  str(did)
        return [None,None]

    if not isinstance( field, bool ):
        print "Input parameter field must be a boolean"
        return [None,None]

    #retrieve dataset
    ds = conn.getObject("Dataset", long(did))

    #get all the images associated with the dataset    
    img_gen = ds.getChildLinks()

    num_image = 0
    num_image_table = 0

    for im in img_gen:
        num_image +=1
        iid = long(im.getId())

        #check if image has a table attached
        [answer, result] = hasTable(conn, iid, set, field)
        if answer:
            num_image_table += 1

    return [num_image, num_image_table]

def calculate( conn, iid, scale=1, set="slf33", field=True, rid=None, pixels=0, channels=[], zslice=0, timepoint=0, threshold=None, debug=False ):
    '''
    Calculates and returns a feature ids vector, a feature vector and the output scale given a valid
    image identification (iid). It currently can calculate SLF33, SLF34, SLF35 and SLF36.

    This method will try to retrieve the resolution of the image from the annotations. 

    If the method is unable to connect to the OMERO.server, then the method will return None.

    If the method doesn't find an image associated with the given image id (iid), then the method will return None.

    For detailed outputs, set debug flag to True.
    
    :param conn: connection
    :type conn: BlitzGateway connection
    :param iid: image id
    :type iid: long
    :param scale: image scale
    :type scale: double
    :param set: feature set name
    :type set: string
    :param field: true if field features, false otherwise
    :type field: boolean
    :param rid: region id
    :type rid: long
    :param pixels: pixel index associated with the image
    :type pixels: integer
    :param channels: list of channel indices
    :type channels: list of integers
    :param zslice: zslice index
    :type zslice: integer
    :param timepoint: time point index
    :type timepoint: integer
    :param threshold: image size threshold value
    :type threshold: integer
    :param debug: debug flag
    :type debug: boolean
    :rtype: a list of feature ids, a feature vector and the scale at which the features where calculated
    '''
   
    if not conn.isConnected():
        raise PyslidException("Unable to connect to OMERO.server")

    if not pyslid.utilities.hasImage( conn, iid ):
        raise PyslidException("No image found with the given image id:%s", iid)
    #check input arguments
    image = conn.getObject("Image", long(iid) )

    if image is None:
        raise PyslidException("Unable to retrieve image with iid:%s", iid)
    else:
        try:
            #if threshold is empty use default value
            if threshold == None:
                threshold = 10*1024;

            #check if image size is greater than threshold value
            #icaoberg 19/02/2013
            if image.getPixelSizeY() > threshold:
                raise PyslidException("Image size is greater than threshold value")
            #icaoberg 19/02/2013
            elif image.getPixelSizeY() > threshold:
                raise PyslidException("Image size is greater than threshold value")
            else:
                #set scale value
                imgScale = pyslid.image.getScale( conn, iid, debug )
                imgScale = imgScale[0]        
        except:
            #if no scale value is present, pyslic will set a scale value of .23
            #to avoid that we prevent feature calculation
            raise PyslidException("Unable to retrieve resolution or resolution was not set")

    #set resolution based on the scale
    print 'scale:%f imgScale:%f' %(scale, imgScale)
    inputScale = scale
    if scale < 0.33 and abs(scale - imgScale)>0.001 :
         scale = imgScale
    elif scale < 0.67 and abs(scale - imgScale*2)>0.001:
         scale = imgScale*2
    else:
         scale = imgScale*4
    print 'Forcing pyslid calculated scale from %f to input scale %f' % (
        scale, inputScale)
    scale = inputScale

    feature_ids = ["SLF27.66","SLF27.67","SLF27.68","SLF27.69","SLF27.70","SLF27.71","SLF27.72","SLF27.73","SLF27.74","SLF27.75","SLF27.76","SLF27.77","SLF27.78","SLF33.37","SLF33.38","SLF33.39","SLF33.40","SLF33.41","SLF33.42","SLF33.43","SLF33.44","SLF33.45","SLF33.46","SLF33.47","SLF33.48","SLF33.49","SLF33.50","SLF33.51","SLF33.52","SLF33.53","SLF33.54","SLF33.55","SLF33.56","SLF33.57","SLF33.58","SLF33.59","SLF33.60","SLF33.61","SLF33.62","SLF33.63","SLF33.64","SLF33.65","SLF33.66","SLF33.67","SLF33.68","SLF33.69","SLF33.70","SLF33.71","SLF33.72","SLF33.73","SLF33.74","SLF33.75","SLF33.76","SLF33.77","SLF33.78","SLF33.79","SLF33.80","SLF33.81","SLF33.82","SLF33.83","SLF33.84","SLF33.85","SLF33.86","SLF33.87","SLF33.88","SLF33.89","SLF33.90","SLF33.91","SLF33.92","SLF33.93","SLF33.94","SLF33.95","SLF33.96","SLF33.97","SLF33.98","SLF33.99","SLF33.100","SLF33.101","SLF33.102","SLF33.103","SLF33.104","SLF33.105","SLF33.106","SLF33.107","SLF33.108","SLF33.109","SLF33.110","SLF33.111","SLF33.112","SLF33.113","SLF33.114","SLF27.1","SLF27.2","SLF27.3","SLF27.4","SLF27.5","SLF27.89","SLF27.90","SLF27.9","SLF27.10","SLF27.11","SLF27.12","SLF27.13","SLF27.80","SLF27.81","SLF27.82","SLF27.83","SLF27.84","SLF27.79","SLF31.1","SLF31.2","SLF31.3","SLF31.4","SLF31.5","SLF31.6","SLF31.7","SLF31.8","SLF31.9","SLF31.10","SLF31.11","SLF31.12","SLF31.13","SLF31.14","SLF31.15","SLF31.16","SLF31.17","SLF31.18","SLF33.1","SLF33.2","SLF33.3","SLF33.4","SLF33.5","SLF33.6","SLF33.7","SLF33.8","SLF33.9","SLF33.19","SLF33.20","SLF33.21","SLF33.22","SLF33.23","SLF33.24","SLF33.25","SLF33.26","SLF33.27","SLF33.10","SLF33.11","SLF33.12","SLF33.13","SLF33.14","SLF33.15","SLF33.16","SLF33.17","SLF33.18","SLF33.28","SLF33.29","SLF33.30","SLF33.31","SLF33.32","SLF33.33","SLF33.34","SLF33.35","SLF33.36","SLF34.1","SLF34.2","SLF34.3","SLF34.4","SLF34.5","SLF34.6","SLF34.7","SLF34.8","SLF34.9","SLF34.10","SLF27.80","SLF27.81","SLF27.82","SLF27.83","SLF27.84","SLF27.79","SLF27.1","SLF27.2","SLF27.3","SLF27.4","SLF27.5","SLF27.6","SLF27.7","SLF27.8","SLF27.85","SLF27.86","SLF27.87","SLF27.88","SLF27.89","SLF27.90","SLF27.14","SLF27.15","SLF27.16","SLF27.17","SLF27.18","SLF27.19","SLF27.20","SLF27.21","SLF27.22","SLF27.23","SLF27.24","SLF27.25","SLF27.26","SLF27.27","SLF27.28","SLF27.29","SLF27.30","SLF27.31","SLF27.32","SLF27.33","SLF27.34","SLF27.35","SLF27.36","SLF27.37","SLF27.38","SLF27.39","SLF27.40","SLF27.41","SLF27.42","SLF27.43","SLF27.44","SLF27.45","SLF27.46","SLF27.47","SLF27.48","SLF27.49","SLF27.50","SLF27.51","SLF27.52","SLF27.53","SLF27.54","SLF27.55","SLF27.56","SLF27.57","SLF27.58","SLF27.59","SLF27.60","SLF27.61","SLF27.62","SLF27.63","SLF27.64","SLF27.65","SLF27.66","SLF27.67","SLF27.68","SLF27.69","SLF27.70","SLF27.71","SLF27.72","SLF27.73","SLF27.74","SLF27.75","SLF27.76","SLF27.77","SLF27.78","SLF27.9","SLF27.10","SLF27.11","SLF27.12","SLF27.13","SLF31.1","SLF31.2","SLF31.3","SLF31.4","SLF31.5","SLF31.6","SLF31.7","SLF31.8","SLF31.9","SLF31.10","SLF31.11","SLF31.12","SLF31.13","SLF31.14","SLF31.15","SLF31.16","SLF31.17","SLF31.18"]
    
    if set=="slf34":
        #make pyslic image container
        img=pyslic.Image()
        img.label=iid
        img.scale=scale
		
        if len(channels) != 2:
            raise PyslidException("Two channels required for slf34")
        labels = [ 'protein', 'dna' ] 

        for c in xrange(2):
            img.channels[ labels[c] ] = channels[c]
            plane = pyslid.utilities.getPlane(
                conn, iid, pixels, channels[c], zslice, timepoint)
            img.channeldata[ labels[c] ] = scipy.misc.imresize(plane, scale)
        
        img.loaded=True
        features = []

        try:
            features = pyslic.computefeatures(img,'field-dna+')
            result = [feature_ids[0:173], features, scale]
        except:
            print "Unable to calculate features"
            raise
    elif set=="slf33":
        #make pyslic image container
        img=pyslic.Image()
        img.label=iid
        img.scale=scale

        print 'scale: %f' % scale
        img.channels[ 'protein' ] = channels[0]
        plane = pyslid.utilities.getPlane(
            conn, iid, pixels, channels[0], zslice, timepoint)
        img.channeldata[ 'protein' ] = scipy.misc.imresize( plane, scale )

        img.loaded=True
        print 'img:%s shape:%s' % (img, img.channeldata['protein'].shape)
        ids = []
        features = []    

        indices=[1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,56,57,58,59,60,61,62,63,64,65,66,67,68,69,70,71,72,73,74,75,76,77,78,79,80,81,82,83,84,85,86,87,88,89,90,91,92,93,94,95,96,99,100,101,102,103,104,105,106,107,108,109,110,111,112,113,114,115,116,117,118,119,120,121,122,123,124,125,126,127,128,129,130,131,132,133,134,135,136,137,138,139,140,141,142,143,144,145,146,147,148,149,150,151,152,153,154,155,156,157,158,159,160,161,162,163]
        for i in range(len(indices)):
            ids.append( feature_ids[indices[i]-1] )

        try:
            features = pyslic.computefeatures(img,'field+')
            result = [ids, features, scale]
        except:
            print "Unable to calculate features"
            raise
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
            plane = pyslid.utilities.getPlane(
                conn, iid, pixels, channel, zslice, timepoint)
            img.channeldata[ labels[channel] ] = scipy.misc.imresize( plane, scale )

        img.loaded=True
        ids = []
        features = []

        try:
            values = pyslic.computefeatures(img,'field-dna+')
            indices = [12,10,11,1,18,17,6,7,8,9,20,2,3,19,4,5,21,22,13,14,15,16]
            for i in range(len(indices)):
                ids.append( feature_ids[indices[i]-1] )
                values.append( values[indices[i]-1] )
            result = [ids, values, scale]
        except:
            print "Unable to calculate features" 
            raise
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
            img.channeldata[ labels[channel] ] = pyslid.utilities.getPlane(
                conn, iid, pixels, channel, zslice, timepoint)

        img.loaded=True
        ids = []
        features = []

        try:
            values = pyslic.computefeatures(img,'field-dna+')
            indices =[170,77,119,13,25,100,167,85,173,160,3,165,83,82,30,16,134,96,114,35,94,98,168]
            for i in range(len(indices)):
                ids.append( feature_ids[indices[i]-1] )
                features.append( values[indices[i]-1] )
            result = [ids, features, scale]
        except:
            print "Unable to calculate features"
            raise
    elif set=="min_max_mean":
        if len(channels) != 1:
            raise PyslidException("Expected 1 channel for featureset %s" % set)

        plane = pyslid.utilities.getPlane(
            conn, iid, pixels, channels[0], zslice, timepoint)
        ids = getIds(set)
        features = numpy.array([plane.min(), plane.max(), plane.mean()])
        result = [ids, features, scale]
    else:
        raise PyslidException("Invalid feature set name")

    # pyslic has a bug which can result in an incorrect number of features
    # being returned
    if len(result[0]) != len(result[1]):
        raise PyslidException(
            "Mismatch between featureids and feature values"
            "\nfids:%s\nfeatures:%s" % (result[0], result[1]))

    return result

		
def clink( conn, iid, scale=1, set="slf34", field=True, rid=None, pixels=0, zslice=0, 
    timepoint=0, threshold=None, overwrite=False, debug=False ):
    '''
    Calculates and links features to an object type given a valid id for the object.
    Will only work for feature sets defined in features.calculate. If you wish to use your own
    features sets, calculate them and use features.link to link to the image.
    This method is a shortcut for feature sets defined by the Murphy Lab.

    If the method is unable to connect to the OMERO.server, then the method will return False.
    If the method doesn't find an image associated with the given image id (iid), then the
    method will return False.

    For detailed outputs, set debug flag to True.

    :param conn: connection
    :type conn: BlitzGateway connection
    :param iid: image id
    :type iid: long
    :param scale: image scale
    :type scale: double
    :param set: feature set name
    :type set: string
    :param field: true if field features, false otherwise
    :type field: boolean
    :param rid: region id
    :type rid: long
    :param pixels: pixel index associated with the image
    :type pixels: integer
    :param zslice: zslice index
    :type zslice: integer
    :param timepoint: time point index
    :type timepoint: integer
    :param threshold: image size threshold value
    :type threshold: integer
    :param overwrite: a flag that say whether it should overwrite feature vector if one is found
    :param debug: debug flag
    :type debug: boolean
    :rtype: true if it calculated the feature vector and successfully added it to a feature table
    '''

    if not conn.isConnected():
        print "Unable to connect to OMERO.server"
        return False
    
    if not pyslid.utilities.hasImage( conn, iid ):
        print "No image found with the given image id"
        return False

    if not isinstance( set, str ):
        print "Input argument set must be a string"
        return False
 
    if not isinstance( field, bool ):
        print "Input argument field must be a boolean"
        return False

    if not isinstance( pixels, int ):
        print "Input argument pixels must be an integer"
        return False

    if not isinstance( zslice, int ):
        print "Input argument zslice must be an integer"
        return False

    if not isinstance( timepoint, int ):
        print "Input argument timepoint must be an integer"
        return False

    if not isinstance( overwrite, bool ):
        print "Input argument overwrite must be a a boolean"
        return False
            
    try:
        [fids, features, scale] = pyslid.features.calculate( conn, iid, scale, set, field, rid, pixels, channels, zslice, timepoint, threshold ) 
    except:
        print "Unable to calculate features"
        return False

    try:
        answer = pyslid.features.link( conn, iid, scale, fids, features, set, field, rid, pixels, channel, zslice, timepoint)
        return answer
    except:
        print "Unable to attach feature table to image"
        return False
        
def unlink( conn, iid, set="slf34", field=True, rid=None, debug=False ):
    '''
    Unlinks and removes feature tables. If more than one feature table with the same 
    name are found to be linked to the same image, this function removes them all.

    :param conn: connection
    :type conn: BlitzGateway connection
    :param iid: image id
    :type iid: long
    :param set: feature set name
    :type set: string
    :param field: true if field features, false otherwise
    :type field: boolean
    :param rid: region id
    :type rid: long
    :param debug: debug flag
    :type debug: boolean
    :rtype: true if the table was removed, false otherwise
    '''

    if not conn.isConnected():
        print "Unable to connect to OMERO.server"
        return False

    if not pyslid.utilities.hasImage( conn, iid ):
        print "No image found with the given image id"
        return False

    if not isinstance( set, str ):
        print "Input argument set must be a string"
        return False

    if not isinstance( field, bool ):
        print "Input argument field must be a boolean"
        return False
    
    fileID = pyslid.utilities.getFileID( conn, iid, set, field )

    #delete object
    try:
        conn.deleteObjects("Annotation", [fileID], deleteChildren=True, deleteAnns=True)
        return True
    except:
        print "Unable to delete feature table"
        return False
 
def get( conn, option, iid, scale=None, set="slf33", field=True, rid=None, pixels=0, channel=0, zslice=0, timepoint=0, calculate=False, debug=False ):
    '''
    Returns a features vector given an image id (iid), pixels, channel, zslice, and timepoint

    :param conn: connection
    :type conn: BlitzGateway connection
    :param iid: image id
    :param option: a valid option, can be table, features or vector
    :type option: string
    :param iid: image id
    :type iid: long
    :param scale: image scale
    :type scale: double
    :param set: feature set name
    :type set: string
    :param field: true if field features, false otherwise
    :type field: boolean
    :param rid: region id
    :type rid: long
    :param pixels: pixel index associated with the image
    :type pixels: integer
    :param channel: channel index
    :type channel: integer
    :param zslice: zslice index
    :type zslice: integer
    :param timepoint: time point index
    :type timepoint: integer
    :param calculate: flag that asks whether it should calculate features if vector not found
    :type calculate: boolean
    :param debug: debug flag
    :type debug: boolean
    :rtype: features
    '''

    #if option != 'table' or option != 'vector' or option != 'features':
    #    return None
           
    if not pyslid.utilities.hasImage( conn, iid ):
        raise PyslidException("No image found with the given image id:%s", iid)
        
    if not isinstance( set, str ):
        raise PyslidException("Input argument set must be a string")
        
    #features
    if field == True:
        filename = 'iid-' + str(iid) + '_feature-' + set + '_field.h5';
    else:
        filename = 'iid-' + str(iid) + '_feature-' + set + '_roi.h5';

    #determine if there is only one table
    [answer, result] = hasTable( conn, iid, set, field )
        
    if answer:
        #returns the file id associated with the table
        fid = result.getId().getValue()
        #open the table given the file id
        table = conn.getSharedResources().openTable(
            omero.model.OriginalFileI(fid, False), conn.SERVICE_OPTS)

        if option == 'table':
            return table

        elif option == 'features':
            #query a specific line in the table
            #icaoberg april 30, 2012
            query = "(pixels ==" + repr(pixels) + ") & (scale ==" + repr(scale) + ") & (channel ==" + repr(channel) +") & (zslice ==" + repr(zslice) + ") & (timepoint =="  + repr(timepoint) + ")"
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
                ids = ids[5:len(ids)]
                features = features[5:len(features)]
                return [ids,features]
            except:
                if table is not None:
                    table.close()
                raise
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
                raise
        else:
            raise PyslidException("Unexpected option")

    elif calculate:
        # to do
        #[ids,features] = pyslid.features.calculate( conn, iid, set, field, rid,pixels, channels, zslice, timepoint, None )
        #return [ids, features]
        raise PyslidException("Not implemented")
    else:
        raise PyslidException("No answer")

def hasTable( conn, iid, featureset="slf33", field=True, rid=None, debug=False ):
    '''
    Returns a boleean flag and and results from the query  if the image 
    has a feature table attached to it.

    :param conn: connection
    :type conn: BlitzGateway connection
    :param iid: image id
    :type iid: long
    :param featureset: feature set name
    :type featureset: string
    :param field: true if field features, false otherwise
    :type field: boolean
    :param rid: region id
    :type rid: long
    :param debug: debug flag
    :type debug: boolean
    :rtype: true if it has an attached feature table, false otherwise
    '''

    if not conn.isConnected():
        raise PyslidException("Unable to connect to OMERO.server")

    if not pyslid.utilities.hasImage( conn, iid ):
        raise PyslidException("No image found with the given image id:%s", iid)

    if not isinstance( featureset, str ):
        raise PyslidException("Input argument feature set must be a string")
		
    if not isinstance( field, bool ):
        raise PyslidException("Input argument field must be boolean")

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
        result = query.findByQuery(string, params.page(0,1), conn.SERVICE_OPTS)
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

    :param set: feature set name
    :type set: string
    :param debug: debug flag
    :type debug: boolean
    :rtype: list of feature ids
    '''
	
    if not isinstance( set, str ):
        PyslidException("Expected set to be a string")
	
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
    elif set=="min_max_mean":
        return ["min", "max", "mean"]
    else:
        print "Unrecognized feature set name: " + set
        return None
		
def link(conn, iid, scale, fids, features, set, field=True, rid=None, pixels=0, channel=0, zslice=0, timepoint=0, debug=False):
    '''
    Creates a table from the feature vector and links the table to image with the 
    given image id (iid).  If the table exists, then it appends the feature vector to the table.

    :param conn: connection
    :type conn: BlitzGateway connection
    :param iid: image id
    :type iid: long
    :param scale: scale at which the features where calculated
    :type scale: double
    :param fids: feature ids list
    :type fids: list of strings
    :param features: feature vector
    :type features: list of features
    :param set: feature set name
    :type set: string
    :param field: true if field features, false otherwise
    :type field: boolean
    :param rid: region id
    :type rid: long
    :param pixels: pixel index associated with the image
    :type pixels: integer
    :param channel: channel index
    :type channel: integer
    :param zslice: zslice index
    :type zslice: integer
    :param timepoint: time point index
    :type timepoint: integer
    :param debug: debug flag
    :type debug: boolean
    :rtype: true if feature if it successfully added feature vector to feature table, false otherwise
    '''
     
    if not conn.isConnected():
        print "Unable to connect to OMERO.server"
        return False

    if not pyslid.utilities.hasImage( conn, iid ):
        raise PyslidException("No image found with the given image id:%s", iid)
	
    # check if image exist
    image = conn.getObject( "Image", long(iid) )
    if image is None:
        raise PyslidException("Unable to retrieve image with id:%s", iid)

    # generate a row-worth data in the OMERO.tables format

    #if the feature ids/names is empty, generate a list feature name given by their index in list
    if not fids:
        fids = []
        for i in range(len(features)):
            fids.append( "feature" + str(i) )
    
    columns = []
    columns.append(omero.grid.LongColumn( 'pixels', 'Pixel Index', [] ))
    columns.append(omero.grid.LongColumn( 'channel', 'Channel Index', [] ))
    columns.append(omero.grid.LongColumn( 'zslice', 'zSlice Index', [] ))
    columns.append(omero.grid.LongColumn( 'timepoint', 'Time Point Index', [] ))
    columns.append(omero.grid.DoubleColumn( 'scale', 'Scale', [] ))

    for fid in fids:
        columns.append(omero.grid.DoubleColumn( str(fid), str(fid), [] ))
	
    # if there is already a feature table attached to the image, this will add the features row to the table
    [answer, result] = hasTable( conn, iid, set, field )
	
    if answer:
        fid = result.getId().getValue()

        table = conn.getSharedResources().openTable(
            omero.model.OriginalFileI(fid, False), conn.SERVICE_OPTS)

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
        return True
    else:
        # create a new table and link it to the image
        if field==True:
            #table for field features
            table = conn.getSharedResources().newTable(
                1, 'iid-' + str(iid) + '_feature-' + str(set) + '_field.h5',
                conn.SERVICE_OPTS)
        else:
            #table for cell level features (roi == regions of interest)
            table = conn.getSharedResources().newTable(
                1, 'iid-' + str(iid) + '_feature-' + str(set) + '_roi.h5',
                conn.SERVICE_OPTS)
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
            conn.getUpdateService().saveObject(flink, conn.SERVICE_OPTS)
        except:
            table.close()
            raise PyslidException("Unable to create file annotation link")


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
            raise PyslidException("Unable to add data to the table")

        #return true because it linked/update a table
        table.close()
        return True
		
def calculateOnDataset( conn, did, set="slf33", field=True, debug=False):
    '''
    Helper method that will calculate and link features on all images in a dataset

    :param conn: connection
    :type conn: BlitzGateway connection
    :param did: dataset id
    :type did: long
    :param field: true if field features, false otherwise
    :type field: boolean
    :param debug: debug flag
    :type debug: boolean
    '''
	
    if not conn.isConnected():
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
        [answer, result] = hasTable(conn, iid, featureset, field)
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

def delete( conn, iid, set="slf34", field=True ):
    '''
    Helper method that removes and unlinks a feature table attached to an image

    :param conn: connection
    :type conn: BlitzGateway connection
    :param iid: image id
    :type iid: long
    :param set: feature set name
    :type set: string
    :param field: true if field features, false otherwise
    :type field: boolean
    :rtype: true if it successfully deleted the table, false otherwise
    '''

    print "Unimplemented method. Features not removed."
    return False

def getScales( conn, iid, set="slf34", field=True, rid=None, debug=False ):
    '''
    Gets a list of unique scales in the feature table for an image given
    an image id (iid).

    :param conn: connection
    :type conn: BlitzGateway connection
    :param iid: image id
    :type iid: long
    :param set: feature set name
    :type set: string
    :param field: true if field features, false otherwise
    :type field: boolean
    :param rid: region id
    :type rid: long or None
    :param debug: debug flag
    :type debug: boolean
    :rtype: list of scales
    '''
   
    if not conn.isConnected():
        raise PyslidException("Unable to connect to OMERO.server")

    try: 
        table = pyslid.features.get( conn, 'table', iid, 1, set, field )
    except Exception as e:
        raise PyslidException("Unable to retrieve feature table: %s" % e)

    if not table:
        print "Empty table. Nothing to return."
        #raise PyslidException("Empty table. Nothing to return.")
        # TODO: Is this an error condition?
        return []
    else:
        try:
           data = table.read([4],0L,table.getNumberOfRows())
           data = data.columns
           data = data.pop()

           scales = []
           for index in range(len(data.values)):
                scales.append( data.values[index] )

           scales = numpy.unique( scales )    
           return scales
        except:
           print "Empty table. Nothing to return."
           raise

def has( conn, iid, scale=None, set="slf33", field=True, rid=None, pixels=0, channel=0, zslice=0, timepoint=0, debug=False ):
    '''
    Helper method that returns true if a feature vector is found in the feature table.

    :param conn: connection
    :type conn: BlitzGateway connection
    :param iid: image id
    :type iid: long
    :param scale: image scale
    :type scale: double
    :param set: feature set name
    :type set: string
    :param field: true if field features, false otherwise
    :type field: boolean
    :param rid: region id
    :type rid: long
    :param pixels: pixel index associated with the image
    :type pixels: integer
    :param channel: channel index
    :type channel: integer
    :param zslice: zslice index
    :type zslice: integer
    :param timepoint: time point index
    :type timepoint: integer
    :param debug: debug flag
    :type debug: boolean
    :rtype: true if feature vector is found, false otherwisede
    '''

    try:
        option = 'features'
        calculate = False
        [ids,features]=pyslid.features.get( conn, option, iid, scale, set, field,rid, pixels, channel, zslice, timepoint, calculate, debug )
        return True
    except PyslidException:
        return False
    except:
        print "Unable to retrieve features"
        return False
        #raise PyslidException("Unable to retrieve features")
        # TODO: Is this an error condition?
