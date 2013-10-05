'''
Copyright 2012 Lloyd Konneker

This is free software, covered by the GNU General Public License.
'''


import functools

from .controlPoint import ControlPoint
from .segment import ARM_TO, TIED_TO, OPPOSITE_TO
from .relationWalker import relationWalker


class SegmentActions(object):
  '''
  GUI actions on ControlPoints of a SegmentString.
  
  Currently, only actions for a GUI where SegmentStrings are only cubic curves,
  and where:
  - the only action is translating (not deleting ControlPoints NOR expanding or rotating direction arms.)
  - moving a ControlPoint maintains cuspness depending on role of ControlPoint and pre-existence of cuspness.
  
  FIXME: delete actions
  Deleting ControlPoint would mean e.g. simplify curve to arc or straighten curve to line
  
  Pattern: Strategy
  =================
  !!! See singleton at end of file.
  FIXME: There could be more than one set of actions, for different GUI design.
  IE implement concrete subclasses of abstract SegmentActions.
  For example, a user preference: use action set from a competing app.
  
  Here, the Strategy caller is a SegmentString, which passes a *Context* which is the relations, etc. between ControlPoints.
  Does NOT pass a reference to the caller.
  
  TODO: 
  =====
  As is, when user moves a Direction CP, cuspness is created.
  To make cuspness dynamic, need to check and possibly restore cuspness (smoothness) after move direction point.
  '''
  
  def moveRelated(self, relations, controlPoint, deltaCoordinate, alternateMode):
    # assert traversal flags are cleared
    self._dispatchMoveRelated(relations, controlPoint, deltaCoordinate, alternateMode)
    # Assert above triggers events to update SegmentString
  
  
  def _dispatchMoveRelated(self, relations, controlPoint, deltaCoordinate, alternateMode):
    ''' 
    Dispatch: GUI meaning of move depends on role and other conditions (cuspness.)
    
    IOW, this defines how a drag of a ControlPoint playing a particular Role
    becomes a translation of a set of ControlPoints.
    '''
    assert controlPoint is not None
    
    # Create visitor function having parameter a ControlPoint instance, with deltaCoordinate fixed
    visitor = functools.partial(ControlPoint.updateCoordinate, deltaCoordinate=deltaCoordinate)
    
    if self.isRoleAnchorAtCusp(controlPoint):
      if not alternateMode:
        # default is : make cusps more cuspy or possibly take out cusp
        #print "Moving cusp anchor"
        self.moveAnchorSetNotMaintainingCuspness(relations, controlPoint, deltaCoordinate, alternateMode, visitor)
      else:
        # alternate is weaker: don't remove the cusp, only move it as a three ControlPoint unit
        self.moveAnchorSetMaintainingCuspness(relations, controlPoint, deltaCoordinate, alternateMode, visitor)
    elif self.isRoleAnchor(relations, controlPoint):
      # assert is not at cusp
      if not alternateMode:
        # default is: maintain cuspness (smoothness)
        self.moveAnchorSetMaintainingCuspness(relations, controlPoint, deltaCoordinate, alternateMode, visitor)
      else:
        # alternate is stronger: usually make a cusp
        self.moveAnchorSetNotMaintainingCuspness(relations, controlPoint, deltaCoordinate, alternateMode, visitor)
    elif self.isRoleDirection(relations, controlPoint):
      if not alternateMode:
        # default is: weak, move just the Direction CP (rotate the arm)
        self.moveDirectionPointIndependently(relations, controlPoint, deltaCoordinate, alternateMode, visitor)
      else:
        # default is strong: move whole side of arm (but not the side of arm on other side of Anchors.)
        self.moveDirectionArm(relations, controlPoint, deltaCoordinate, alternateMode, visitor)
    else:
      print("Control point has unknown role?")

  '''
  Roles of ControlPoints in SegmentString.
  '''

  def isRoleAnchorAtCusp(self, controlPoint):
    ''' 
    Returns whether controlPoint is Anchor and is at a cusp.
    
    Anchor is at cusp if it is last anchor of cusped segment
    OR first anchor TiedTo anchor with same conditions.
    '''
    distinguishedAnchor = self.getDistinguishedAnchorOfPair(controlPoint)
    if distinguishedAnchor is not None:
      return self._testAnchorCusp(distinguishedAnchor)
    else:
      return False  # Not Anchor at all
  
      
  def getDistinguishedAnchorOfPair(self, controlPoint):
    ''' 
    ControlPoint may be an anchor.  If so, may be two anchors coincident.  
    Return the distinguished one (which is the end of its segment, not the first.)
    Return None if not an anchor or is solitary (the first Anchor of the first segment.)
    '''
    if controlPoint.parentSegment.isLastAnchor(controlPoint):
      return controlPoint
    else: # not an anchor or first anchor
      segmentString = controlPoint.parentSegment.parentString
      # Only the SegmentString knows TiedTo relation between Anchors of different segments
      return segmentString.relations.getRelatedInstance(controlPoint, TIED_TO)
    # assert returns last Anchor or None


  def _testAnchorCusp(self, controlPoint):
    ''' Is this distinguished Anchor at a Cusp? '''
    # assert controlPoint is Anchor and last in segment
    parentSegment = controlPoint.parentSegment
    segmentString = parentSegment.parentString
    # SegmentString knows which segments are cusps
    return segmentString.isSegmentCusp(parentSegment.getIndexInString())
  
    
  def isRoleAnchor(self, relations, controlPoint):
    '''
    Is controlPoint role Anchor?
    
    A ControlPoint plays the Anchor role if:
    - it is ArmTo related (paired with a Direction CP)
    - AND it is OppositeTo related (paired with an opposite Anchor CP)
    A ControlPoint playing the Anchor role MAY be TiedTo related (to an Anchor of an adjoining segment)
    unless it is the starting or ending Anchor of a SegmentString (the boundary set of ControlPoints of SegmentString.)
    '''
    # FIXME: when SegmentString is only curves (no lines having no Direction CP's), OPPOSITE_TO is sufficient for Anchor
    return relations.isRelated(instance=controlPoint, relationType=OPPOSITE_TO)


  def isRoleDirection(self, relations, controlPoint):
    '''
    A ControlPoint plays the Direction role if:
      - it is ArmTo related 
      - AND has no other relation
    '''
    return relations.isSolelyRelated(instance=controlPoint, relationType=ARM_TO)
  
  
  
  '''
  Movements
  
  Interpret drag of ControlPoint to translations of set of related ControlPoints.
  '''
  
  def moveAnchorSetMaintainingCuspness(self, relations, controlPoint, deltaCoordinate, alternateMode, visitor):
    '''
    Move all TiedTo Anchor CP's and their Direction CP's: maintain cuspness or lack thereof (smoothness.)
    '''
    relationWalker.walk(root=controlPoint, 
                        relations=relations, 
                        relationsToFollow=[TIED_TO, ARM_TO],
                        visitor = visitor,
                        maxDepth=2)
  
  
  def moveAnchorSetNotMaintainingCuspness(self, relations, controlPoint, deltaCoordinate, alternateMode, visitor):
    ''' Move just the TiedTo Anchor CP's: cuspness may change. '''
    relationWalker.walk(root=controlPoint,
                        relations=relations, 
                        relationsToFollow=[TIED_TO],
                        visitor = visitor,
                        maxDepth=1)
    self.updateAnchorCuspness(controlPoint)
    
    
  def moveDirectionPointIndependently(self, relations, controlPoint, deltaCoordinate, alternateMode, visitor):
    '''Move just a Direction CP. '''
    relationWalker.walk(root=controlPoint,
                      relations=relations, 
                      relationsToFollow=[],
                      visitor = visitor,
                      maxDepth=0)
    self.updateDirectionCuspness(relations, controlPoint)
  
  
  def moveDirectionArm(self, relations, controlPoint, deltaCoordinate, alternateMode, visitor):
    '''Move a Direction CP and its Anchor CP. '''
    relationWalker.walk(root=controlPoint,
                      relations=relations, 
                      relationsToFollow=[ARM_TO],
                      visitor = visitor,
                      maxDepth=1)
    self.updateDirectionCuspness(relations, controlPoint)
  
  
  def updateDirectionCuspness(self, relations, controlPoint):
    ''' Direction CP moved: Calculate new colinear cuspness. '''
    anchor = relations.getRelatedInstance(controlPoint, ARM_TO)
    self.updateAnchorCuspness(anchor)
  
  def updateAnchorCuspness(self, controlPoint):
    ''' Anchor CP moved: Calculate new colinear cuspness. '''
    # TODO: for now, always make cusp.  Should calculate.
    distinguishedAnchor = self.getDistinguishedAnchorOfPair(controlPoint)
    if distinguishedAnchor is not None:
      segment = distinguishedAnchor.parentSegment
      segmentString = segment.parentString
      segmentIndex = segment.getIndexInString()
      segmentString.setSegmentCuspness(segmentIndex)
      
    
# Singleton
segmentStringActions = SegmentActions()
  