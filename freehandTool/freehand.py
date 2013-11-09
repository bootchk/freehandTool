from __future__ import print_function # Python3 compatible

'''
Copyright 2012 Lloyd Konneker

This is free software, covered by the GNU General Public License.
'''

'''
Freehand drawing tool.
Input: pointer device (mouse) events.
Output: graphic vector path (lines and splines) which a GUI toolkit renders.
Not a complete app, only a component.
Includes a rudimentary GUI app for testing.
Written in pure Python.

Tags:
- freehand drawing
- computational geometry.
- incremental (dynamic) line tracing.
- Python coroutines.
- pipe of filters.
- GUI toolkit Qt.


Incremental line tracing
========================
Tracing means generating vector graphics from bitmaps.
Incremental, also called dynamic, means generate graphics as a user works,
before the user has completed a stroke (say by mouseReleaseEvent.)
Compare to other freehand tools that draw (not render) pixels until end of tool,
then fit splines to the complete PointerPath and renders the spline.
Here, immediately draw vector graphics (splines and lines.)
Here, look at only a finite tail of the PointerPath.

Goals of incrementality:
- avoid drawing jaggy pixel traces (only to be redrawn later)
- use machine cycles otherwise wasted waiting for pointerEvents

There is a tradeoff: if we spend too much time here, then we fall behind the pointer,
and worse, most GUI toolkits will condense pointer events and only deliver the latest one
(leaving gaps in the input PointerPath).  In other words,  the input will have low resolution.
Then the output suffers, since its quality depends on input resolution.


Filter pipes in Python
======================
This is a series or pipe of filters.
The data between the filters are sequences (streams) of:
- pointer positions, possibly with gaps and possibly with jitter
- pointer positions, without jitter (not implemented)
- pointer turns, between pointer positions not on same axis
- vectors (straight lines) fitting end to end and quaranteed to pass through every PointerPoint (the pixel around it.)
- vectors with adjusted real vertexes (not implemented)
- graphic objects (lines and segments)
- optimized graphic objects (minimal count and minimal error) (not implemented)

The filters are "extended generator" or coroutine or "reverse generators."
Pointer events are pushed (send()) into the pipe and each filter pushes any result to the next filter.
Each filter may maintain history (often just one previous) of its input events,
rolling forward when it recognizes an object that the next filter needs.
The final filter generates finished graphic objects.


potrace
=======
This uses sequence of filters and algorithms from potrace library for tracing bitmap images, by Peter Selinger.
See the potrace paper, it is well written and understandable.

Note some of the filters are optional and this code might not implement them.
See potrace for more description of missing filters.

The main difference to potrace is: potrace input is an image, this input is a PointerPath.

One difference from potrace is that potrace globally finds the best fit.
That is, for a COMPLETE PointerPath, there are many fits, and it would find the best.
Incrementally, we don't have a complete PointerPath,
and we don't have the computing power to incrementally generate a best fit for the partial PointerPath.
We only find the easiest fit, the first one generated.
This could be extended to find a better fit from a set of alternative fits for a short tail of the PointerPath
(where short is defined by how much we can do without lagging the pointer.)
Or you could just use the generated fit as a first approximation, find the best fit, and redraw
(which the user might see as a nudge.)

Another difference from potrace is that potrace generates from continuous paths.
Here the path is generated by the pointer device and may have gaps (if the OS is busy.)
Here detectCorner works despite gaps, i.e. isolates rest of pipe from gaps in the PointerPath. 

Another difference from potrace is that this uses timing.

A property of the potrace algorithm is that it generates cusps for sharp angles on short path segments,
AND ALSO cusps for shallow angles on long path lines.
That is a problem for incremental PointerPath tracing: when user moves the pointer very fast,
it leaves long gaps in the PointerPath, makes for long path lines, and cusps rather than splines.
Also, the generated cusps form a polygon which circumbscribes INSIDE concavities of "real pointer track."
A simple fix MIGHT be to dynamically adjust ALPHAMAX to a value near 4/3 when the pointer is moving very fast.
But it might be a hard limit of implementation in Python: 
there simply is not enough machine resources (in one thread) to do better.
(Another fix might be a threaded implementation.)


Timing
======

The timing of a user's stroke has meaning or intention.
When a user strokes rapidly, they intend a smooth curve.
When a user slows a stroke and turns, they might intend a cusp.
But a slow diagonal generates many PathTurns, which should not generate a cusp.


Ghosting
=======
Since the pipeline lags, ghost a graphic item from last output of pipeline to current PointerPoint.
Otherwise, the drawn graphic separates from the pointer.

There are two alternatives implemented for the ghost (also called the head):
- ghost is a straight LinePathElement (ghostLine.py)
- ghost is a QGPathItem( freehandHead.py)

Note when shutting down the pipeline, final segments are generated and
a final head is added between the end of the pipeline generated path and final pointer position.
The final head is NOT the same as the ghost.


Closing the pipeline
====================
The pipeline lags. Shutting down the pipeline may generate more segments (without new pointer positions)
but also may leave the generating segment string short of the last PointerPoint.
So we generate a final head segment, from several alternatives:
- a straight line
- several straight lines (an untraced pointer track, similar to the head.) (Not implemented.)
- another algorithm to fit a curve? (Not implemented.)


Null segments
=============
Early versions generated null segments.  
Null segments added to a QPainterPath have no effect.
The resulting SegmentString seems OK, but cuspness gets mangled.

Later versions don't generate null segments.  
We check that a segment added is not null, and raise an exception.

We catch that exception in certain places, but it may still be uncaught and reach the caller.
Although this is not nice, it reveals certain situations that
should be handled better by freehand, yielding better SegmentString (by a few pixels?)
So if you get this exception, you should report it to the author,
or change the code yourself so that the exception is NOT uncaught
(for example, catching the exception, simply not generating the null segment
and gracefully continuing tracing.)

Currently, the exception is rarely generated, in segmentsForCusp(),
and when it is, we gracefully handle it.
It takes many minutes of drawing, usually very small movements back and forth,
to cause the exception to be generated.

(The exception is still generated after a major rewrite fixing int/float and View/Scene/Local issues.)

It is really not a matter of performance:
whether you spend more time discovering null segments,
or whether you call Qt to append a null segment that has no effect,
probably takes the same amount of time.


FUTURE
====
adapt tool to any GUI kit
jitter filter: doesn't seem to be necessary
curve optimization filter: doesn't seem to be necessary
draw raw mouse track as well as smoothed, for testing
Expose other parameters
Generating single spline, instead of (spline, line) for cusp-like?
Generate a  spline at closing?


Naming
======
generator functions are not classes, but I use use upper case leading letter to emphasize
that calling them returns a generator, whose name begins with lower case letter.


Terminology
===========
(I attempt to use separate terms for distinct concepts!)
Pixels have corners (between sides of a square.)
A PointerPoint is usually coordinates of the upper left corner of a pixel.
A PointerPath, often called a stroke, is a sequence of captured PointerPoints,
from a "pointer device", i.e. mouse, pen, or touch.
(But stroke also refers to a graphics operation of rendering with a brush.)
The "real pointer track" is the shape the user drew, not captured when the pointer moves very fast.
PointerPaths have turns (between subpaths on axis.) Called corners in potrace.
A PathLine is between one or more turns.
Consecutive PathLines have a pivot (points between sequential, non-aligned vectors.)
(Sometimes I use line ambiguously to mean: the math concept, a PathLine, or a LinePathElement.)
The output is a PointerTrack, a sequence of graphic vectors.
Here, it is represented by a QPainterPath inside a QGraphicPathItem.
A PointerTrack comprises a sequence of graphic path items (or elements.)
Graphic path items are LinePathElements or SplinePathElements (beziers.)
Graphic path items have end points.
A cusp is a point between two graphic LinePathElements.  Also called a corner in potrace.
A cusp is usually sharp, but not always an acute angle.
A cusp-like is an end point between a graphic LinePathElement and a SplinePathElement.
When a LinePathElement is between two SplinePathElements, one of the cusp-like is usually sharp.
Distinguish between the PointerPath (bitmap coord input) and the PointerTrack (vector output.)



GUI toolkit adaption
====================
As written, FreehandTool uses Qt.
It could be adapted for other toolkits.
From Qt we use:
- QPointF for points and vectors.
- QLineF for lines
- view and scheme with an API for converting global coords to scheme coords
 and for adding graphic items to scheme
- QGraphicPathItem for the generated drawable graphic (comprising line and curve elements),
to represent user's stroke, 
- OR a set of QGraphicItems for lines and segments


Coordinate systems (CS)
=======================
Tool input is a pointer track.
Typically (e.g. Qt) these are in device (View) CS, and as in a QMouseEvent, are ints.
Freehand uses PointerPoint class to wrap them.
TurnGenerator receives and generates PointerPoints.
LineGenerator generates PathLine objects, which are also int (pairs of PointerPoint) in the View CS.
CurveGenerator converts PathLine objects to FreehandPoint, which are float and in the Scene CS.
Segments are created by passing FreehandPoint.
Segments are converted to Local CS (float) of SegmentString when appended.

(An early design converted back and forth to Device CS, with loss of precision due to a call to round().)
'''


import sys

# !!! QTime for timing of cusps
# !!! This not depend on QtGui.  SegmentString depends on QtGui.
from PyQt5.QtCore import QObject

from .generator.turnGenerator import TurnGeneratorMixin
from .generator.lineGenerator import LineGeneratorMixin
from .generator.curveGenerator import CurveGeneratorMixin
from .segmentString.segment import LineSegment
from .type.pathLine import PathLine
from .type.freehandPoint import FreehandPoint


'''
Generators are mixin behavior.
  
A generator filter is a mixin'ed method of FreeHand class.
A generator method name is capitalized because method *appears* to be a class.
'''
# Need QObject for QTime

class FreehandTool(TurnGeneratorMixin, LineGeneratorMixin, CurveGeneratorMixin, QObject):


  def __init__(self):
    self.turnGenerator = None # Flag, indicates pipe is generating
    # Also attributes: lineGenerator and curveGenerator
    
    # Tool operates on these, but they are None until setSegmentString
    self.pathHeadGhost = None
    self.path = None
    
    self._isGenerating = False
    
    '''
    Cache last point generated.  CurveGenerator uses this.  In frame (CS) of CurveGenerator
    Alternative is to get it from SegmentString,
    but that might suffer loss of precision from coordinate transformations between frames.
    '''
    self.lastEndPointGenerated = None
    
    
  def setSegmentString(self, segmentString, pathHeadGhost, scenePosition):
    '''
    Client call to initialize: tell tool the SegmentString it should operate upon.
    Client should add segmentString graphics item to scene.
    Tool starts writing into segmentString after pointerPressEvent().
    '''
    self.path = segmentString
    self.pathHeadGhost = pathHeadGhost
    self.pathHeadGhost.showAt(scenePosition)

    
  def _initFilterPipe(self, startPosition):
    ''' 
    Initialize pipe of filters.
    They feed to each other in same order of creation.
     '''
    self.turnGenerator = self.TurnGenerator(startPosition) # call to generator function returns a generator
    self.turnGenerator.send(None) # Execute preamble of generator and pause at first yield
    self.lineGenerator = self.LineGenerator(startPosition) 
    self.lineGenerator.send(None) 
    self.curveGenerator = self.CurveGenerator(PathLine.nullPathLine(startPosition))
    self.curveGenerator.send(None)
    self.setGenerating(True)
  
  
  def _closeFilterPipe(self):
    '''
    Close generators. 
    They will finally generate SOME of final objects (i.e. turn, PathLine) to current PointerPoint.
    Assume we already received a pointerMoveEvent at same coords of pointerReleaseEvent.
    
    close() is a built-in method of generators.
    
    Closing a generator may cause it to yield, and thus invoke downstream generators in the pipeline.
    Close generators in their order in the pipeline.
    '''
    if self.isGenerating():  
      self.turnGenerator.close()
      self.lineGenerator.close()
      self.curveGenerator.close()
      self.setGenerating(False)
    # else ignore pointerRelease without prior pointerPress, race?


  def pointerMoveEvent(self, pointerEvent):
    ''' Client feeds pointerMoveEvent into a pipe. '''
    if self.isGenerating():
      try:
        self.turnGenerator.send(pointerEvent.viewPos)  # Feed pipe
      except StopIteration:
        '''
        While user is moving pointer with pointer button down, we don't expect pipe to stop.
        For debugging, call exitAbnormally().
        If a component of large app, raise.
        A caller might catch it and rescue by ending and restarting the tool?
        '''
        raise
      else: # else no exception
        self.pathHeadGhost.updateEnd(FreehandPoint(pointerEvent.scenePos))
    # else ignore pointerEvent when not isGenerating
  
  
  def exitAbnormally(self):
    " For debugging: quit app so we can see error trace. "
    print("Abnormal pointerMoveEvent, exiting")
    sys.exit()
    
    
  def pointerPressEvent(self, pointerEvent):
    ''' Client call to start freehand drawing. '''
    self._initFilterPipe(pointerEvent.viewPos)

  
  def pointerReleaseEvent(self, pointerEvent):
    ''' Client call to end freehand drawing. '''
    self._closeFilterPipe()
    self.pathHeadGhost.hide()
    self._createFinalSegment(pointerEvent)
    #print "Final segment count", self.path.countSegments()
  
  
  def isGenerating(self):
    ''' Is pointer button down and accepting pointerEvents. '''
    return self._isGenerating
  
  def setGenerating(self, truth):
    ''' Set flag indicating closed generators, not accepting pointerEvents. '''
    self._isGenerating = truth
    
    
  
  def _createFinalSegment(self, pointerEvent):
    '''
    CurveGenerator only finally draws:
    - to midpoint of current PathLine.
    - OR for a cusp, current PathLine is nullLine (generated MidToEnd)
    
    Add final element to path, a LinePathElement from midpoint to current PointerPoint.
    Note path already ends at the midpoint, don't need to "return" it from close()
    (and close() CANNOT return a value.)
    
    TODO are we sure not leaving PointerTrack one pixel off?
    TODO straight line is crude, should generate a curve or pointerTrack (many line segments)
    '''
    
    # Scene coordinates, float, but don't need near comparison
    currenPathEnd = self.lastEndPointGenerated
    currentPointerPos = pointerEvent.scenePos   # was viewPos
    # Only create final segment if pointer was NOT released at exact end of current path 
    # For example when ending on a timed cusp??
    if currenPathEnd != currentPointerPos:
      #print "Created final line segment"
      finalLineSegment = LineSegment(startPoint=currenPathEnd, endPoint=currentPointerPos)
      self.path.appendSegments( [finalLineSegment], segmentCuspness=[False])
  
  
  def testControlPoint(self, event, alternateMode):
    ''' 
    For testing, simulate a GUI that moves ControlPoints. 
    
    Any key will move a control point (fixed by constant below.)
    If ControlKey is down, will move the control point
    in an alternate mode (moving the control point independently
    versus moving the control point and its related control point together.)
     '''
    print("Test moving control point.")
    controlPointSet = self.path.getControlPointSet()
    
    """
    Oct. 2013 Seems somewhat broken after conversion to Python3.
    Now only 7 works???
    """
    # delta an arbitrary control point
    # 8 start anchor of second segment
    # 6 is Direction CP of second seg
    # 7 is the end anchor of second segment
    arbitraryControlPoint = controlPointSet[7]
    if arbitraryControlPoint is None:
      print("Arbitrary control point is None")
    self.path.moveRelated(controlPoint=arbitraryControlPoint, 
                          deltaCoordinate=FreehandPoint(5,5), 
                          alternateMode=alternateMode)
    # Result should be visible
  
  
  def mapFromDeviceToScene(self, pointVCS):
    '''
    Map from device coords (pipeline input) to freehandTool internal CS.
    Which here is Scene CS.
    Must be real valued.
    Must be mappable to Local CS of SegmentString.
    
    Depends on Qt.
    '''
    '''
    Can't: assert isinstance(pointVCS, PointerPoint), str(pointVCS),
    since PathLine.p1(), p2() methods return QPoint.
    '''
    assert isinstance(pointVCS.x(), int)
    assert isinstance(pointVCS.y(), int)
    
    # Hack: tool knows segmentString which knows scene which knows view which can map VCS to SCS
    result = self.path.scene().views()[0].mapToScene(pointVCS)
    #assert isinstance(result, QPointF)
    return result
