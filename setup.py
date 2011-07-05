# Author: Ivan E. Cao-Berg (icaoberg@scs.cmu.edu)
# Created: January 15, 2011
# Updated: July 3, 2011
#
# Copyright (C) 2011 Murphy Lab
# Lane Center for Computational Biology
# School of Computer Science
# Carnegie Mellon University
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published
# by the Free Software Foundation; either version 2 of the License,
# or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301, USA.
#
# For additional information visit http://murphylab.web.cmu.edu or
# send email to murphy@cmu.edu

from distutils.core import setup
setup(name='pslid',
      version='0.1',
      py_modules=['pslid.features', 'pslid.utilities']
      install_requires=['numpy','scipy','omero','milk','matplotlib','mahotas','pyslic'])
      
