'''
Copyright 2013 Lloyd Konneker

This is free software, covered by the GNU General Public License.

Ghost for head of being-drawn freehand curve.
Using a pipeline, the head is not known precisely, but it needs to be drawn
so that there is no gap between the pointer and the precise freehand curve.
It is a ghost in the sense that it approximates the precise freehand curve in progress.

This is one alternative.
Another alternative is keep the head in the SegmentString, updating it.

Derived from ghostLine, which is a QGLineItem, whereas this is a QGPathItem,
so that it follows the pointer track with more fidelity.
'''

from PySide.QtGui import QGraphicsPathItem, QPainterPath
from PySide.QtCore import QPoint

from type.freehandPoint import FreehandPoint



class PointerTrackGhost(QGraphicsPathItem):
  '''
  A ghost for freehand drawing.
  Graphic between current PointerPosition and last PointerTrack path segment generated, which lags.
  Finally replaced by a path segment.
  Hidden when user not using freehand tool.
  
  Implementation: extend QGraphicsPathItem.
  Use a path of lines, one for each pointerTrack value.
  That is, there is no attempt here to make it minimal;
  after all that is what the rest of freehand is doing.
  I.E. this has about the same density as a bitmap of the pointerTrack.
  
  This presents a simplified API to FreehandTool,
  to reduce coupling between FreehandTool and Qt.
  '''
  def __init__(self, **kwargs):
    super(PointerTrackGhost,self).__init__(**kwargs)
    self.start = None
    self.end = None
    self.path = QPainterPath() # working copy, frequently setPath() to self.
    # ensure is hidden, not in scene
  
  
  def showAt(self, initialPosition):
    #print "showAt"
    self.start = initialPosition
    self.end = initialPosition
    self.path.moveTo(initialPosition)
    self.setPath(self.path)
    self.show()
    
  
  def updateStart(self, pointSCS):
    '''
    Completely abandon the working path;
    assume new start point is near self.end (so that lineTo is short.)
    '''
    assert isinstance(pointSCS, FreehandPoint)
    self.path = QPainterPath()
    self.path.moveTo(pointSCS)  # OLD self.floatSceneFromIntViewPoint(pointVCS))
    self.path.lineTo(self.end)
    self.setPath(self.path)
    
    
  def updateEnd(self, point):
    '''
    Update current path by appending lineTo new end point.
    '''
    #print "updateEnd"
    assert isinstance(point, FreehandPoint)
    self.end = point
    self.path.lineTo(point)
    self.setPath(self.path)
    
    
  # hide() is inherited
  
  
  def floatSceneFromIntViewPoint(self, pointVCS):
    # !!! start point from FreehandTool is in View CS. 
    pointViewInt = QPoint(pointVCS.x(), pointVCS.y())
    pointSceneFloat = self.scene().views()[0].mapToScene(pointViewInt)
    return pointSceneFloat
  
  
  """
  WORK IN PROGRESS
  More complicated updateStart, but not working
  
  def updateStart(self, pointVCS):
    '''
    '''
    #print "updateStart"
    # !!! start point from FreehandTool is in View CS. 
    pointViewInt = QPoint(pointVCS.x(), pointVCS.y())
    pointSceneFloat = self.scene().views()[0].mapToScene(pointViewInt)
    self.start = pointSceneFloat
    
    newPath = self._deletePathPrefixTo(self.start)
    self.path = newPath
    self.setPath(self.path)
  
  def _deletePathPrefixTo(self, point):
    '''
    Shorten by deleting prefix of path up to point.
    '''
    newStartIndex = self._findFirstElementAt(point)
    # assert newStartIndex is the first element to point (?? needs to be the last??)
    
    return self._copyPathSuffix(newStartIndex, point)

    
  def _findFirstElementAt(self, point):
    # skip initial moveTo
    assert self.path.elementCount() > 1 # moveTo, lineTo
    for elementIndex in range(1, self.path.elementCount()):
      element = self.path.elementAt(elementIndex)
      #print element.x, element.y, point
      if element.x == point.x() and element.y == point.y() :
        return elementIndex
    assert False, 'New start point must be on existing path.'
      
      
  def _copyPathSuffix(self, index, point):
    '''
    Copy suffix of path starting at index.
    '''
    newPath = QPainterPath()
    newPath.moveTo(point)
    
    for elementIndex in range(index, self.path.elementCount()):
      element = self.path.elementAt(elementIndex)
      newPath.lineTo(element.x, element.y)
    return newPath
    
  """