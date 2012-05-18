
import functools

from controlPoint import ControlPoint
from segment import ARM_TO, TIED_TO, OPPOSITE_TO
from relationWalker import relationWalker


class SegmentActions(object):
  '''
  Algorithms acting on ControlPoints of a SegmentString.
  
  Currently, only one algorithm for a GUI where SegmentStrings are only cubic curves,
  and where:
  - the only action is moving 
  - moving a ControlPoint maintains smoothness depending on role of ControlPoint and pre-existence of smoothness.
  
  FIXME: delete actions
  Deleting ControlPoint would mean e.g. simplify curve to arc or straighten curve to line
  
  Pattern: Strategy
  =================
  FIXME: There could be more than one algorithm, for each GUI design.
  IE implement concrete subclasses of abstract SegmentActions.
  
  Here, the caller is a SegmentString, which passes a *Context* which is the relations, etc. between ControlPoints.
  Does NOT pass a reference to the caller.
  '''
  
  
  '''
  TODO: if move Direction, clearCuspness
  This GUI design only allows cuspness to clear.
  To make cuspness dynamic, need to check for cuspness after move direction point.
  '''
  
  def moveRelated(self, relations, controlPoint, deltaCoordinate, alternateMode):
    self._dispatchMoveRelated(relations, controlPoint, deltaCoordinate, alternateMode)
    # Assert above triggers events to update SegmentString
  
  
  def _dispatchMoveRelated(self, relations, controlPoint, deltaCoordinate, alternateMode):
    ''' 
    Dispatch: GUI meaning of move depends on role and other conditions.
    
    IOW, this defines how a drag of a ControlPoint playing a particular Role
    becomes a translation of a set of ControlPoints.
    '''
    # Create visitor function having parameter a ControlPoint instance, with deltaCoordinate fixed
    visitor = functools.partial(ControlPoint.updateCoordinate, deltaCoordinate=deltaCoordinate)
    if self.isRoleAnchorAtCusp(controlPoint):
      if not alternateMode:
        # default is : make cusps more cuspy or possible take out the cusp
        print "Moving cusp anchor"
        self.moveNotMaintainingSmoothness(relations, controlPoint, deltaCoordinate, alternateMode, visitor)
      else:
        # alternate is weaker: can't remove the cusp, only move it as a three ControlPoint unit
        self.moveMaintainingSmoothness(relations, controlPoint, deltaCoordinate, alternateMode, visitor)
    elif self.isRoleAnchor(relations, controlPoint):
      # assert is not at cusp
      if not alternateMode:
        # default is: maintain smoothness
        self.moveMaintainingSmoothness(relations, controlPoint, deltaCoordinate, alternateMode, visitor)
      else:
        # alternate is stronger: usually make a cusp
        self.moveNotMaintainingSmoothness(relations, controlPoint, deltaCoordinate, alternateMode, visitor)
    elif self.isRoleDirection(relations, controlPoint):
      if not alternateMode:
        # Move Direction CP independently
        # TODO:
        relationWalker.walk(root=self, relations=self.relations, relationsToFollow=[], maxDepth=0)
      else:
        # Move Direction CP and its Anchor.  This is probably non-intuitive to users.
        # TODO:
        relationWalker.walk(root=self, relations=self.relations, relationsToFollow=[ARM_TO], maxDepth=1)

  '''
  Roles
  '''

  def isRoleAnchorAtCusp(self, controlPoint):
    ''' 
    Returns whether anchor is at a cusp.
    Two anchors are at a cusp, but only segments where the anchor is the last (not first)
    anchor of its segment is identified as a cusp segment.
    
    Anchor is at cusp if it is last anchor of cusped segment
    OR first anchor TiedTo anchor with same conditions.
    '''
    if controlPoint.parentSegment.isLastAnchor(controlPoint):
      return self._testAnchorCusp(controlPoint)
    else:
      segmentString = controlPoint.parentSegment.parent
      # Only the SegmentString knows TiedTo relation between Anchors of different segments
      tiedToAnchor = segmentString.relations.getRelatedInstance(controlPoint, "TiedTo")
      if tiedToAnchor is not None:
        return self._testAnchorCusp(tiedToAnchor)
      else: # controlPoint must be an end Anchor of SegmentString, or is not an Anchor
        return False
      

  def _testAnchorCusp(self, controlPoint):
    # assert controlPoint is Anchor and last in segment
    parentSegment = controlPoint.parentSegment
    segmentString = parentSegment.parent
    # SegmentString knows which segments are cusps
    return segmentString.isSegmentCusp(parentSegment.getIndexInParent())
  
    
  def isRoleAnchor(self, relations, controlPoint):
    '''
    Is controlPoint role Anchor?
    
    A ControlPoint plays the Anchor role if:
    - it is ArmTo related (paired with a Direction CP)
    - AND it is OppositeTo related (paired with an opposite Anchor CP)
    A ControlPoint playing the Anchor role MAY be TiedTo related (to an Anchor of an adjoining segment)
    unless it is the starting or ending Anchor of a PolySegment.
    '''
    # TEMP when PolySegment has no lines (having no Direction CP's), OPPOSITE_TO is sufficient for Anchor
    return relations.isRelated(instance=controlPoint, relationType=OPPOSITE_TO)


  def isRoleDirection(self, controlPoint):
    '''
    A ControlPoint plays the Direction role if:
      - it is ArmTo related 
      - AND has no other relation
    '''
    return False
  
  '''
  Movements
  '''
  def moveMaintainingSmoothness(self, relations, controlPoint, deltaCoordinate, alternateMode, visitor):
    '''
    Move all TiedTo Anchor CP's and their Direction CP's: maintain smoothness (colinear) or lack thereof (cuspness.)
    '''
    relationWalker.walk(root=controlPoint, 
                        relations=relations, 
                        relationsToFollow=[TIED_TO, ARM_TO],
                        visitor = visitor,
                        maxDepth=2)
  
  
  def moveNotMaintainingSmoothness(self, relations, controlPoint, deltaCoordinate, alternateMode, visitor):
    '''
    Move just the TiedTo Anchor CP's: smoothness may change
    '''
    relationWalker.walk(root=controlPoint,
                        relations=relations, 
                        relationsToFollow=[TIED_TO],
                        visitor = visitor,
                        maxDepth=1)
    # TODO: Calculate new colinear smoothness
    
    
    
# Singleton
segmentStringActions = SegmentActions()
  