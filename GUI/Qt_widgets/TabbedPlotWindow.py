# -*- coding: utf-8 -*-
"""
"""
from PyQt4 import QtGui, QtCore
import sys
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QTAgg as NavigationToolbar
from matplotlib.figure import Figure
from pylab import *
from random import random

import logging

logging.basicConfig(level=logging.WARNING)
module_logger = logging.getLogger(__name__)
module_logger.setLevel(logging.DEBUG)

class MPLplotter(QtGui.QWidget):
  """
  This creates a plotting area with a MPL toolbar.

  This is called for each tabbed sheet that needs a plot window.  The
  toolbar belongs to the canvas.

  Public attributes::
    fig -    a Figure() instance
    canvas - a FigureCanvas() instance
  """
  def __init__(self):
    """
    Instantiate MPLplotter

    It lays out the canvas and the toolbar
    """
    super(MPLplotter,self).__init__()
    self.fig = Figure()
    self.fig.hold(False)
    self.canvas = MPLcanvas(self.fig, self)
    vlayout = QtGui.QVBoxLayout()
    vlayout.addWidget(self.canvas)
    vlayout.addWidget(self.canvas.toolbar)
    self.setLayout(vlayout)
    self.canvas.show()

class MPLcanvas(FigureCanvas):
  """
  A canvas with a toolbar
  """
  def __init__(self, fig, window):
    """
    Instantiate the canvas and add a toolbar

    @param fig : the figure which holds the canvas
    @type  fig : Figure() instance

    @param window : the widget in which the figure is defined
    @type  window : QWidget() instance
    """
    FigureCanvas.__init__(self, fig)
    self.toolbar = NavigationToolbar(self, window)
    
class TabbedPlotWindow(QtGui.QTabWidget):
  """
  A separate tabbed window for plots (and possibly other things)
  """
  def __init__(self, num_tabs=0, names=[], fill=False):
    """
    Instantiate a separate tabbed plot window

    Either num_tabs or names must be specified or an exception will be raised
    
    @param num_tabs : optional number of tabs
    @type  num_tabs : int

    @param names : optional list of tab names
    @type  names : list of str
    """
    self.logger = logging.getLogger(__name__+".TabbedPlotWindow")
    if num_tabs == 0 and names == []:
      raise RuntimeError("No tabs specified")
    elif num_tabs == 0:
      num_tabs = len(names)
    elif len(names) < num_tabs:
      for i in range(len(names),num_tabs):
        names.append("Tab "+str(i))
    self.logger.debug("Names: %s",str(names))
    super(TabbedPlotWindow,self).__init__()
    self.plottab = {}
    self.axes = {}
    for tab in range(num_tabs):
      self.logger.debug("Making plot page %d",tab)
      self.plottab[tab] = MPLplotter()
      self.addTab(self.plottab[tab],names[tab])
      self.make_plot(tab,rows=2,columns=2,fill=fill)
    self.setWindowTitle('Widgets Inside Tabs')
    self.show()

  def make_plot(self, tab, rows=1, columns=1, fill=fill):
    """
    Create the subplots for a tab page

    For testing purposes this draws a graph of random numbers by default.
    For ordinary use, set Fill to False and then invoke::
      self.axes[tab][subplot].plot(...)

    @param tab : the tabbed sheet on which the grapgs will be configured
    @type  tab : int

    @param rows : number of subplot rows
    @type  rows : int

    @param columns : number of subplot columns
    @type  columns : int

    @param fill : generate a dummy plot if True (default)
    @type  fill : bool
    """
    num_subplots = rows*columns
    self.axes[tab] = {}
    if fill:
      x = range(100)
      y = [random() for i in range(100)]
    for i in range(num_subplots):
      self.logger.debug("Making subplot %d for tab %d",i,tab)
      self.axes[tab][i] = self.plottab[tab].fig.add_subplot(rows,columns,i+1)
      if fill:
        self.lines[tab] = self.axes[tab][i].plot(x,y)
      self.logger.debug("axes: %s",str(self.axes))
    self.plottab[tab].canvas.show()

if __name__ == "__main__":
  app = QtGui.QApplication(sys.argv)
  myapp = TabbedPlotWindow(names=["One","Two","Three"],fill=True)
  myapp.show()
  sys.exit(app.exec_())
  