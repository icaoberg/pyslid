# Author: Ivan E. Cao-Berg (icaoberg@scs.cmu.edu)
#
# Copyright (C) 2011-2014 Murphy Lab
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

#load the current version number of the package
exec(compile(open('VERSION').read(),'VERSION', 'exec'))

from setuptools import setup

setup(name='pyslid',
      version=__version__,
      description='Protein Subcellular Location Image Database for OMERO',
      author='Ivan Cao-Berg, Jennifer Bakal, Baek Hwan Cho and Robert F. Murphy',
      author_email='icaoberg@cmu.edu',
      maintainer='Robert F. Murphy',
      maintainer_email='murphy@cmu.edu',
      url='http://murphylab.web.cmu.edu/software/',
      py_modules=[
        'pyslid.features',
        'pyslid.utilities',
        'pyslid.database.link',
        'pyslid.image',
        'pyslid.database.direct',
        'pyslid.table',
        ],
      install_requires = [
        # pip install numpy and scipy just doesn't work, so make sure you
        # manually install them first
        'numpy>=1.4.1',
        'scipy>=0.7.2',
        # Note: mahotas requires the freeimage library
        'mahotas==0.9.4',
        'milk==0.4.3',
        'pymorph==0.96',
        'pyslic==0.6.1',
        ],
)
