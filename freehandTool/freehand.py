
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
A bitmap is a 'batch', and tracing it is a 'batch' operation: all data is known before you begin.

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


Flushing the pipe
=================

When the user is done (mouse button up), the pipe still holds data (positions, turns, pathLines)
that have not been traced into segments (straight lines or curves.)
In other words, the pipeline lags. 
Closing the pipe flushes that data.
That generate more segments (without new pointer positions)
The flushed generated segment string extends to the last PointerPoint.

Flushing the line generator sends a NullPathLine (infinitely short, a point, but still conceptually a line.)
The penultimate segment is a curve to the middle of that NullPathLine,
and the final (head) segment is a very short straight LineSegment.
(??? TODO Post process to eliminate that.)

But also, the pipe may be flushed when the user pauses.  See next section...


Using timing in incremental line tracing
========================================

A bitmap usually has no timing data, so batch tracing doesn't use timing.
But incremental line tracing can use the timing of positions in the pointer track.

In particular, if the user pauses, we flush the pipe.
This means that no data that follows can affect the tracing (smoothness) of what is already drawn.
The user sees it as the rendered segments catching up to the pointer position
(or the same thing, the ghost head of the drawn line collapsing to the pointer position.)

In other words, the user can pause to make a cusp (a hard corner or even a slight but hard inflection ).

The timing of a user's stroke has meaning or intention.
When a user strokes rapidly, they might intend a smooth curve (or not care if it is accurate.)
When a user slows a stroke and turns, they might intend less smoothing.
But we are NOT altering the smoothing parameter dynamically based on the speed of drawing.
(TODO should we?  This is a user interface issue.)

How flushing for a pause works
==============================

The feeder to the pipe (freehandTool.py) includes a timer,
so that it can know when the user has paused.
When the timer timeouts, we resend the last position received from the pointer, as a forcing or flushing event.
That works through the entire pipe, flushing it (each portion of the pipe can receive a forcing.)
The pipe is flushed but not closed.

(In early designs, the turn generator of the pipe had the timer. But the feeder is the best place for the timer.)


Reversals and spikes
====================

If the use reverses the pointer back along the same track,
the generated segment string should extend to the extremity.
Such a reversal could also be called a spike.
In batch tracing, spikes are usually filtered out, they are bad 'hairs' or noise on a block of pixels.

The original SimpleTurnDetector didn't properly handle spikes.
The ReverseDetector now does.

But those only handle spikes along the horizontal and vertical axis.
You can still see spikes not handled if the user reverses along a diagonal (quickly, without pausing.)
Drawing along a diagonal generates a sequence of turns.
When the user draws a diagonal spike, the reversing turns may still fall within the constraints of the LineGenerator.

TODO change the LineGenerator to detect extreme turns (in distance from the start turn) and generate lines to them
instead of to the turn that violates constraints.


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

# !!! QTime for timing of paused forcing
# !!! This not depend on QtGui.  SegmentString depends on QtGui.
try:
  from PyQt5.QtCore import QObject, QTimer
except ImportError:
  from PySide.QtCore import QObject, QTimer



from .generator.turnGenerator import TurnGeneratorMixin
from .generator.lineGenerator import LineGeneratorMixin
from .generator.curveGenerator import CurveGeneratorMixin
from .type.pathLine import PathLine
from .type.freehandPoint import FreehandPoint
from .logger import logger




'''
Generators are mixin behavior.
  
A generator filter is a mixin'ed method of FreeHand class.
A generator method name is capitalized because method *appears* to be a class.

!!! Note generator mixins call logger.debug() and so forth, so that must be defined in this class.
'''

# Need QObject for QTime
class FreehandTool(TurnGeneratorMixin, LineGeneratorMixin, CurveGeneratorMixin, QObject):
  '''
  Algebra of the API:
  tool := create use*    # A tool can be reused, zero or more times.
  use := setSegmentString  pointerPressEvent pointerMoveEvent* pointerReleaseEvent
  
  pointerMoveEvent can be called zero or more times.
  If called zero times, the segment string will be empty.
  If called only one time, at the same position as pointerPressEvent ???
  If called only two times, the second time at the same position as pointerPressEvent (jitter.) ???
  
  The API algebra is enforced.
  Cases:
  Fail to call setSegmentString: assertion exception.
  Call pointerMoveEvent without proper prefix: quietly ignored.
  Call pointerPressEvent more than once: assertion exception.
  Call pointerReleaseEvent more than once ???
  Call pointerReleaseEvent without a prior pointerPressEvent: assertion exception.
  TODO write doctests for these
  '''

  def __init__(self, view):
    super(FreehandTool, self).__init__()
    # See below: _initFilterPipe creates self.turnGenerator, etc.
    self._resetState()
    self.createTimer()
    self.path = None  # Do not reset, i.e. keep this reference to old path, for testing
    
    self.logger = logger
    self.logger.debug("Init FreehandTool")
    
    self.view = view
    
    
  def _resetState(self):

    self.pathHeadGhost = None # None until setSegmentString
    
    # API state
    self._wasSetSegment = False
    self._wasPointerPress = False
    self._wasPointerMove = False
    
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
    self._wasSetSegment = True
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
    self.turnGenerator.close()
    self.lineGenerator.close()
    self.curveGenerator.close()
    
  

  def pointerMoveEvent(self, pointerEvent):
    ''' 
    Client feeds pointerMoveEvent into a pipe. 
    
    !!! We don't assume that the same position will not be fed consecutively,
    or that consecutive positions are contiguous in any sense.
    The external system (OS and framework) might get busy and/or confused.
    '''
    if not self._wasPointerPress:
      return   # Quietly ignore this API error
    
    self.setGenerating(True)
    try:
      position = pointerEvent.viewPos
      self.turnGenerator.send((position, False))  # Feed pipe, not forced
      self.restartTimer(position)
      assert self.timer.isActive()
    except StopIteration:
      '''
      While user is moving pointer with pointer button down, we don't expect pipe to stop.
      For debugging, call _exitAbnormally(), below.
      If a component of large app, raise.
      A caller might catch it and rescue by ending and restarting the tool?
      '''
      raise
    else: # else no exception
      self.pathHeadGhost.updateEnd(FreehandPoint(pointerEvent.scenePos))
  
  
  """
  Optional code useful for debugging.
  import sys
  
  def _exitAbnormally(self):
    " For debugging: quit app so we can see error trace. "
    print("Abnormal pointerMoveEvent, exiting")
    sys.exit()
  """
    
  def pointerPressEvent(self, pointerEvent):
    ''' Client call to start freehand drawing. '''
    assert not self._wasPointerPress, 'Consecutive pointerPressEvent'
    assert self._wasSetSegment, 'No prior call to setSegmentString.'
    self._initFilterPipe(pointerEvent.viewPos)
    self._wasPointerPress = True
    # Do not start timer until pointerMoveEvent
    # Do not setGenerating(True) until pointerMoveEvents

  
  def pointerReleaseEvent(self, pointerEvent):
    ''' Client call to end freehand drawing. '''
    assert self._wasPointerPress
    self.stopTimer()  # Can stop even if not started.
    if self.isGenerating():
      # Don't close unless generating, since it flushes and creates at least one segment
      self._closeFilterPipe()
    else:
      # leave pipe in initial state
      assert self.path.countSegments == 0
      pass
    
    self.pathHeadGhost.hide() # Hide.  Client knows about it but shouldn't be concerned with hiding, and may be reusing it.
    #print "Final segment count", self.path.countSegments()
    self._resetState()
    
    
  
  def isGenerating(self):
    ''' Is pointer button down and at least one pointerEvent received. '''
    return self._wasPointerMove
  
  def setGenerating(self, truth):
    ''' Set flag indicating closed generators, not accepting pointerEvents. '''
    self._wasPointerMove = truth
  
  
  '''
  Timer
  
  If elapsed time in milliseconds between pointer moves is greater, flush pipeline 
  TODO make this a parameter, and use it below.
  MAX_POINTER_ELAPSED_FOR_SMOOTH = 100
  '''
  def createTimer(self):
    self.timer = QTimer()
    self.timer.setSingleShot(True)
    self.timer.timeout.connect(self.handleTimeout)
    
  def restartTimer(self, position):
    '''
    Start a timer showing how long we have been at position (without receiving another position.)
    '''
    self.lastSentPosition = position
    self.timer.stop()
    self.timer.start(300)
  
  def stopTimer(self):
    self.timer.stop()
  
  
  def handleTimeout(self):
    ''' 
    Timeout after previous pointerMoveEvent. 
    
    Resend the same position we previously sent.
    
    It is USUALLY only resent once (since timer is not restarted until pointerMoveEvent)
    but a subsequent pointerMoveEvent may also be (and send) the same position,
    and it too could timeout.
    But we don't prevent forcing the same position more than once consecutively.
    '''
    #print("Timeout")
    # Resend lastSentPosition, forced (flush)
    self.turnGenerator.send((self.lastSentPosition, True))
    
    
    
  """
  OLD: In new design, closing pipe causes flush which generates final segments.
  
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
  """
  
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
    Map from device coords (pipeline input) to freehandTool internal CS (which is Scene CS.)
    Result is real valued, mappable to Local CS of SegmentString.
    
    Depends on Qt.
    '''
    '''
    Can't: assert isinstance(pointVCS, PointerPoint), str(pointVCS),
    since PathLine.p1(), p2() methods return QPoint.
    '''
    assert isinstance(pointVCS.x(), int)
    assert isinstance(pointVCS.y(), int)
    
    """
    OLD
    Hack: tool knows segmentString which knows scene which knows view which can map VCS to SCS
    result = self.path.scene().views()[0].mapToScene(pointVCS)
    """
    result = self.view.mapToScene(pointVCS) # self knows it's view which maps
    #assert isinstance(result, QPointF)
    return result
