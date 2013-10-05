'''
Copyright 2012 Lloyd Konneker

This is free software, covered by the GNU General Public License.
'''
from PyQt5.QtCore import QLine
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
    Initial send to CurveGenerator.
    '''
    assert isinstance(point, PointerPoint), str(point)
    return QLine(point, point)
  
  
  def __init__(self, point1, point2):
    '''
    No substantive change, just check types.
    '''
    assert isinstance(point1, PointerPoint)
    assert isinstance(point2, PointerPoint)
    super(PathLine, self).__init__(point1, point2)