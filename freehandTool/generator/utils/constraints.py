'''
Copyright 2012 Lloyd Konneker

This is free software, covered by the GNU General Public License.
'''
from ...type.pointerPoint import PointerPoint



class Constraints(object):
  '''
  Constraints comprise pair of vectors.
  Their origin is near starting position, which is same as starting turn.
  It may help to think of them as crossing, from extremities of first pixel corners,
  to "opposite", but nearest to centerline, corner of extreme pixel in path.
  In other words, constraints define a funnel where future pixels can be
  and there still exist an approximating vector touching all pixels.
  
  !!! Integers
  '''
  def __init__(self):
    # Null vectors
    self.constraintLeft = PointerPoint(0,0)
    self.constraintRight = PointerPoint(0,0)
  
  def __repr__(self):
    return "Left " + str(self.constraintLeft) + " Right " + str(self.constraintRight)
  
  def isViolatedBy(self, vector=None):
    ''' Does vector violate constraints? i.e. lie outside constraint vectors '''
    return self.constraintLeft.crossProduct(vector) < 0 or self.constraintRight.crossProduct(vector) > 0
  
  
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
      #print "No constraints."
      pass
    else:
    '''
    #print "Updating constraints"
    offset = PointerPoint( v.x() + (1 if v.y() >= 0 and (v.y()>0 or v.x()<0) else -1 ),
                      v.y() + (1 if v.x() <= 0 and (v.x()<0 or v.y()<0) else -1 ) )
    if self.constraintLeft.crossProduct(offset) >= 0 :
      self.constraintLeft = offset
      
    offset = PointerPoint( v.x() + (1 if v.y() <= 0 and (v.y()<0 or v.x()<0) else -1 ),
                      v.y() + (1 if v.x() >= 0 and (v.x()>0 or v.y()<0) else -1 ) )
    if self.constraintRight.crossProduct(offset) <= 0 :
      self.constraintRight = offset

  
  