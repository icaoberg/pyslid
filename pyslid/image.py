'''
Authors: Ivan E. Cao-Berg (icaoberg@scs.cmu.edu)
Created: April 24, 2012

Copyright (C) 2012 Murphy Lab
Lane Center for Computational Biology
School of Computer Science
Carnegie Mellon University

April 24, 2012
* I. Cao-Berg Added getNominalMagnification method that queries OMERO and
    tries to retrieve the nomimal magnification associated with an image.
    If the result is empty, then it returns the DEFAULT_MAGNIFICATION
* I. Cao-Berg Added getResolution method that gets the pixel size in [x,y,z]
* I. Cao-Berg Added getScale method that calculate the image scale

May 2, 2012
* I. Cao-Berg Added method for retrieving a list of image ids for the current user

try:
   query = conn.getQueryService()
   me = conn.getAdminService().getEventContext().userId
   string = "select i.id from Image i where i.details.owner.id = :id"
   params = omero.sys.ParametersI().addId(me)
   iids = omero.rtypes.unwrap(query.projection(string,params))
   return iids
except:
   return []

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
from utilities import PyslidException
import omero.util.script_utils as utils
from omero.rtypes import *
from omero.gateway import BlitzGateway

def getNomimalMagnification( conn, iid, debug=False ):
    '''
    Gets the nomimal magnification associated with an image given an image id (iid). If
    the query is empty (meaning the field containing the nomimal magnification was empty), 
    then this method will return the value of DEFAULT_MAGNIFICATION. The out of the box value
    of DEFAULT_MAGNIFICATION is set to 40, which corresponds to the 3D Hela dataset from 
    the Murphy Lab.

    If the method is unable to connect to the OMERO.server, then the method will return None.
    If the method doesn't find an image associated with the given image id (iid), then the 
    method will return None.

    For detailed outputs, set debug flag to True.

    @param connection
    @param image id (iid)
    @param debug
    @return nominal magnification
    '''

    DEFAULT_MAGNIFICATION = 40
       
    if not conn.isConnected():
        raise PyslidException("Unable to connect to OMERO.server")

    if not pyslid.utilities.hasImage( conn, iid ):
        raise PyslidException("No image found with the give image id")

    #create and populate parameter
    params = omero.sys.ParametersI()
    params.addLong( "iid", iid )

    #hql string query
    string = "select i from Image i join fetch i.objectiveSettings as objS join fetch objS.objective as ob where i.id=:iid"

    #database query
    query = conn.getQueryService()

    try:
        result = query.findByQuery(string, params.page(0,1), conn.SERVICE_OPTS)
    except:
        raise PyslidException("Unable to run query")

    if not result:
        if debug:
            print "Query was empty. Setting magnification to default value"
        return DEFAULT_MAGNIFICATION
    else:
        return result

def getResolution( conn, iid, debug=False ):
    '''
    Gets the image resolution.

    If the method is unable to connect to the OMERO.server, then the method will return None.
    If the method doesn't find an image associated with the given image id (iid), then the
    method will return None.

    For detailed outputs, set debug flag to True.

    @param connection
    @param image id (iid)
    @param debug flag
    @return resolution
    '''

    if not conn.isConnected():
        raise PyslidException("Unable to connect to OMERO.server")

    if not pyslid.utilities.hasImage( conn, iid ):
        raise PyslidException("No image found with the give image id")

    img = pyslid.utilities.getImage( conn, iid )
    resolution = [ img.getPixelSizeX(), img.getPixelSizeY(), img.getPixelSizeZ() ]
    
    return resolution

def getScale( conn, iid, debug=False ):
    '''
    Get image scale. Image scale is defined as resolution over nominal magnification.

    If the method is unable to connect to the OMERO.server, then the method will return None.
    If the method doesn't find an image associated with the given image id (iid), then the
    method will return None.

    For detailed outputs, set debug flag to True.

    @param connection
    @param image id (iid)
    @param debug flag
    '''

    if not conn.isConnected():
        raise PyslidException("Unable to connect to OMERO.server")

    if not pyslid.utilities.hasImage( conn, iid ):
        raise PyslidException("No image found with the give image id")

    try:
       resolution = pyslid.image.getResolution( conn, iid )
       #magnification = pyslid.image.getNomimalMagnification( conn, iid )
       magnification = 1.0
       print 'Ignoring magnification, setting to %f' % magnification
       scale = [resolution[0]/magnification, resolution[1]/magnification, resolution[2]/magnification]
    except:
        raise PyslidException("Unable to calculate scale")

    return scale

def getList( conn, debug=False ):
   '''
   Returns a list of image ids (iids) from images owned by the user making the connection.
   @param conn
   @returns image ids (iids) list
   '''
   if not conn.isConnected():
       raise PyslidException("Unable to connect to OMERO.server")

   try:
      query = conn.getQueryService()
      me = conn.getAdminService().getEventContext().userId
      string = "select i.id from Image i where i.details.owner.id = :id"
      params = omero.sys.ParametersI().addId(me)
      iids = omero.rtypes.unwrap(query.projection(
              string, params, conn.SERVICE_OPTS))
      return iids 
   except:
       raise PyslidException("Unable to run query")
