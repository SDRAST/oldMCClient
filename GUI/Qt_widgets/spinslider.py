# -*- coding: utf-8 -*-
"""
"""
from PyQt5 import QtCore, QtGui, QtWidgets

import logging
from MCClient.GUI.Qt_widgets import SignalMaker

class SpinSlider(QtWidgets.QFrame):
  """
  Combines a coupled slider and spinbox in one widget.

  The slider can be used for coarse setting and the spinbox for precise
  setting.
  """
  def __init__(self, parent, value, minval=0, maxval=2000, jump=100):
    """
    Initializes a SpinSlider instance.

    @param parent : the object which created this instance of SpinSlider
    @type  parent : QWidget

    @param minval : minimum value for the range
    @type  minval : int

    @param maxval : maximum value for the range
    @type  maxval : int

    @param jump : change in value when clicking beside the slider
    @type  jump : int
    """
    QtGui.QFrame.__init__(self, parent)
    self.logger = logging.getLogger(__name__)
    self.logger.debug("SpinSlider instance %s is child of %s",
                      self, parent)
    self.value = minval
    self.signal = SignalMaker()
    self.setupUi(parent,value,minval,maxval,jump)
    
  def setupUi(self,parent,value,minval,maxval,jump):
    """
    Creates the widget.

    @param parent : the object which created this instance of SpinSlider
    @type  parent : QWidget

    @param minval : minimum value for the range
    @type  minval : int

    @param maxval : maximum value for the range
    @type  maxval : int

    @param jump : change in value when clicking beside the slider
    @type  jump : int
    """
    widget = self # QtGui.QFrame(parent)
    widget.setFrameShape(QtGui.QFrame.Panel)
    widget.resize(100,60)
    layout = QtGui.QVBoxLayout()
    layout.addStretch(1)

    toplayout = QtGui.QHBoxLayout()
    toplayout.addStretch(1)
    
    spin = QtGui.QSpinBox()
    spin.resize(60,30)
    spin.setMinimum(minval)
    spin.setMaximum(maxval)
    spin.setSingleStep(1)
    spin.setValue(value)
    toplayout.addWidget(spin)

    self.push = QtGui.QCheckBox()
    self.push.resize(30,30)
    self.push.setChecked(True)
    toplayout.addWidget(self.push)

    layout.addLayout(toplayout)
    
    slide = QtGui.QSlider()
    slide.resize(100,30)
    slide.setMinimum(minval)
    slide.setMaximum(maxval)
    slide.setSingleStep(1)
    slide.setPageStep(jump)
    slide.setValue(value)
    slide.setOrientation(QtCore.Qt.Horizontal)
    layout.addWidget(slide)

    widget.setLayout(layout)

    QtCore.QObject.connect(slide,
                           QtCore.SIGNAL("valueChanged(int)"),
                           spin.setValue)
    QtCore.QObject.connect(spin,
                           QtCore.SIGNAL("valueChanged(int)"),
                           slide.setValue)
    QtCore.QObject.connect(slide,
                           QtCore.SIGNAL("valueChanged(int)"),
                           self.valueChanged)
    QtCore.QObject.connect(self.push,
                           QtCore.SIGNAL("clicked()"),
                           self.setValue)

  def valueChanged(self, *args):
    """
    Emits a signal when the value is changed.

    Use it like this::
      ss = SpinSlider(self,minval=minval,maxval=maxval)
      ss.signal.stateChanged.connect(action)

      def action():
        print "new value = %s" % ss.value
    """
    self.push.setChecked(False)
    self.value = args[0]
    self.logger.debug("%s valueChanged: %s", self, self.value)

  def setValue(self, *args):
    """
    """
    self.logger.debug("%s setValue called with %s", self, self.value)
    self.signal.valueChanged.emit(self.value)
    
