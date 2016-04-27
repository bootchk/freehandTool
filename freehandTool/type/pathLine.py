'''
Copyright 2012 Lloyd Konneker

This is free software, covered by the GNU General Public License.
'''
try:
  from PyQt5.QtCore import QLine
except ImportError:
  from PySide.QtCore import QLine
from .pointerPoint import PointerPoint

class PathLine(QLine):
  '''
  Line defined by two PointerPoint.
  
  Thin wrapper of implementation in Qt.
  
  PathLines are int valued.
  PathLines are in device CS (Qt View.)
  '''
  
  @classmethod
  def nullPathLine(self, point):
    ''' 
    Zero length PathLine at a point.
    
    Sent to CurveGenerator in these cases:
    - initial send
    - forced (flushing) send
    - final (flushing) send
    
    '''
    assert isinstance(point, PointerPoint), str(point)
    return PathLine(point, point)
  
  def __init__(self, point1, point2):
    '''
    No substantive change, just check types.
    '''
    assert isinstance(point1, PointerPoint)
    assert isinstance(point2, PointerPoint)
    super(PathLine, self).__init__(point1, point2)
    
  def isNullPathLine(self):
    return self.dx() == 0 and self.dy() == 0