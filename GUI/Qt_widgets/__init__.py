"""
module to provide Qt4 support
"""
import logging
from PyQt5 import QtGui,QtCore

module_logger = logging.getLogger(__name__)

# ------------------------------ module classes -------------------------------

class SignalMaker(QtCore.QObject):
  """
  Create special purpose signals

  This creates a signal object and defines signals as class variables so that
  other objects can have an instance of this as an attribute and emit or listen
  for defined signals.  For example::
    class Selector_Form(QtGui.QDialog):
      def __init__(self):
        self.signal = SignalMaker()
      def send_signal(self,*args):
        self.signal.stateChanged.emit()

    class ControlPanelGriddedFrame(QtGui.QFrame):
      def __init__(self, rows, parent = None):
        ...
      def switch_popup(self, *args):
        selector = Selector_Form(key, parent=self)
        ...
        selector.signal.stateChanged.connect(
          slotgen((selector,key), selector.update_selector))
  In this a Selector_Form instance emits a 'stateChanged' signal, the
  ControlPanelGriddedFrame instance will see it an invoke the method
  update_selector.
  """
  closeApp     = QtCore.pyqtSignal()
  stateChanged = QtCore.pyqtSignal()
  # This one is predefined for QDial, QScrollBar and QSlider
  valueChanged = QtCore.pyqtSignal(float)
  
# ------------------------------- module methods ------------------------------

def slotgen(extra_arg, slot):
  """
  Generate a slot with an additional argument

  Thanks to Diez B. Roggisch in
  http://bytes.com/topic/python/answers/712902-\
    pyqt-parameters-when-connecting-signal-method

  @param extra_arg : extra argument(s) to be passed to slot

  @param slot : an action slot (function invoked bu signal)
  """
  def _slot(*args):
    """
    Create a temporary slot with the extra argument prepended
    """
    if type(extra_arg) == tuple:
      return slot(*(extra_arg + args))
    else:
      return slot(*((extra_arg,) + args))
  return _slot

def slot_wrapper(*args):
  """
  Modifies a slot to add a post-action action

  An example might be where the action updates a radiobutton group
  and the post-action action is to update the entire parent GUI.

  Example::
        wrapped_slot = slotgen((action,
                                parent.refresh_UI,
                                parent.column,
                                title,
                                index),
                               slot_wrapper)
        #self.buttons[index].clicked.connect(request)
        self.buttons[index].clicked.connect(wrapped_slot)

  @param args[0] : original slot action
  @type  args[0] : function

  @param args[1] : post-action action
  @type  args[1] : function

  @param args[2:] : extra arguments for args[0]
  """
  args[0](*args[2:])
  args[1]()

def create_action(widget, text, slot=None, shortcut=None,
                      icon=None, tip=None, checkable=False,
                      signal="triggered()"):
  """
  This is a convenience for creating menu action buttons.

  It must be called with 'self' as the first argument.  It makes creating
  menus easier.

  @param widget : the GUI which has the menu
  @type  widget : probably a QMainWindow

  @param text : the menu item text
  @type  text : str

  @param slot : the slot to be invoked by the signal
  @type  slot : function()

  @param shortcut : optional keystroke to invoked menu item
  @type  shortcut : str

  @param icon : path to icon to decorate the menu item
  @type  icon : str

  @param tip : pop-up to displace if mouse hovers over menu item
  @type  tip : str

  @param checkable : has checkbox to toggle state
  @type  checkable : bool

  @param signal : signal emited when menu item is invoked
  """
  action = QtGui.QAction(text, widget)
  if icon is not None:
    action.setIcon(QIcon(":/%s.png" % icon))
  if shortcut is not None:
    action.setShortcut(shortcut)
  if tip is not None:
    action.setToolTip(tip)
    action.setStatusTip(tip)
  if slot is not None:
    widget.connect(action, QtCore.SIGNAL(signal), slot)
  if checkable:
    action.setCheckable(True)
  return action

def add_actions(target, actions):
  """
  This is a convenience function for adding a list of menu button actions
  to a menu button.

  @param target : menu item to which actions will be added
  @type  target : QMainWindow.menuBar() menu

  @param actions : actions
  @type  actions : tuple
  """
  for action in actions:
    if action is None:
      target.addSeparator()
    else:
      target.addAction(action)

def create_option_menu(parent, menu, text, action, option_list):
  """
  Add an option selection item to a menu.

  On selection, the selected QAction object is passed to the action
  as a parameter.  The object method text() contains the selection label text.

  @param parent : the parent of the menu
  @type  parent : QMainWindow

  @param menu : the menu for this menu item
  @type  menu : QMenu

  @param text : label for the menu item
  @type  text : str

  @param action : parent method to invoke when a selection is made
  @type  action : callable (function)

  @param option_list : list of options
  @type  option_list : list of str
  """
  option_menu = menu.addMenu(text)

  groupActions = QtGui.QActionGroup(menu)
  groupActions.setExclusive(True) # only one selection possible
  parent.connect(groupActions,
                 QtCore.SIGNAL("triggered (QAction *)"),
                 action)
  option = {}
  for opt in option_list:
    option[opt] = option_menu.addAction(opt)
    option[opt].setCheckable(True)
    groupActions.addAction(option[opt])
  return option_menu
