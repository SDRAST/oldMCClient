"""
Module provides dialog window to select one from many using radiobuttons.
"""
from PyQt4 import QtCore, QtGui
import logging

from Qt_widgets import slotgen, SignalMaker

mylogger = logging.getLogger("__main__."+__name__)

class Selector_Form(QtGui.QDialog):
  """
  Nx1 or 1xN selector widget

  The form is a dialog window with radio buttons which allows a selection of
  one out of N.  When the selection is made, it changes the text on the button
  on the parent which invoked pop-up.  It also passes a signal to the top-level
  window so it can implement the selection.
  """
  def __init__(self, key, parent=None, state=-1, button_text=None):
    """
    Create instance of selector widget

    @param key : selector ID
    @type  key : int
    """
    super(Selector_Form, self).__init__()
    self.logger = logging.getLogger(__name__+".Selector_Form")
    self.logger.debug("logger is %s", self.logger.name)
    self.ID = key
    self.parent = parent
    self.state = state
    self.button_text = button_text

    self.signal = SignalMaker()
    self.logger.debug("__init__: Nx1 selector %s form instantiated", self)

  def setupUi(self, labels, label_default="Port", cols=1):
    """
    Generate the radiobutton form.

    When the state of a button is changed, it sends a signal to that effect.
    The parent form, the MultiSelectorForm() instance, is connected to that
    signal and takes appropriate action.

    @param labels : labels for the selector radiobuttons
    @type  labels : list of str or empty list

    @param label_default : Prefix for selection number if no label is given
    @type  label_default : str

    @param cols : number of radiobutton column
    @type  cols : int
    """
    self.logger.debug("setupUI: setting up Nx1 selector form")
    rows = len(labels)
    self.rows = rows/cols + (rows % cols)
    self.cols = cols
    self.logger.debug("setupUI: %d rows x %d cols", self.rows,self.cols)

    self.gridLayout = QtGui.QGridLayout()
    self.radioButton = {}
    rb_action = {}
    for row in range(self.rows):
      for col in range(self.cols):
        index = col*self.rows + row
        self.radioButton[index] = QtGui.QRadioButton()
        self.label_radiobutton(labels,index,label_default)
        self.gridLayout.addWidget(self.radioButton[index], row, col, 1, 1)
        QtCore.QObject.connect(self.radioButton[index],
                               QtCore.SIGNAL("clicked()"),
                               slotgen((self.ID,index),self.send_signal))
    self.setLayout(self.gridLayout)
    self.logger.debug("setupUI: Nx1 selector %s setup completed", self.ID)

  def label_radiobutton(self, labels, index, label_default):
    """
    Put text on the button, either specified in labels, or a default

    @param labels : text next to each radio button
    @type  labels : list of str

    @param index : ID for the MultiSelectorForm column
    @type  index : int

    @param label_default : text to use with button number if not in labels
    @type  label_default : str
    """
    try:
      if labels[index]:
        self.radioButton[index].setText(QtGui.QApplication.translate(
                                      "gridLayout",
                                      labels[index],
                                      None,
                                      QtGui.QApplication.UnicodeUTF8))
      else:
        self.radioButton[index].setText(QtGui.QApplication.translate(
                                      "gridLayout",
                                      label_default+" "+str(index),
                                      None,
                                      QtGui.QApplication.UnicodeUTF8))
    except IndexError:
      self.radioButton[index].setText("None")
      self.radioButton[index].setDisabled(True)

  def send_signal(self,*args):
    """
    Register the selected value
    """
    self.last_switch_ID, self.state = args
    self.logger.debug(" send_signal: selected input %d for switch %s",
                   self.state, self.last_switch_ID)
    self.signal.stateChanged.emit()

  def update_selector(self, selector, key, rowname, new_state=-1):
    """
    Update the state of a selector in a group

    This will update the selector button text if a new state is provided.
    Else it will open a window to allow the user to select a new state.
    If a state is provided either way, the button text will be set to
    that of the new state.  Otherwise, the state is -1 and the text "Unknown".

    Additionally it invokes a method to actually set the switch.

    @param new_state : optional new state if known
    @type  new_state : int
    """
    self.logger.debug("update_selector: %s invoked with switch %s",
                   self, self.switch)
    if new_state > -1:
      self.state = new_state
    else:
      try:
        self.parent._set_switch_button_text(self.switch, self.state)
      except AttributeError:
        # program has not yet set the state
        self.state = new_state
        self.parent._set_switch_button_text(self.switch, -1,
                                            "Input ", text="Unknown")
    self.logger.debug("update_selector: new state for switch %s is %d",
                        key, self.state)
    self.logger.debug("update_selector: switch %s in row %s was changed",
                        self.ID, rowname)
    self.parent.parent.switch_changed(self, rowname, self.ID)
    self.close()
