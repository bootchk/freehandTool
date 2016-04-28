'''
Copyright 2012 Lloyd Konneker

This is free software, covered by the GNU General Public License.
'''
try:
  from PyQt5.QtCore import QPoint
except ImportError:
  from PySide.QtCore import QPoint



class PointerPoint(QPoint):
  '''
  Integer valued point.
  
  Thin wrapper of implementation in Qt.
  
  In device CS (Qt View.)
  
  !!! Note we are actually using vector interpretation of point (having a direction) especially the crossProduct()
  '''
  
  def crossProduct(self, other):
    ''' 
    vector cross product. QPoint does not define. 
    
    Assert result is integer, with no loss of precision.
    '''
    return self.x()*other.y() - self.y()*other.x()
  

  def __copy__(self):
    return PointerPoint(self.x(), self.y())