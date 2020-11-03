# -*- coding: utf-8 -*-
'''
selector - GUIs to allow selection from a pre-defined set of states

A selector could be a Nx1 or 1xN switch or a step attenuator.  A selector
group would be a bunch of similar selectors in parallel.
'''

from PyQt4 import QtCore, QtGui
from Qt_widgets import slotgen, SignalMaker
from support.text import longest_text
import logging

mylogger = logging.getLogger("__main__."+__name__)

class MultiSelectorForm(QtGui.QWidget):
  """
  Class to display/select the state of a group of selectors

  Public attributes::
   - num_selectors: number of selectors in the group
   - state[]:           a dictionary with the state of each selector
   - label_text:      text for the labels
   - label_template:  alternate text for label to be followed by index number
   - button_text:     text for buttons, obtained from Selector_Form()
   - button_template: alternate text for button to be followed by index number
  """
  def __init__(self, num_selectors,
                     label_text = [],
                     label_template = "Channel",
                     button_text = [],
                     button_template = "Port",
                     buttons = 1,
                     title="MultiSwitch"):
    """
    Create a multi-selector form

    The form consists of a label for each selector, either taken from
    a list of labels or else consisting of a prefix and a number.  The
    buttons are labeled with the selector state.
    
    @param num_selectors : number of selectors on the form
    @type  num_selectors : int

    @param label_text : optional individual labels for the selectors
    @type  label_text : list of str
    
    @param label_template : prefix for the selector number if label not given
    @type  label_template : str

    @param button_text : optional text for the button selections
    @type  button_text : list of str
    
    @param button_template : prefix for the button state
    @type  button_template : str

    @param buttons : number of buttons if button_text is not given
    @type  buttons : int

    @param title : title for the form
    @type  title : str
    """
    super(MultiSelectorForm, self).__init__()
    self.num_selectors   = num_selectors
    self.label_text      = label_text
    self.label_template  = label_template
    self.button_template = button_template
    if button_text:
      self.button_text = button_text
    else:
      self.button_text = [""]*buttons
    self.title=title
    self.state = {}

    self.signal = SignalMaker()

  def setupUi(self):
    """
    Set up the UI
    """
    mylogger.debug("Setting up multi-selector form")

    # make a group box widget
    self.groupbox = QtGui.QGroupBox("Groupbox")
    #self.groupbox.setObjectName("frame")
    self.groupbox.setTitle(self.title)
    self.horizontalLayout = QtGui.QHBoxLayout(self.groupbox)
    self.horizontalLayout.setObjectName("horizontalLayout")

    self.label = {}
    verticalLayout = {}
    self.pushButton = {}
    verticalLabelLayout = QtGui.QVBoxLayout()
    labelRow0 = QtGui.QLabel("Channel")
    verticalLabelLayout.addWidget(labelRow0)
    labelRow1 = QtGui.QLabel("Input")
    verticalLabelLayout.addWidget(labelRow1)
    self.horizontalLayout.addLayout(verticalLabelLayout)
    
    for index in range(self.num_selectors):
      self.C[index] = -1
      # make a vertical layout for the label and button
      verticalLayout[index] = QtGui.QVBoxLayout()
      # add the label to the layout
      self.label[index] = QtGui.QLabel(self.groupbox)
      self.label[index].setFrameShape(QtGui.QFrame.Panel)
      self.label[index].setAlignment(QtCore.Qt.AlignCenter)
      self.set_label_text(index)
      verticalLayout[index].addWidget(self.label[index])
      # add the pushbutton to the layout
      self.pushButton[index] = QtGui.QPushButton(self.groupbox)
      self.set_button_text(index, None, text="Make selection")
      verticalLayout[index].addWidget(self.pushButton[index])
      self.horizontalLayout.addLayout(verticalLayout[index])
      
      mylogger.debug("Connecting multi-selector form pushbutton to popup %d",index)
      self.pushButton[index].clicked.connect(slotgen(index,self.popup))
    self.setLayout(self.horizontalLayout)

  def set_label_text(self,index):
    """
    Put text in the label above each button

    @param index : the button index
    @type  index : int
    """
    if self.label_text:
      try:
        text = self.label_text[index]
        if not text:
          text = self.label_template+" "+str(index)
      except IndexError:
        text = self.label_template+" "+str(index)
    else:
      text = self.label_template+" "+str(index)
    self.label[index].setText(text)
    
  def set_button_text(self, index, state, text=None):
    """
    Label a selector button with the current selection

    @param index : the button index
    @type  index : int

    @param state : the current state of the selector
    @type  state : int
    """
    if text:
      pass
    elif self.button_text:
      if self.button_text[state]:
        text = self.button_text[state]
      else:
        text = self.button_template+" "+str(state)
    else:
      text = self.button_template+" "+str(state)
    self.pushButton[index].setText(QtGui.QApplication.translate("Form2",
                                   text, None, QtGui.QApplication.UnicodeUTF8))

  def popup(self, index, dummy):
    """
    Pop up a 1xN selector if a button is pressed

    @param index : ID of the selector
    @type  index : int

    @param dummy : value created by 'clicked' signal
    @type  dummy : bool
    """
    mylogger.debug("multi-selector form popup(%d) invoked",index)
    self.dialog = Selector_Form(index)
    mylogger.debug("dialog is type %s", type(self.dialog))
    self.dialog.setupUi(self.button_text, label_default="Port", cols=2)
    self.dialog.setWindowTitle("IF "+str(index))
    self.dialog.show()
    self.dialog.signal.stateChanged.connect(
                                           slotgen(index,self.update_selector))
    mylogger.debug("multi-selector form popup(%d) completed",index)

  def update_selector(self, index, new_state=-1):
    """
    Update the state of a selector in a group

    This will update the selector button text if a new state is provided.
    Else it will open a window to allow the user to select a new state.
    If a state is provided either way, the button text will be set to
    that of the new state.  Otherwise, the state is -1 and the text "Unknown".

    @param index : the I.D. of the selector to be updated
    @type  index : int

    @param new_state : optional new state if known
    @type  new_state : int
    """
    mylogger.debug("update_selector invoked for switch %d",index)
    if new_state > -1:
      self.state[index] = new_state
    else:
      try:
        self.state[index] = self.dialog.state
        self.dialog.close()
      except AttributeError:
        # program has not yet set the state
        self.state[index] = new_state
        self.set_button_text(index,-1,text="Unknown")
    self.set_button_text(index, self.state[index])
    mylogger.debug("new state for switch %d is %d",
                   index, self.state[index])
    self.current_selector = index
    self.signal.stateChanged.emit()
    
class Selector_Form(QtGui.QDialog):
  """
  Nx1 or 1xN selector widget
  """
  def __init__(self, switch):
    """
    Create instance of selector widget

    @param switch : selector ID
    @type  switch : int
    """
    super(Selector_Form, self).__init__()
    self.ID = switch
    self.state = -1

    self.signal = SignalMaker()
    mylogger.debug("Nx1 selector %d form instantiated", self.ID)

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
    mylogger.debug("setting up Nx1 selector form")
    rows = len(labels)
    self.rows = rows/cols + (rows % cols)
    self.cols = cols
    mylogger.debug("%d rows x %d cols", self.rows,self.cols)
    
    self.gridLayout = QtGui.QGridLayout()
    self.radioButton = {}
    rb_action = {}
    for row in range(self.rows):
      for col in range(self.cols):
        index = col*self.rows + row
        self.radioButton[index] = QtGui.QRadioButton()
        self.label_radiobutton(labels,index,label_default)
        self.gridLayout.addWidget(self.radioButton[index], row, col, 1, 1)
        this_slot = slotgen((self.ID,index),self.send_signal)
        QtCore.QObject.connect(self.radioButton[index],
                               QtCore.SIGNAL("clicked()"),
                               this_slot)
    self.setLayout(self.gridLayout)
    mylogger.debug("Nx1 selector %d setup completed", self.ID)

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
    if labels[index]:
      self.radioButton[index].setText(QtGui.QApplication.translate("gridLayout",
                                      labels[index],
                                      None,
                                      QtGui.QApplication.UnicodeUTF8))
    else:
      self.radioButton[index].setText(QtGui.QApplication.translate("gridLayout",
                                      label_default+" "+str(index),
                                      None,
                                      QtGui.QApplication.UnicodeUTF8))

  def send_signal(self,*args):
    """
    Register the selected value
    """
    self.last_switch_ID, self.state = args
    mylogger.debug("Selected input %d for switch %d",
                   self.state, self.last_switch_ID)
    self.signal.stateChanged.emit()
