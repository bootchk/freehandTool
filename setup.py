#!/usr/bin/env python

from distutils.core import setup

setup(name='freehandTool',
      version='0.1',
      description='User interface tool for drawing freehand curves (vector graphic sequence of bezier curves.) ',
      author='Lloyd Konneker',
      author_email='bootch@nc.rr.com',
      url='https://github.com/bootchk/freehandTool',
      packages=['freehandTool',
                'freehandTool.generator',
                'freehandTool.generator.turnDetector',
                'freehandTool.generator.utils',
                'freehandTool.segmentString',
                'freehandTool.type']
     )