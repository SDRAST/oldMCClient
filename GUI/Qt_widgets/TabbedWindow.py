# -*- coding: utf-8 -*-
"""
"""
from PyQt4 import QtGui, QtCore
import sys
import logging

module_logger = logging.getLogger(__name__)

    
class TabbedWindow(QtGui.QTabWidget):
  """
  A separate tabbed window for plots (and possibly other things)
  """
  def __init__(self, frames, names=[]):
    """
    Instantiate a separate tabbed plot window for each frame

    @param frames : widgets to appear on each tab
    @type  frames : dict of widgets

    @param names : optional ordered list of frame keys
    @type  names : list of str
    """
    super(TabbedWindow,self).__init__()
    if len(frames) == 0 and names == []:
      raise RuntimeError("__init__: No tabs specified")
    elif names == []:
      names = frames.keys()
    elif len(names) < len(frames):
      count = 0
      for key in frames.keys():
        try:
          names.index(key)
        except ValueError:
          count += 1
          names.append(key)
    module_logger.debug("__init__: Names: %s",str(names))
    self.frames = {}
    for tab in names:
      module_logger.debug("__init__: Making tabbed page %s",tab)
      self.frames[tab] = frames[tab]
      self.addTab(self.frames[tab],tab)


if __name__ == "__main__":
  mylogger = logging.getLogger()
  mylogger.setLevel(logging.DEBUG)
  
  app = QtGui.QApplication(sys.argv)
  pixmap = QtGui.QPixmap("png/1.png")
  lbl = QtGui.QLabel()
  lbl.setPixmap(pixmap)
  qle = QtGui.QLineEdit()

  frames = {'One': lbl, 'Two': qle}
  myapp = TabbedWindow(frames, names=["Two","One"])
  myapp.show()
  sys.exit(app.exec_())
  