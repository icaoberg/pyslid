from setuptools import setup

setup(name='pyslid',
      version='0.0.2',
      description='Protein Subcellular Location Image Database for OMERO',
      author='Ivan E. Cao-Berg',
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


