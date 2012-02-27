"""
Authors: Ivan E. Cao-Berg (icaoberg@scs.cmu.edu)
Created: February 22, 2012

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
"""

import omero
from omero.gateway import BlitzGateway
import pyslid.features
import pyslid.utilities
import copy

NUM_DIGIT_COUNT = 20

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
    gid = conn.getGroupFromContext().getId()
    if did == None: 
        NameSpace = 'edu.cmu.cs.compbio.omepslid:'+'all'+'_'+str(featureset)
        DBName = str(gid)+'_all_'+str(featureset)+'_content_db_'+COUNT+'.h5'
    else:
        NameSpace = 'edu.cmu.cs.compbio.omepslid:'+str(did)+'_'+str(featureset)
        DBName = str(gid)+'_'+str(did)+'_'+str(featureset)+'_content_db_'+COUNT+'.h5'

    #create an empty tag
    tag = conn.getUpdateService().saveAndReturnObject(omero.model.TagAnnotationI())
    tag.setNs(omero.rtypes.RStringI(NameSpace))
    tag.setTextValue(omero.rtypes.RStringI(DBName))
    tag=conn.getUpdateService().saveAndReturnObject(tag) # update the tag
    
    flink = omero.model.ExperimenterGroupAnnotationLinkI()
    

    # link the tag to the ExperimentGroup
    flink.link(omero.model.ExperimenterGroupI(gid, False), tag)
    conn.getUpdateService().saveObject(flink)   # update the link

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
    conn.getUpdateService().saveObject(tag)

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
    #get the name of the active group to which the user belongs
    groupname = conn.getGroupFromContext().getName()
    groupid = conn.getGroupFromContext().getId()
    
    #create query service
    query = conn.getQueryService()

    if did == None: 
        NameSpace = 'edu.cmu.cs.compbio.omepslid:'+'all'+'_'+str(featureset)
    else:
        NameSpace = 'edu.cmu.cs.compbio.omepslid:'+str(did)+'_'+str(featureset)

    params = omero.sys.ParametersI()
    params.addString("namesp", NameSpace )
    params.addLong("gid", groupid )

    #for ExperimeterGroupANnotationLink objects
    query_string = "select grl from ExperimenterGroupAnnotationLink as grl join grl.child as ann where grl.parent.id = :gid and ann.ns=:namesp"
    results_link = query.findAllByQuery(query_string, params)
    #for tagAnnotation
    query_string = "select ann from ExperimenterGroupAnnotationLink as grl join grl.child as ann where grl.parent.id = :gid and ann.ns=:namesp"
    results_tag = query.findAllByQuery(query_string, params)

    try:
        for result in results_link:
            conn.getUpdateService().deleteObject(result)
        for result in results_tag:
            conn.getUpdateService().deleteObject(result)

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
    #get the name of the active group to which the user belongs
    groupname = conn.getGroupFromContext().getName()
    groupid = conn.getGroupFromContext().getId()
    
    #create query service
    query = conn.getQueryService()

    if did == None: 
        NameSpace = 'edu.cmu.cs.compbio.omepslid:'+'all'+'_'+str(featureset)
    else:
        NameSpace = 'edu.cmu.cs.compbio.omepslid:'+str(did)+'_'+str(featureset)

    params = omero.sys.ParametersI()
    params.addString("namesp", NameSpace )
    params.addLong("gid", groupid )

    # get the most recent Tag
    query_string = "select ann from ExperimenterGroupAnnotationLink as grl join grl.child as ann where grl.parent.id = :gid and ann.ns=:namesp order by ann.id desc"
    result = query.findByQuery(query_string, params.page(0,1))

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
    
    # search the file by name and mimetype
    params = omero.sys.ParametersI()
    
    if did is None:
        query_string = "select f from OriginalFile f where f.name=:filename and f.mimetype=:mimetype order by f.id desc"
    else:
        # for a DB for a specific dataset (the DB file is attached to that dataset)
        params.addLong("did",did);
        query_string = "select f from DatasetAnnotationLink as dsl join dsl.child as fileAnn "+ \
               "join fileAnn.file as f join dsl.parent as ds where ds.id = :did and f.name=:filename and f.mimetype=:mimetype "+\
               "order by f.id desc"
    
    mimetype = 'OMERO.tables'
    params.addString( "mimetype", mimetype );
    params.addString( "filename", DBfilename );

    #params2 = copy.deepcopy(params) # this is deprecated
    result = conn.getQueryService().findByQuery(query_string,params.page(0,1))
    #results = conn.getQueryService().findByQuery(query_string,params2) # this is deprecated
    #@return results (All the Query results that points the all DB with the same name)

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
    

    # search the file by name, mimetype, and dataset id (if any)
    DBfilename, DBfilename_next, tag = getRecentName(conn, featureset, did)
    params.addString( "filename", DBfilename );
    if did == None:
        query_string = "select f from OriginalFile f where f.name=:filename and f.mimetype=:mimetype order by f.id desc"
        results_db_file = conn.getQueryService().findAllByQuery(query_string, params)
        for result in results_db_file:
            try:    # if the DB is not owned by the current user, it might fail
                conn.getUpdateService().deleteObject(result)
            except:
                return False
    else:
        # for a DB for a specific dataset (the DB file is attached to that dataset)
        params.addLong("did",did);
        # delete DatasetAnnotationLink
        query_string = "select dsl from DatasetAnnotationLink as dsl join dsl.child as fileAnn "+ \
               "join fileAnn.file as f join dsl.parent as ds where ds.id = :did and f.name=:filename and f.mimetype=:mimetype "+\
               "order by f.id desc"
        results_link = conn.getQueryService().findAllByQuery(query_string, params)
        for result in results_link:
            try:
                conn.getUpdateService().deleteObject(result)
            except:
                return False
        # delete FileAnnotation and File
        query_string = "select fileAnn from DatasetAnnotationLink as dsl join dsl.child as fileAnn "+ \
               "join fileAnn.file as f join dsl.parent as ds where ds.id = :did and f.name=:filename and f.mimetype=:mimetype "+\
               "order by f.id desc"
        results_file_ann = conn.getQueryService().findAllByQuery(query_string, params)
        for result in results_file_ann:
            try:    # if the DB is not owned by the current user, it might fail
                conn.getUpdateService().deleteObject(result)
                conn.getUpdateService().deleteObject(result.file)
            except:
                return False

    # delete the tagAnnotation
    deleteNameTag(conn, featureset)
    return True        

def createColumns(feature_ids):
    '''
    Create a List variable (Columns) for content DB.
    Note that the first 6 columns are fixed as 'INDEX', 'iid', 'pixels', 'channel', 'zslice', 'timepoint'.
    Then the next columns are assigned by the input 'feature_ids'
    
    @param feature_ids (Feature name array. The length of this argument should match with the number of features)
    @return columns 
    '''

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

    # check the existence of the DB with DBfilename
    # if it exists, it will overwrite when overwrite flag is True. Otherwise it will do nothing
    answer, result = has(conn, featureset, did)

    if answer == True:
        # delete the old one
        deleteTableLink(conn, featureset, did)

    try:
        columns = createColumns(feature_ids)

        NS, DBfilename = initializeNameTag(conn, featureset, did)
        table = conn.getSharedResources().newTable( 1, DBfilename )
        table.initialize(columns)

        if did == None: # if it is for all data, the table is not attached to anything
            orig_file = table.getOriginalFile()
            table.close()
        else:   # if a dataset ID is specified, then the table is attached to it
            flink = omero.model.DatasetAnnotationLinkI()
            annotation = omero.model.FileAnnotationI()
            annotation.file = table.getOriginalFile()
            flink.link( omero.model.DatasetI(did, False), annotation )
            conn.getUpdateService().saveObject(flink)
            table.close()
            
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
                answer2, result =pyslid.features.has(conn, iid, featureset, field)
                if answer2:
                    [ids, feats] = pyslid.features.get(conn, 'vector', iid, featureset, field)
                    if len(ids) == 0:
                        print str(iid)+' has wrong table'
                    else:
                        IID.append(long(iid))
                        for feat in feats:
                            PIXELS.append(long(feat[0]))
                            CHANNEL.append(long(feat[1]))
                            ZSLICE.append(long(feat[2]))
                            TIMEPOINT.append(long(feat[3]))
                            FEATURE_IDS = list(ids[4:])
                            features_array.append(list(feat[4:]))


            updateDataset(conn, server, username, IID, PIXELS, CHANNEL, ZSLICE, TIMEPOINT, FEATURE_IDS, features_array, featureset, did)

        return True
    else:
        return False
 
def update(conn, server, username, iid, pixels, channel, zslice, timepoint, feature_ids, features, featureset, did=None): 
    """
    Update the DB for a feature vector.
    @param conn (Blitzgateway)
    @param server (server name)
    @param username (user name)
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
        fid = result.getId().getValue()            
        table = conn.getSharedResources().openTable( omero.model.OriginalFileI( fid, False ) )
        num_data = table.getNumberOfRows()

        # if this is for a public dataset (when did is None), it creates a new table with additional data
        if did == None:
            # 1. get the DB file name and tag
            DBfilename_old, DBfilename_new, tag = getRecentName(conn, featureset, did)
            

            # 2. create a new table by new name
            columns = createColumns(feature_ids)
            
            table2 = conn.getSharedResources().newTable( 1, DBfilename_new )
            table2.initialize(columns)

            # 3. copy table to table2
            
            values = table.read(range(len(table.getHeaders())),0,table.getNumberOfRows())
            values = values.columns
            table2.addData(values)

            # 4. update the table2 with new input data
            IND = num_data + 1
            columns[0].values.append( long(IND) )   #INDEX
            columns[1].values.append( str(server) )
            columns[2].values.append( str(username) )   
            columns[3].values.append( long(iid) )   
            columns[4].values.append( long(pixels) )
            columns[5].values.append( long(channel) ) 
            columns[6].values.append( long(zslice) )  
            columns[7].values.append( long(timepoint) )
            for i in range(8, len(feature_ids)+8):
                columns[i].values.append( float(features[i-8]) ) 

            table2.addData(columns)

            orig_file = table2.getOriginalFile()
            table2.close()
            table.close()
            # 5.up date the tag with a new file name
            Answer = updateNameTag(conn, tag, DBfilename_new)

            #6. delete the previous table
            try:
                conn.getUpdateService().deleteObject(result)
                Message = "Good"
            except:
                Message = "Updated, but could not deleted the previous one"
            
            return True, Message

        else: # if this is for a specific dataset, it just updates the table (assuming the table belongs to the current user)
            columns = createColumns(feature_ids)

            IND = num_data + 1
            columns[0].values.append( long(IND) )   #INDEX
            columns[1].values.append( str(server) )
            columns[2].values.append( str(username) )   
            columns[3].values.append( long(iid) )   
            columns[4].values.append( long(pixels) )
            columns[5].values.append( long(channel) ) 
            columns[6].values.append( long(zslice) )  
            columns[7].values.append( long(timepoint) )
            for i in range(8, len(feature_ids)+8):
                columns[i].values.append( float(features[i-8]) ) 

            table.addData(columns)
            table.close()
            Message = "Good"
            return True, Message
        
    else:
        Message = "There is no table for the featureset"
        return False, Message

def updateDataset(conn, server, username, iid, pixels, channel, zslice, timepoint, feature_ids, features, featureset, did=None): 
    """
    Update the DB for a feature vector array (for a dataset).
    @param conn (Blitzgateway)
    @param server (server name)
    @param username (user name)
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
        fid = result.getId().getValue()            
        table = conn.getSharedResources().openTable( omero.model.OriginalFileI( fid, False ) )
        num_data = table.getNumberOfRows()

        # if this is for a public dataset (when did is None), it creates a new table with additional data
        if did == None:
            # 1. get the DB file name and tag
            DBfilename_old, DBfilename_new, tag = getRecentName(conn, featureset, did)
            

            # 2. create a new table by new name
            columns = createColumns(feature_ids)
            
            table2 = conn.getSharedResources().newTable( 1, DBfilename_new )
            table2.initialize(columns)

            # 3. copy table to table2
            
            values = table.read(range(len(table.getHeaders())),0,table.getNumberOfRows())
            values = values.columns
            table2.addData(values)

            # 4. update the table2 with new input data
            num_rows = len(iid)
            for i in range(num_rows):
                IND = num_data + i + 1
                columns[0].values.append( long(IND) )   #INDEX
                columns[1].values.append( str(server) )
                columns[2].values.append( str(username) )
                columns[3].values.append( long(iid[i]) )   
                columns[4].values.append( long(pixels[i]) )
                columns[5].values.append( long(channel[i]) ) 
                columns[6].values.append( long(zslice[i]) )  
                columns[7].values.append( long(timepoint[i]) )
                for j in range(8, len(feature_ids)+8):
                    columns[j].values.append( float(features[i][j-8]) ) 

            table2.addData(columns)

            

            orig_file = table2.getOriginalFile()
            table2.close()
            table.close()
            # 5.up date the tag with a new file name
            Answer = updateNameTag(conn, tag, DBfilename_new)

            #6. delete the previous table
            try:
                conn.getUpdateService().deleteObject(result)
                Message = "Good"
            except:
                Message = "Updated, but could not deleted the previous one"
            
            return True, Message

        else: # if this is for a specific dataset, it just updates the table (assuming the table belongs to the current user)
            columns = createColumns(feature_ids)


            num_rows = len(iid)
            for i in range(num_rows):
                IND = num_data + i + 1
                columns[0].values.append( long(IND) )   #INDEX
                columns[1].values.append( str(server) )
                columns[2].values.append( str(username) )
                columns[3].values.append( long(iid[i]) )   
                columns[4].values.append( long(pixels[i]) )
                columns[5].values.append( long(channel[i]) ) 
                columns[6].values.append( long(zslice[i]) )  
                columns[7].values.append( long(timepoint[i]) )
                for j in range(8, len(feature_ids)+8):
                    columns[j].values.append( float(features[i][j-8]) ) 

            table.addData(columns)
            table.close()
            Message = "Good"
            return True, Message
        
    else:
        Message = "There is no table for the featureset"
        return False, Message

def chunks(l, n):
    '''
	Helper method.
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
    
    data = []
    answer, result = has(conn, featureset, did)
    if answer == True:
        fid = result.getId().getValue()            
        table = conn.getSharedResources().openTable( omero.model.OriginalFileI( fid, False ) )

        num_col = len(table.getHeaders())
        num_row = table.getNumberOfRows()

        chunk_col = chunks(range(num_col), 100) # read every 50 columns
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
        

    return data, Message

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
        answer, result = has(conn, featureset, did)
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

