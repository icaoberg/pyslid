from distutils.core import setup
setup(name='pyslid',
      version='1.0.0',
      description='Protein Subcellular Location Image Database for OMERO',
      author='Ivan E. Cao-Berg, Baek-Hwan Cho, Jennifer Bakal',
      author_email='icaoberg@cmu.edu',
      maintainer='Robert F. Murphy',
      maintainer_email='murphy@cmu.edu',
      url='http://murphylab.web.cmu.edu/software/',
      py_modules=['pyslid.features', 'pyslid.utilities', 'pyslid.database.link', \
        'pyslid.image', 'pyslid.database.direct'])


