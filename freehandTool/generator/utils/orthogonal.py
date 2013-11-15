'''
Copyright 2013 Lloyd Konneker

This is free software, covered by the GNU General Public License.
'''

'''
Methods taking two positions.
Primitives used to determine an axis.
Orthogonality along fixed axises of the screen.
'''

def areHorizontallyAligned(position1, position2):
  ''' same horizontal axis implies y()'s are same. '''
  return position1.y() == position2.y()

def areVerticallyAligned(position1, position2):
  return position1.x() == position2.x()

def areOrthogonal(position1, position2):
  ''' Are both positions on any same axis. '''
  return areHorizontallyAligned(position1, position2) or areVerticallyAligned(position1, position2)