"""
Authors: Ivan E. Cao-Berg and Jennifer Bakal
Created: February 22, 2012

Copyright (C) 2012 Murphy Lab
Lane Center for Computational Biology
School of Computer Science
Carnegie Mellon University

May 4, 2012
* J. Bakal Updated

April 10, 2013
* J. Bakal Included processOMEIDs and def processOMESearchSet methods

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

import omero
from omero.gateway import BlitzGateway
import pyslid.features
import pyslid.utilities
import copy
import pickle
from os.path import exists, join
import os

NUM_DIGIT_COUNT = 20

def set_contentdb_path(contentdb_path):
    """
    Set the OMERO_CONTENTDB_PATH, used to store the ContentDB files
    """
    global OMERO_CONTENTDB_PATH

    #if contentdb_path is None:
    #    contentdb_path = os.environ['OMERO_CONTENTDB_PATH']
    if not contentdb_path.endswith(os.sep):
        contentdb_path += os.sep
    if not os.path.isdir(contentdb_path):
        # TODO: Raise PyslidException
        raise Exception('Invalid ContentDB directory: %s', contentdb_path)

    OMERO_CONTENTDB_PATH = contentdb_path


def getCurrentGroupId(conn):
    '''
    Returns the current group ID, either from SERVICE_OPTS if set or from the
    current context.
    @param connection (conn)
    @return the current group ID
    '''
    gid = conn.SERVICE_OPTS.getOmeroGroup()
    if gid is not None:
        gid = long(gid)
    else:
        gid = conn.getEventContext().groupId
    return gid

def search_file(filename, search_path):
   """Given a search path, find file
   """
   file_found = 0
   if exists(join(search_path, filename)):
        file_found = 1
   if file_found:
      return join(search_path, filename)
   else:
      return None

def initializeNameTag(conn, featureset, did=None):
    """
    Initialize a tagAnnotation for image-content DB Name and link it to the ExperimenterGroup.
    
    @param conn (Blitzgateway)
    @param featureset (featureset name)
    @param did (Dataset ID. If did is specified, this function will retrieve the partircular DB that is attached to the dataset. Otherwise it will retrieve the general DB that includes all datasets)
    @return NameSpace
    @return DBName
    """

    COUNT = ''
    for i in range(NUM_DIGIT_COUNT-1):
        COUNT +="0"
    COUNT +="1"
    gid = getCurrentGroupId(conn)
    
    if did == None: 
        NameSpace = 'direct.edu.cmu.cs.compbio.omepslid:'+'all'+'_'+str(featureset)
        DBName = str(gid)+'_all_'+str(featureset)+'_content_db_'+COUNT+'.pkl'
    else:
        NameSpace = 'direct.edu.cmu.cs.compbio.omepslid:'+str(did)+'_'+str(featureset)
        DBName = str(gid)+'_'+str(did)+'_'+str(featureset)+'_content_db_'+COUNT+'.pkl'

    #create an empty tag
    tag = conn.getUpdateService().saveAndReturnObject(
        omero.model.TagAnnotationI(), conn.SERVICE_OPTS)
    tag.setNs(omero.rtypes.RStringI(NameSpace))
    tag.setTextValue(omero.rtypes.RStringI(DBName))
    tag = conn.getUpdateService().saveAndReturnObject(
        tag, conn.SERVICE_OPTS) # update the tag
    
    flink = omero.model.ExperimenterGroupAnnotationLinkI()
    

    # link the tag to the ExperimentGroup
    flink.link(omero.model.ExperimenterGroupI(gid, False), tag)
    conn.getUpdateService().saveObject(
        flink, conn.SERVICE_OPTS)   # update the link

    return NameSpace, DBName

def updateNameTag(conn, tag, DBName_new):
    """
    Update the tag by updating DB Name. (Increase the number by 1)
    
    @param conn (Blitzgateway)
    @param tag (tagAnnotation object)
    @param DBName_new (Old DBName)
    @return Answer (True if successfully done)
    """
    

    # change the DBName
    tag.setTextValue(omero.rtypes.RStringI(DBName_new))
    # update the tag
    conn.getUpdateService().saveObject(tag, conn.SERVICE_OPTS)

    return True

def deleteNameTag(conn, featureset, did=None):
    """
    Delete all tagAnnotations and links for image-content DB Name.
    Note that only the account who created the tag/link can delete them.
    
    @param conn (Blitzgateway)
    @param featureset (featureset name)
    @param did (Dataset ID. If did is specified, this function will retrieve the partircular DB that is attached to the dataset. Otherwise it will retrieve the general DB that includes all datasets)
    @return Answer (True if successfully done)
    
    """
    groupid = getCurrentGroupId(conn)
    
    #create query service
    query = conn.getQueryService()

    if did == None: 
        NameSpace = 'direct.edu.cmu.cs.compbio.omepslid:'+'all'+'_'+str(featureset)
    else:
        NameSpace = 'direct.edu.cmu.cs.compbio.omepslid:'+str(did)+'_'+str(featureset)

    params = omero.sys.ParametersI()
    params.addString("namesp", NameSpace )
    params.addLong("gid", groupid )

    #for ExperimeterGroupANnotationLink objects
    query_string = "select grl from ExperimenterGroupAnnotationLink as grl join grl.child as ann where grl.parent.id = :gid and ann.ns=:namesp"
    results_link = query.findAllByQuery(query_string, params, conn.SERVICE_OPTS)
    #for tagAnnotation
    query_string = "select ann from ExperimenterGroupAnnotationLink as grl join grl.child as ann where grl.parent.id = :gid and ann.ns=:namesp"
    results_tag = query.findAllByQuery(query_string, params, conn.SERVICE_OPTS)

    try:
        for result in results_link:
            conn.getUpdateService().deleteObject(result, conn.SERVICE_OPTS)
        for result in results_tag:
            conn.getUpdateService().deleteObject(result, conn.SERVICE_OPTS)

        return True
    except:
        return False
    
def getRecentName(conn, featureset, did=None):
    """
    Retreive the most recent public (entire) image-content DB file name for a specific featureset.
    This function retrieves the DB file name from a tagAnnotation in the ExperimenterGroup (Collaborative).
    @param conn (Blitzgateway)
    @param featureset (featureset name)
    @param did (Dataset ID. If did is specified, this function will retrieve the partircular DB that is attached to the dataset. Otherwise it will retrieve the general DB that includes all datasets)
    @return DBName (DB file name)
    @return DBName_next (DB file name for the next round)
    @return tag (tagAnnotation)
    
    """
    groupid = getCurrentGroupId(conn)
    
    #create query service
    query = conn.getQueryService()

    if did == None: 
        NameSpace = 'direct.edu.cmu.cs.compbio.omepslid:'+'all'+'_'+str(featureset)
    else:
        NameSpace = 'direct.edu.cmu.cs.compbio.omepslid:'+str(did)+'_'+str(featureset)

    params = omero.sys.ParametersI()
    params.addString("namesp", NameSpace )
    params.addLong("gid", groupid )

    # get the most recent Tag
    query_string = "select ann from ExperimenterGroupAnnotationLink as grl join grl.child as ann where grl.parent.id = :gid and ann.ns=:namesp order by ann.id desc"
    result = query.findByQuery(
        query_string, params.page(0,1), conn.SERVICE_OPTS)

    if result is None:
        DBName = None
        DBName_next = None
    else:
        DBName = result.getTextValue().getValue()

        # get the next DBName
        COUNT_old = DBName.split('.')[0].split('_')[-1]
        COUNT_num = long(COUNT_old)
        COUNT_num += 1
        num_digit = len(str(COUNT_num))
        num_zeros = NUM_DIGIT_COUNT - num_digit

        COUNT_new = ""
        for i in range(num_zeros):
            COUNT_new +="0"
        COUNT_new += str(COUNT_num)
        DBName_next=DBName.replace(COUNT_old, COUNT_new)
    
    return DBName, DBName_next, result

def has(conn, featureset, did=None):
    """
    Check if the DB object(HDF5 file) exists on OMERO server 
    @param conn (Blitzgateway)
    @param featureset (featureset name)
    @param did (Dataset ID. If did is specified, this function will retrieve the partircular DB that is attached to the dataset. Otherwise it will retrieve the general DB that includes all datasets)
    @return answer (True if it is successful)
    @return result (Query result that points the newest DB)
    """
    answer = False        

    DBfilename, DBfilename_next, tag = getRecentName(conn, featureset, did)
    if DBfilename is None:
        return False, None

    # search the file from PATH_DB_FILES
    result = search_file(DBfilename, OMERO_CONTENTDB_PATH)

    if result is None:
        answer = False
    else:
        answer = True
    
    return answer, result

def deleteTableLink(conn, featureset, did=None):
    """
    Delete all tables and links for image-content DB Name. (Also delete the tagAnnotation that contains the filename of the table)
    Note that only the account who created the table/link can delete them.
    
    @param conn (Blitzgateway)
    @param featureset (featureset name)
    @param did (Dataset ID. If did is specified, this function will retrieve the partircular DB that is attached to the dataset. Otherwise it will retrieve the general DB that includes all datasets)
    @return Answer (True if successfully done)
    """


    params = omero.sys.ParametersI()
    mimetype = 'OMERO.tables'
    params.addString( "mimetype", mimetype );
    

    
    DBfilename, DBfilename_next, tag = getRecentName(conn, featureset, did)
    if DBfilename is None:
        return False

    result = search_file(DBfilename, OMERO_CONTENTDB_PATH)
    if result is None:
        return False
    else:
        import os
        try:
            os.remove(result)
            deleteNameTag(conn, featureset, did)
            return True
        except:
            return False

def createColumns(feature_ids):
    """
    Create a List variable (Columns) for content DB.
    Note that the first 6 columns are fixed as 'INDEX', 'iid', 'pixels', 'channel', 'zslice', 'timepoint'.
    Then the next columns are assigned by the input 'feature_ids'
    
    @param feature_ids (Feature name array. The length of this argument should match with the number of features)
    @return columns 
    """
    columns = []
    columns.append(omero.grid.LongColumn( 'INDEX', 'Data Index', [] ))
    columns.append(omero.grid.StringColumn( 'server', 'Server name', long(256),[]))
    columns.append(omero.grid.StringColumn( 'username', 'Owner ID of the data', long(256), []))
    columns.append(omero.grid.LongColumn( 'iid', 'Image ID', [] ))
    columns.append(omero.grid.LongColumn( 'pixels', 'Pixel Index', [] ))
    columns.append(omero.grid.LongColumn( 'channel', 'Channel Index', [] ))
    columns.append(omero.grid.LongColumn( 'zslice', 'zSlice Index', [] ))
    columns.append(omero.grid.LongColumn( 'timepoint', 'Time Point Index', [] ))

    for feat_id in feature_ids:
        columns.append(omero.grid.DoubleColumn( str(feat_id), str(feat_id), [] ))

    return columns
    
def initialize(conn, feature_ids, featureset, did=None): 
    """
    Initialize a DB object(HDF5 file) onto OMERO server (without attaching to anything)
    @param conn (Blitzgateway)
    @param feature_ids (Feature name array. The length of this argument should match with the number of features)
    @param featureset (Featureset name.)
    @param did (Dataset ID. If did is specified, this function will initialize the partircular DB of the dataset. Otherwise it will be for all images)
    @return answer (True if it is successful)
    """
    answer, result = has(conn, featureset, did)

    if answer == True:
        # delete the old one
        deleteTableLink(conn, featureset, did)

    try:
        #columns = createColumns(feature_ids)

        NS, DBfilename = initializeNameTag(conn, featureset, did)

        fullpath = OMERO_CONTENTDB_PATH + DBfilename
        output = open(fullpath, 'wb')

        Data={'info': featureset}
        pickle.dump(Data, output)
        output.close()
            
        return True
    except:
        return False
    
def updatePerDataset(conn, server, username, dataset_id_list, featureset, field=True, did=None):
    """
    Update the DB for given dataset list. Firstly retrieve OMERO.tables from each image in the dataset and add the data onto the DB.
    @param conn (Blitzgateway)
    @param server (server name)
    @param username (user name)
    @param dataset_id_list (list of dataset ids)
    @param featureset (featureset name)
    @param field (True if the featureset is for field-level features)
    @param did (Dataset ID. If did is specified, this function will retrieve the partircular DB that is attached to the dataset. Otherwise it will retrieve the general DB that includes all datasets)
    @return answer (True if it is successfuly saved)
    @return Message (Error Message)
    """ 
    # check the existence of the DB with DBfilename
    answer, result = has(conn, featureset, did)

    if answer is False:
        feature_ids = pyslid.features.getIds(featureset)
        initialize(conn, feature_ids, featureset, did)
        answer, result = has(conn, featureset, did)

    if answer is True:
        # update image by image
        for DID in dataset_id_list:
            print 'starting dataset: '+str(DID)
            ds = conn.getObject("Dataset", long(DID))
            img_gen = ds.getChildLinks()


            IID = []
            PIXELS = []
            CHANNEL = []
            ZSLICE = []
            TIMEPOINT = []
            FEATURE_IDS =''
            features_array = []
            for im in img_gen:
                iid = long(im.getId())
                
                print iid
                answer2, result =pyslid.features.hasTable(conn, iid, featureset, field)
                if answer2:
                    scales=pyslid.features.getScales(conn, iid, featureset, field)
                    scale=scales[0]
#                    scale=0.645
                    [ids, feats] = pyslid.features.get(conn, 'vector', iid, scale, featureset, field)
                    if len(ids) == 0:
                        print str(iid)+' has wrong table'
                    else:
                        IID.append(long(iid))
                        for feat in feats:
                            PIXELS.append(long(feat[0]))
                            CHANNEL.append(long(feat[1]))
                            ZSLICE.append(long(feat[2]))
                            TIMEPOINT.append(long(feat[3]))
                            FEATURE_IDS = list(ids[5:])
                            features_array.append(list(feat[5:]))


            updateDataset(conn, server, username, IID, PIXELS, CHANNEL, ZSLICE, TIMEPOINT, FEATURE_IDS, features_array, featureset, did)

        return True
    else:
        return False

    
def update(conn, server, username, scale,
           iid, pixels, channel, zslice, timepoint,
           feature_ids, features, featureset, did=None):
    """
    Update the DB for a feature vector.
    @param conn (Blitzgateway)
    @param server (server name)
    @param username (user name)
    @param scale (image feature scale parameter)
    @param iid (image id)
    @param pixels (pixels index)
    @param channel (channel index)
    @param zslice (zslice index)
    @param timepoint (timpoint index)
    @param featre_ids (id list for features)
    @param features (feature vector)
    @param featureset (featureset name)
    @param did (Dataset ID. If did is specified, this function will retrieve the partircular DB that is attached to the dataset. Otherwise it will retrieve the general DB that includes all datasets)
    @return answer (True if it is successfuly saved)
    @return Message (Error Message)
    """

    # check the existence of the DB with DBfilename
    answer, result = has(conn, featureset, did)

    if answer is False:
        initialize(conn, feature_ids, featureset, did)
        answer, result = has(conn, featureset, did)
    

    if answer == True:
        # result is the absolute path of the DB file
        pkl_file = open(result, 'rb')
        Data = pickle.load(pkl_file)
        pkl_file.close()

        if scale not in Data:
            Data[scale] = []
        num_data = len(Data[scale])


        # 1. get the DB file name and tag
        DBfilename_old, DBfilename_new, tag = getRecentName(conn, featureset, did)


        # 2. update the table2 with new input data
        IND = num_data + 1
        tup = []
        tup.append( long(IND) )   #INDEX
        tup.append( str(server) )
        tup.append( str(username) )
        tup.append( str(server)+'/webclient/metadata_details/image/'+str(iid))
        tup.append( str(server)+'/webclient/?show=image-' + str(iid))
        tup.append( str(server)+'/webclient/img_detail/' + str(iid))
        tup.append( long(iid ) )
        tup.append( long(pixels) )
        tup.append( long(channel) ) 
        tup.append( long(zslice) )  
        tup.append( long(timepoint) )
        for j in range(9, len(feature_ids)+9):
           tup.append( float(features[j-9]) )

        Data[scale].append(tup)

        # 3. save it with the new DB file name
        fullpath = OMERO_CONTENTDB_PATH + DBfilename_new
        output = open(fullpath, 'wb')
        pickle.dump(Data, output)
        output.close()

        # 4. up date the tag with a new file name
        Answer = updateNameTag(conn, tag, DBfilename_new)

        # 5. delete the previous one
        import os
        try:
            os.remove(result)
        except:
            return False, "Couldn't remove the previous contentDB file"

        Message = "Good"
        return True, Message
        
    else:
        Message = "There is no table for the featureset"
        return False, Message
    

def updateDataset(conn, server, username, scale,
           iid, pixels, channel, zslice, timepoint,
           feature_ids, features, featureset, did=None):
    """
    Update the DB for a feature vector array (for a dataset).
    @param conn (Blitzgateway)
    @param server (server name)
    @param username (user name)
    @param scale (image feature scale parameter)
    @param iid (image id array)
    @param pixels (pixels index array)
    @param channel (channel index array)
    @param zslice (zslice index array)
    @param timepoint (timpoint index array)
    @param feature_ids (id list for features)
    @param features (feature vector array)
    @param featureset (featureset name array)
    @param did (Dataset ID. If did is specified, this function will retrieve the partircular DB that is attached to the dataset. Otherwise it will retrieve the general DB that includes all datasets)
    @return answer (True if it is successfuly saved)
    @return Message (Error Message)
    """

    # check the existence of the DB with DBfilename
    answer, result = has(conn, featureset, did)

    if answer is False:
        initialize(conn, feature_ids, featureset, did)
        answer, result = has(conn, featureset, did)
    

    if answer == True:
        # result is the absolute path of the DB file
        pkl_file = open(result, 'rb')
        Data = pickle.load(pkl_file)
        pkl_file.close()

        if scale not in Data:
            Data[scale] = []
        num_data = len(Data[scale])
        

        # 1. get the DB file name and tag
        DBfilename_old, DBfilename_new, tag = getRecentName(conn, featureset, did)
        

        # 2. update the table2 with new input data
        num_rows = len(iid)
        for i in range(num_rows):
            IND = num_data + i + 1
            tup=[] # tuple (one row)
            tup.append( long(IND) )   #INDEX
            tup.append( str(server) )
            tup.append( str(username) )
            tup.append( str(server)+'/webclient/metadata_details/image/'+str(iid[i]))
            tup.append( str(server)+'/webclient/?show=image-' + str(iid[i]))
            tup.append( str(server)+'/webclient/img_detail/' + str(iid[i]))
            tup.append( long(iid[i]) )   
            tup.append( long(pixels[i]) )
            tup.append( long(channel[i]) ) 
            tup.append( long(zslice[i]) )  
            tup.append( long(timepoint[i]) )
            for j in range(9, len(feature_ids)+9):
               tup.append( float(features[i][j-9]) )

            Data[scale].append(tup)

        # 3. save it with the new DB file name
        fullpath = OMERO_CONTENTDB_PATH + DBfilename_new
        output = open(fullpath, 'wb')
        pickle.dump(Data, output)
        output.close()

        # 4. update the tag with a new file name
        Answer = updateNameTag(conn, tag, DBfilename_new)

        # 5. delete the previous one
        import os
        try:
            os.remove(result)
        except:
            return False, "Couldn't remove the previous contentDB file"
        
        Message = "Good"
        return True, Message
        
    else:
        Message = "There is no table for the featureset"
        return False, Message
    

def chunks(l, n):
    '''
	Get a chunk of data (Internal function)
    '''
    return [l[i:i+n] for i in range(0, len(l), n)]

def retrieve(conn, featureset, did=None):
    """
    Retrieve a DB object(HDF5 file) from OMERO server
    This function is using omero.client object. Thus this function cannot be called from OMERO.web directly.
    Also, this function splits the table-reading process for fast reading (from OMERO 4.3.3)
    @param conn (Blitzgateway)
    @param featureset (featureset name)
    @param did (Dataset ID. If did is specified, this function will retrieve the partircular DB that is attached to the dataset. Otherwise it will retrieve the general DB that includes all datasets
    @return data (list of data lists) [ [IND,server,username,iid,pixels,channel,zslice,timepoint,...],
                                        [IND,server,username,iid,pixels,channel,zslice,timepoint,...],
                                        [IND,server,username,iid,pixels,channel,zslice,timepoint,...],
                                        ...]
    @return Message (Error Message)
    """
    
    Data = []
    answer, result = has(conn, featureset, did)
    if answer == True:
        # result is the absolute path of the DB file
        pkl_file = open(result, 'rb')
        Data = pickle.load(pkl_file)
        pkl_file.close()
        Message = "Good"
    else:
        Message = "There is no table for the featureset"

    return Data, Message

def retrieveRemote(conn_local, conn_remote, featureset, did=None):
    """
    Retrieve a DB object(HDF5 file) from remote OMERO server
    Also, this function splits the table-reading process for fast reading (from OMERO 4.3.3)
    @param conn (Blitzgateway)
    @param featureset (featureset name)
    @param did (Dataset ID. If did is specified, this function will retrieve the partircular DB that is attached to the dataset. Otherwise it will retrieve the general DB that includes all datasets
    @return data (list of data lists) [ [IND,server,username,iid,pixels,channel,zslice,timepoint,...],
                                        [IND,server,username,iid,pixels,channel,zslice,timepoint,...],
                                        [IND,server,username,iid,pixels,channel,zslice,timepoint,...],
                                        ...]
    @return Message (Error Message)
    """
    
    data = []
    
    try:
        answer, result = has(conn_remote, featureset, did)
        if answer == True:
            fid = result.getId().getValue()            
            table = conn.getSharedResources().openTable( omero.model.OriginalFileI( fid, False ) )

            num_col = len(table.getHeaders())
            num_row = table.getNumberOfRows()

            chunk_col = chunks(range(num_col), 100) # read every 100 columns
            chunk_row = chunks(range(num_row), 1000) # read every 1000 columns
            
            data = []
            for row in range(len(chunk_row)):
                temp_col = []
                for col in range(len(chunk_col)):
                    values = table.read(chunk_col[col], chunk_row[row][0], chunk_row[row][-1]+1)
                    values = values.columns
                    for cols in values:
                        column_value_list = cols.values
                        temp_col.append(list(column_value_list))
                temp_col = zip(*temp_col)
                for r in temp_col:
                    data.append(r)

            table.close()
            Message = "Good"
        else:
            Message = "There is no table for the featureset"
    except:
        Message = "Not Done Correctly"

    return data, Message

def processOMEIDs(cdb_row):
     '''
     Process content database id
     '''
     
     info=cdb_row[6:11]
     ID = ''.join([str(tmp)+'.' for tmp in info])[:-1]
     cdbID = [ID,cdb_row[2],cdb_row[1]] 
     return cdbID
     
def processOMESearchSet(contentDB,image_refs_dict,dscale):
     '''
     Create dict with iids as keys and contentDB feature vector as value 
     to use instead of retrieving features from omero (too slow)
     '''
     iid_contentDB_dict={}
     for key in contentDB[dscale]:
         iid_contentDB_dict[key[6]]=key

     goodSet_pos = []
     for ID in image_refs_dict:
         items = ID.split('.')
         iid = long(items[0])
         pixels = long(items[1])
         channel = long(items[2])
         zslice = long(items[3])
         timepoint = long(items[4])
         rid=[]
         field=True

         if iid_contentDB_dict.has_key(iid):
             feats=iid_contentDB_dict[iid][11:]
             goodSet_pos.append([ID, 1, feats])
         else:
             return []

     return goodSet_pos


def removeDuplicates(conn, scale, featureset, did=None):
    """
    Remove duplicate entries in a content DB. The most recent of any duplicate
    entries is kept, but the overall ordering of entries is unspecified.
    @param conn (Blitzgateway)
    @param scale (image feature scale parameter)
    @param featureset (featureset name)
    @param did (Dataset ID. If did is specified, this function will retrieve
    the particular DB that is attached to the dataset. Otherwise it will
    retrieve the general DB that includes all datasets.
    @return answer (True if it is successfuly saved)
    @return Message (Error Message)
    """

    # check the existence of the DB with DBfilename
    answer, result = has(conn, featureset, did)

    if answer is False:
        Message = "There is no table for the featureset"
        return False, Message

    # result is the absolute path of the DB file
    pkl_file = open(result, 'rb')
    Data = pickle.load(pkl_file)
    pkl_file.close()

    if scale not in Data:
        Message = "No entries for the request scale"
        return False, Message


    # 1. get the DB file name and tag
    DBfilename_old, DBfilename_new, tag = getRecentName(conn, featureset, did)

    # 2. Remove duplicates, keeping the latest
    uniqueRows = {}
    for d in Data[scale]:
        # 0:IND 1:server 2:username 3:metadata 4:image 5:render,
        #   6:iid 7:pixels 8:channel 9:zslice 10:timepoint 11:features ....
        k = tuple([d[1]] + d[4:11])
        uniqueRows[k] = d

    # Should be unique, so order doesn't matter
    uniqueData = uniqueRows.values()
    for n in xrange(len(uniqueData)):
        uniqueData[n][0] = n + 1

    Data[scale] = uniqueData

    # 3. save it with the new DB file name
    fullpath = OMERO_CONTENTDB_PATH + DBfilename_new
    output = open(fullpath, 'wb')
    pickle.dump(Data, output)
    output.close()

    # 4. update the tag with a new file name
    Answer = updateNameTag(conn, tag, DBfilename_new)

    # 5. delete the previous one
    try:
        os.remove(result)
    except:
        return False, "Couldn't remove the previous contentDB file"

    Message = "Good"
    return True, Message

