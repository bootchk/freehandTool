'''
Copyright 2012 Lloyd Konneker

This is free software, covered by the GNU General Public License.
'''
from PySide.QtCore import QPointF



class Constraints(object):
  '''
  Constraints comprise pair of vectors.
  Their origin is near starting position, which is same as starting turn.
  It may help to think of them as crossing, from extremities of first pixel corners,
  to "opposite", but nearest to centerline, corner of extreme pixel in path.
  In other words, constraints define a funnel where future pixels can be
  and there still exist an approximating vector touching all pixels. 
  '''
  def __init__(self):
    # Null vectors
    self.constraintLeft = QPointF(0,0)
    self.constraintRight = QPointF(0,0)
  
  def __repr__(self):
    return "Left " + str(self.constraintLeft) + " Right " + str(self.constraintRight)
  
  def isViolatedBy(self, vector=None):
    ''' Does vector violate constraints? i.e. lie outside constraint vectors '''
    return self.crossProduct(self.constraintLeft, vector) < 0 or self.crossProduct(self.constraintRight, vector) > 0
  
  
  def update(self, v):
    '''
    Update constraints given vector v.
    Vector v is via all turns: many turns may have satisfied constraints.
    Assert: Vector v satisfies constraints.
    '''
    '''
    Potrace checked for no constraints as follows.
    It never occurs when turns are input since it takes three pixels to make a turn.
    If you take out turnGenerator, this might make sense.
   
    if abs(v.x())<=1 and abs(v.y())<=1 :
      print "No constraints."
      pass
    else:
    '''
    # print "Updating constraints"
    offset = QPointF( v.x() + (1 if v.y() >= 0 and (v.y()>0 or v.x()<0) else -1 ),
                      v.y() + (1 if v.x() <= 0 and (v.x()<0 or v.y()<0) else -1 ) )
    if self.crossProduct(self.constraintLeft, offset) >= 0 :
      self.constraintLeft = offset
      
    offset = QPointF( v.x() + (1 if v.y() <= 0 and (v.y()<0 or v.x()<0) else -1 ),
                      v.y() + (1 if v.x() >= 0 and (v.x()>0 or v.y()<0) else -1 ) )
    if self.crossProduct(self.constraintRight, offset) <= 0 :
      self.constraintRight = offset

  def crossProduct(self, p1, p2):
    ''' vector cross product. QPointF does not define. '''
    return p1.x()*p2.y() - p1.y()*p2.x()
  
  