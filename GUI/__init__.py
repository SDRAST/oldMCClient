from PyQt5 import QtGui,QtCore, QtWidgets
import logging

from support.dicts import flattenDict
from MCClient.GUI.Qt_widgets import slotgen
from MCClient.GUI.Qt_widgets.spinslider import SpinSlider
from MCClient.GUI.Qt_widgets.general_dial import GeneralDial

class ControlPanelGriddedFrame(QtWidgets.QFrame):
  """
  Automatically generated frame with a grid of M&C widgets

  The following widget types are recognized::
   labels       - text or values
   checkbuttons - True or false selection
   pushbuttons  - cause an action
   dials        - set a value within a range of values
   switches     - 1xN or Nx1 selection; button invokes a radiobutton form

  Each row in the frame is specified by an item in a list of rows passed
  as an argument for instantiating the class::
    Type (row[0])         - a string currently having one of the values:
                            'label', 'check', 'push', 'dial', 'switch'.
    Name (row[1])         - a unique name for this type of row.
    Devices (row[2])      - a dictionary of dictionaries whose contents depend
                            on the row's type.  The nested dictionaries are
                            indexed with ROACH number (int), an optional ADC
                            number (0 or 1), and an optional RF input number
                            (0 or 1). If only ROACH indices are given, the
                            widget will span all the columns for that widget.
                            Similarly if only ROACH and ADC numbers are given.
    Additional (rows[3:]) - specific to the row type. Check the doc string of
                            the method which creates the row.
  """
  def __init__(self, rows, parent = None):
    """
    Instantiate ControlPanelGriddedFrame()

    @param rows : ordered list of data for row of widgets (see class doc str)
    @type  rows : list

    @param parent : the object which instantiated this class
    @type  parent : object
    """
    QtGui.QFrame.__init__(self)

    self.logger = logging.getLogger(__name__+".ControlPanelGriddedFrame")
    self.logger.debug("logger is %s", self.logger.name)
    self.parent = parent
    self.gridLayout = QtGui.QGridLayout(self)
    self.columnize(rows)
    self.logger.debug("__init__: highest depth keys: %s",
                      str(self.highest_depth_keys))
    self.initUI(rows)

  def initUI(self,rows):
    """
    Initialize a rows and columns grid of monitor and control widgets.  The
    following keys specify the type of widget::
     'label'      - text, which could be updated to reflect dynamic values
     'check'      - to select or deselect an option
     'push'       - button to cause an action (e.g. perform a calibration)
     'dial'       - to set a value with a specified range
     'switch'     - a pushbutton with a pop-up to select one of many (e.g.
                    a signal source)
     'spinslider' - combination slider and spinbox (good for setting large
                    numbers to high precision
     'spinbox'    - standard spinbox for selecting values in a range
     'custom'     - special widget with a unique functionality
    """
    self.labels = {}
    self.checkbuttons = {}
    self.pushbuttons = {}
    self.dials = {}
    self.switches = {}
    self.synth = {}
    self.custom = {}
    rownum = 0
    for row in rows:
      self.logger.debug("__init__: making type %s row '%s'",
                        row['widget'], row['name'])
      if row['widget'] == 'label':
        keyword_args = {}
        if row.has_key('format'):
          keyword_args['format'] = row['format']
        if row.has_key('slots'):
          keyword_args['slots'] = row['slots']
        self.labels[row['name']] = self.make_label_row(
                                       rownum,
                                       row['name'],
                                       row['values'],
                                       **keyword_args)
      elif row['widget'] == 'check':
        self.checkbuttons[row['name']] = self.make_checkbutton_row(
                                       rownum,
                                       row['name'],
                                       row['values'],
                                       row['action'])
      elif row['widget'] == 'push':
        self.pushbuttons[row['name']] = self.make_pushbutton_row(
                                       rownum,
                                       row['name'],
                                       row['values'],
                                       row['action'])
      elif row['widget'] == 'dial':
        self.dials[row['name']] = self.make_dial_row(
                                       rownum,
                                       row['name'],
                                       row['values'],
                                       row['range'],
                                       row['format'],
                                       row['converters'][1],
                                       row['converters'][0],
                                       row['action'])
      elif row['widget'] == 'switch':
        if row.has_key('label_template'):
          self.switches[row['name']] = self.make_switch_row(
                                       rownum,
                                       row['name'],
                                       row['values'],
                                       row['labels'],
                                       label_template = row['label_template'])
        else:
          self.switches[row['name']] = self.make_switch_row(
                                       rownum,
                                       row['name'],
                                       row['values'],
                                       row['labels'])
      elif row['widget'] == 'spinslider':
        if row.has_key('range'):
          self.synth[row['name']] = self.make_spinslider_row(
                                       rownum,
                                       row['name'],
                                       row['values'],
                                       row['action'],
                                       limits = row['range'])
        else:
          self.synth[row['name']] = self.make_spinslider_row(
                                       rownum,
                                       row['name'],
                                       row['values'],
                                       row['action'])

      elif row['widget'] == 'spinbox':
        if row.has_key('range'):
          self.synth[row['name']] = self.make_spinbox_row(
                                       rownum,
                                       row['name'],
                                       row['values'],
                                       row['action'],
                                       steps=row['range'])
        else:
          self.synth[row['name']] = self.make_spinbox_row(
                                       rownum,
                                       row['name'],
                                       row['values'],
                                       row['action'])
      elif row['widget'] == 'custom':
        self.custom[row['name']] = self.make_custom_row(
                                       rownum,
                                       row['name'],
                                       row['values'],
                                       row['widgets'])
      else:
        self.logger.warning("__init__: row type %s is unknown",row['widget'])
      rownum += 1

  def columnize(self,rows):
    """
    Extract information about multiply-indexed widgets to be gridded.

    One column will be created for each key in highest_depth_keys.
    Creates attribute::
     highest_depth_keys:      list of highest dimension keys

    @param rows : rows to be created in gridded frame
    @type  rows : list

    @return: tuple
    """
    dicts = []
    rekeyed = []
    flatdicts = []
    for row in rows:
      dicts.append(row['values'])
      keys = row['values'].keys()
      keys.sort()
      newdict = {}
      for index in range(len(keys)):
        key = keys[index]
        if type(key) == int:
          newdict[key] = row['values'][key]
        else:
          newdict[index] = row['values'][key]
      rekeyed.append(newdict)
    self.logger.debug("columnize: collected: %s", str(dicts))
    self.logger.debug("columnize: re-keyed: %s", str(rekeyed))
    for d in rekeyed:
      flatdicts.append(flattenDict(d))
    self.highest_depth_keys = self.get_highest_depth_keys(flatdicts)
    self.highest_depth_keys.sort()

  def get_highest_depth_keys(self,dictionaries):
    """
    This returns all the indices for the deepest key level.

    For example, if roach1 has one ADC with two inputs and roach2 has one
    ADC with one input it should return::
      [(0,0,0), (0,0,1), (1,0,0)]
    The widget positioning method then can match the widget index with this
    list to see what column the widget should go in.

    The keys in 'dictionaries' are tuples, obtained from flattenDict().
    Because the keys returned from this will be used to organize the columns
    of the grid, they must all use the same convention. We use a tuple of ints.
    """
    highest_depth = 0 # should become 3 for (roach, adc, rf)
    keyset = {}       # lists of keys indexed by depth
    self.logger.debug("get_highest_depth_keys: dicts: %s", dictionaries)
    for dictionary in dictionaries:
      self.logger.debug("get_highest_depth_keys: processing %s",
                        dictionary)
      keys = dictionary.keys()
      self.logger.debug("get_highest_depth_keys: processing depth 0 keys %s",
                        str(keys))
      if len(keys):
        if type(keys[0]) == tuple:
          depth = len(keys[0]) # We assume all the keys have the same depth
        else:
          # the key is a single integer
          depth = 1
        if depth >= highest_depth:
          highest_depth = depth
          self.logger.debug("get_highest_depth_keys: highest depth is now %d",
                            highest_depth)
          try:
            # See if there is a keyset for this depth
            keyset[depth]
          except KeyError:
            # If not, create it
            self.logger.debug(
                         "get_highest_depth_keys: created keyset for depth %d",
                         depth)
            keyset[depth] = []
          for key in keys:
            try:
              # Is this key already in the keyset?
              keyset[depth].index(key)
            except ValueError:
              # If not, add it
              keyset[depth].append(key)
      else:
        # empty dict
        pass
    self.logger.debug("get_highest_depth_keys: keysets: %s",str(keyset))
    highest_depth_keyset = keyset[highest_depth]
    # At the very minimum there must be an entry for each ROACH
    if len(highest_depth_keyset) < len(keyset[1]):
      # create missing key(s)
      required_keys = keyset[1]
      for index in range(len(required_keys)):
        for depth in range(2,highest_depth+1):
          required_keys[index] += (0,)
      self.logger.debug("get_highest_keys: required_keys: %s",required_keys)
      for key in required_keys:
        try:
          highest_depth_keyset.index(key)
        except ValueError:
          position = key[0]
          highest_depth_keyset.insert(position,key)
    self.logger.debug("get_highest_keys: got %s",highest_depth_keyset)
    return highest_depth_keyset

  def _position_widget(self, key, keylen, col):
    """
    Positions one widget in a row.

    All the widgets are assumed to have the same key dimension which is
    determined from the first key and passed in as an argument.

    This determines how many columns a widget will occupy.

    @param key : key of the widget in a dict
    @type  key : tuple

    @param keylen : length of the key
    @type  keylen : int

    @param col : the column for the widget
    @type  col : int
    """
    colspan = 0
    self.logger.debug("_position_widget: processing key %s of length %d",
                      str(key), keylen)
    # Are any of the subkeys not integers?  If so, replace them.
    newkey = False
    for index in range(len(key)):
      if type(key[index]) != int:
        if index == 0:
          # Assume the last key is like ('roach1',0) or ('roach2',0)
          newkey = (int(key[0][-1])-1,)
        else:
          newkey = key[:index]+(index,)
        self.logger.log(5,
                      "_position_widget: non-integer key %s found at index %d",
                      str(key[index]),index)
        self.logger.log(5,'_position_widget: building new key: %s',str(newkey))
      else:
        if newkey:
          # keep on building the new key
          newkey += (key[index],)
    if newkey:
      self.logger.log(5,"_position_widget: %s replaced with: %s", str(key),
                        str(newkey))
    else:
      newkey = key

    num_keys_to_test = len(newkey)
    for testkey in self.highest_depth_keys:
      testpart = testkey[:num_keys_to_test]
      self.logger.log(5, "_position_widget: comparing %s to %s",
                            str(newkey), str(testpart))
      if newkey == testpart:
        colspan += 1
      else:
        continue
    self.logger.log(5,
                   "_position_widget: widget in column %d spanning %d columns",
                   col,colspan)
    return col, colspan

  def make_label_row(self, row, row_name, dictionary, **kwargs):
    """
    Make a row of labels in the grid

    Three parameters are required to describe the row.

    @param row : row number for positioning the widgets in the grid
    @type  row : int

    @param row_name : name of monitor data or control widget
    @type  row_name : str

    @param dictionary : values for the widgets in the row
    @type  dictionary : dict of whatever, defaulting to str
    """
    rowLabel = QtGui.QLabel(row_name)
    rowLabel.setSizePolicy(8,0)
    # the numeric arguments below are: row, column,rowspan, colspan
    self.gridLayout.addWidget(rowLabel, row, 0, 1, 1,
                              QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)
    self.logger.debug("make_label_row: processing dictionary: %s",
                      str(dictionary))
    flatdict = flattenDict(dictionary)
    keys = flatdict.keys()
    keys.sort()
    self.logger.debug("make_label_row: new keys for label row: %s", str(keys))
    labels = {}
    # the following code figures out where to put the widgets
    col = 1
    if len(keys):
      keylen = len(keys[0])
      if kwargs.has_key('format'):
        format = kwargs['format']
      else:
        format = "%s"
      for key in keys:
        col, colspan = self._position_widget(key,keylen,col)
        labels[key] = QtGui.QLabel()
        labels[key].setSizePolicy(8,0)
        self.gridLayout.addWidget(labels[key],
                                  row, col, 1, colspan,
                                  QtCore.Qt.AlignHCenter|QtCore.Qt.AlignTop)
        if flatdict[key]:
          labels[key].setText(format % flatdict[key])
          labels[key].setFrameShape(QtGui.QFrame.Panel)
        else:
          labels[key].setText("None")
        col += colspan
    #if kwargs.has_key('slots'):
    #  for pair in kwargs['slots']:
    #    signal = pair[0]
    #    self.logger.debug("make_label_row: signal = %s", signal)
    #    slot = pair[1]
    #    self.logger.debug("make_label_row: slot = %s", slot)
    #    signal.connect(slot)
    return labels

  def make_checkbutton_row(self, row, row_name, states, action):
    """
    Make a row of checkbuttons

    Four parameters are required to describe this row.

    @param row : row number
    @type  row : int

    @param row_name : name of monitor data
    @type  row_name : str

    @param states : checkbutton states
    @type  states : dict of bool

    @param action : method to invoke on state change
    @type  action : dict of functions
    """
    rowLabel = QtGui.QLabel(row_name)
    rowLabel.setSizePolicy(8,0)
    self.gridLayout.addWidget(rowLabel, row, 0, 1, 1,
                              QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)
    self.logger.debug("make_checkbutton_row: processing dictionary: %s",
                      str(states))
    flatdict = flattenDict(states)
    keys = flatdict.keys()
    keys.sort()
    self.logger.debug("make_checkbutton_row: new keys for checkbox row: %s",
                      str(keys))
    checkbuttons = {}
    col = 1
    if keys:
      keylen = len(keys[0])
      for key in keys:
        col, colspan = self._position_widget(key,keylen,col)
        checkbuttons[key] = QtGui.QCheckBox("On")
        checkbuttons[key].setSizePolicy(8,0)
        self.gridLayout.addWidget(checkbuttons[key],
                                  row, col, 1, colspan,
                                  QtCore.Qt.AlignHCenter|QtCore.Qt.AlignTop)
        if flatdict[key] == None:
          checkbuttons[key].setDisabled(True)
        else:
          checkbuttons[key].setChecked(flatdict[key])
          checkbuttons[key].clicked.connect(slotgen((self,row_name)+key,
                                                     action))
        col += colspan
    return checkbuttons

  def make_pushbutton_row(self, row, row_name, button_text, action):
    """
    Make a row of checkbuttons

    Four parameters are required to describe this row.

    @param row : row number
    @type  row : int

    @param row_name : name of monitor data
    @type  row_name : str

    @param button_text : dictionary of text to be put on the buttons
    @type  button_text : multiple depth dictionary

    @param action : methods to invoke on state change
    @type  action : dict of functions
    """
    rowLabel = QtGui.QLabel(row_name)
    self.gridLayout.addWidget(rowLabel, row, 0, 1, 1,
                              QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)
    self.logger.debug("make_pushbutton_row: processing dictionary: %s",
                      str(button_text))
    flatdict = flattenDict(button_text)
    keys = flatdict.keys()
    keys.sort()
    self.logger.debug("make_pushbutton_row: new keys for button row: %s",
                      str(keys))
    pushbuttons = {}
    col = 1
    keylen = len(keys[0])
    for key in keys:
      col, colspan = self._position_widget(key,keylen,col)
      pushbuttons[key] = QtGui.QPushButton(flatdict[key])
      self.gridLayout.addWidget(pushbuttons[key],
                                row, col, 1, colspan,
                                QtCore.Qt.AlignHCenter|QtCore.Qt.AlignTop)
      if flatdict[key] == None:
        pushbuttons[key].setDisabled(True)
      else:
        pushbuttons[key].clicked.connect(slotgen((self,row_name)+key, action))
      col += colspan
    return pushbuttons

  def make_dial_row(self, row, row_name,
                    values, value_range, format,
                    convertTo, convertFrom, action):
    """
    Make a row of dials

    Eight parameters are required to describe this row.

    @param row : row number
    @type  row : int

    @param row_name : name of monitor data
    @type  row_name : str

    @param values : dial state values
    @type  values : dict of float

    @param value_range : minimum and maximum value
    @type  value_range : tuple

    @param format : format for displayed values
    @type  format : str

    @param convertTo : converts dial integer to user value
    @type  convertTo : method

    @param convertFrom : converts user value to dial integer
    @ type convertFrom : method

    @param action : method to invoke on state change
    @type  action : dict of functions
    """
    rowLabel = QtGui.QLabel(row_name)
    self.gridLayout.addWidget(rowLabel, row, 0, 1, 1,
                              QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)
    self.logger.debug("make_dial_row: processing dictionary: %s", str(values))
    flatdict = flattenDict(values)
    keys = flatdict.keys()
    keys.sort()
    self.logger.debug("make_dial_row: new keys for dial row: %s", str(keys))
    dials = {}
    col = 1
    if keys:
      keylen = len(keys[0])
      for key in keys:
        col, colspan = self._position_widget(key,keylen,col)
        dials[key] = GeneralDial(value_range,
                                 format,
                                 convertFrom, convertTo)
        dials[key].setWrapping(False)
        dials[key].setNotchesVisible(True)
        self.gridLayout.addWidget(dials[key], row, col, 1, colspan,
                                QtCore.Qt.AlignHCenter|QtCore.Qt.AlignTop)
        if flatdict[key] == None:
          dials[key].setDisabled(True)
        else:
          dials[key].setRealValue(flatdict[key])
          dials[key].valueChanged.connect(slotgen((self,row_name)+key, action))
        col += colspan
    return dials

  def make_switch_row(self, row, row_name, states, inputs,
                      label_template="Input "):
    """
    Row of buttons to active radiobutton pop-ups.

    Typical use would be for a 1xN or Nx1 switch.

    Four parameters are required to describe this row.

    @param row : row number
    @type  row : int

    @param row_name : name of monitor data
    @type  row_name : str

    @param states : states of the switches
    @type  states : multi-level dict of ints

    @param inputs : names of N inputs or outputs
    @type  inputs : list of str

    @param label_template : generates label text if none is known
    @type  label_template : str
    """
    rowLabel = QtGui.QLabel(row_name)
    self.gridLayout.addWidget(rowLabel, row, 0, 1, 1,
                              QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)
    self.logger.debug("make_switch_row: processing dictionary: %s",
                      str(states))
    flatdict = flattenDict(states)
    keys = flatdict.keys()
    keys.sort()
    self.logger.debug("make_switch_row: new keys for switch row: %s",
                      str(keys))
    switches = {}
    col = 1
    if len(keys):
      keylen = len(keys[0])
      for key in keys:
        col, colspan = self._position_widget(key,keylen,col)
        value = flatdict[key]
        self.logger.debug("make_switch_row: key %s becomes %s", key, value)
        if value != 'None':
          switches[key] = QtGui.QPushButton(label_template+str(value))
          switches[key].inputs = inputs
          self._set_switch_button_text(switches[key], value, label_template)
        else:
          switches[key] = QtGui.QPushButton("None")
          switches[key].inputs = inputs
        self.logger.debug(
           "make_switch_row: connecting multi-selector pushbutton to popup %s",
           str(key))
        switches[key].clicked.connect(slotgen((self, row_name, key,
                                               switches[key]),
                                              self._switch_popup))
        self.gridLayout.addWidget(switches[key],
                                  row, col, 1, colspan,
                                  QtCore.Qt.AlignHCenter|QtCore.Qt.AlignTop)
        col += colspan
    return switches

  def make_spinslider_row(self, row, row_name, values, action, limits = []):
    """
    Note that 'step' does not follow the Python convention but the
    QSpinBox convention.
    """
    rowLabel = QtGui.QLabel(row_name)
    self.gridLayout.addWidget(rowLabel, row, 0, 1, 1,
                              QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)
    self.logger.debug("make_spinslider_row: processing dictionary: %s",
                      str(values))
    flatdict = flattenDict(values)
    keys = flatdict.keys()
    keys.sort()
    self.logger.debug("make_spinslider_row: new keys for dial row: %s",
                      str(keys))
    spinsliders = {}
    col = 1
    keylen = len(keys[0])
    for key in keys:
      col, colspan = self._position_widget(key,keylen,col)
      if limits:
        spinsliders[key] = SpinSlider(self,
                                      flatdict[key],
                                      minval=limits[0],
                                      maxval=limits[1])
      else:
        spinsliders[key] = SpinSlider(self,flatdict[key])
      self.gridLayout.addWidget(spinsliders[key], row, col, 1, colspan,
                                QtCore.Qt.AlignHCenter|QtCore.Qt.AlignTop)
      if flatdict[key] == None:
        spinsliders[key].setDisabled(True)
      else:
        spinsliders[key].setValue(flatdict[key])
        spinsliders[key].signal.valueChanged.connect(
                slotgen( (self,
                          row_name)+key+(spinsliders[key].value,),
                          action ))
      col += colspan
    return spinsliders

  def make_spinbox_row(self, row, row_name, values, action, steps=[]):
    """
    """
    rowLabel = QtGui.QLabel(row_name)
    self.gridLayout.addWidget(rowLabel, row, 0, 1, 1,
                              QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)
    self.logger.debug("make_spinbox_row: processing dictionary: %s",
                      str(values))
    flatdict = flattenDict(values)
    keys = flatdict.keys()
    keys.sort()
    self.logger.debug("make_spinslider_row: new keys for dial row: %s",
                      str(keys))
    spinboxes = {}
    col = 1
    keylen = len(keys[0])
    for key in keys:
      col, colspan = self._position_widget(key,keylen,col)
      spinboxes[key] = QtGui.QSpinBox(self)
      if steps:
        spinboxes[key].setRange(steps[0],steps[1])
        spinboxes[key].setSingleStep(steps[2])
      self.gridLayout.addWidget(spinboxes[key], row, col, 1, colspan,
                                QtCore.Qt.AlignHCenter|QtCore.Qt.AlignTop)
      if flatdict[key] == None:
        spinboxes[key].setDisabled(True)
      else:
        spinboxes[key].setValue(flatdict[key])
        spinboxes[key].valueChanged.connect(
                         slotgen((self,row_name)+key+(spinboxes[key].value(),),
                         action))
      col += colspan
    return spinboxes

  def make_custom_row(self, row, rowname, values, widgets):
    rowLabel = QtGui.QLabel(rowname)
    self.gridLayout.addWidget(rowLabel, row, 0, 1, 1,
                              QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)
    self.logger.debug("make_custom_row: processing dictionary: %s",
                      str(values))
    flatdict = flattenDict(values)
    keys = flatdict.keys()
    keys.sort()
    self.logger.debug("make_custom_row: new keys for custom row: %s",
                      str(keys))
    custom = {}
    col = 1
    keylen = len(keys[0])
    for key in keys:
      col, colspan = self._position_widget(key,keylen,col)
      if rowname == "Firmware":
        self.logger.debug("make_custom_row: column %s has firmware key %s",
                          key, flatdict[key])
        widget = widgets[flatdict[key]]
        self.logger.debug("make_custom_row: widget class is %s", widget)
        if widget:
          custom[key] = widget(self,key[0])
          self.logger.debug("make_custom_widget: at row %d, column %d",row,col)
          self.gridLayout.addWidget(custom[key], row, col, 1, colspan,
                                    QtCore.Qt.AlignHCenter|QtCore.Qt.AlignTop)
        else:
          custom[key] = None
      else:
        self.logger.error("make_custom_row: unknown category %s", rowname)
      col += colspan
    return custom

  def _set_switch_button_text(self, switch, state,
                              button_template="Sel ", text=None):
    """
    Label the button text of the specified switch with the current selection

    @param switch : the button receiving the text
    @type  switch : QPushButton instance

    @param state : the current state of the selector
    @type  state : int

    @param button_template : template for automatic name based on state
    @type  button_template : str

    @param text : text to override text based on template
    @type  text : str
    """
    self.logger.debug(
            "_set_switch_button_text: setting button %s to text for state %s",
            switch, state)
    if text:
      pass
    elif switch.inputs:
      self.logger.debug(
                     "_set_switch_button_text: text will be selected from %s",
                     switch.inputs)
      if state != None:
        if switch.inputs[state]:
          text = switch.inputs[state]
        else:
          text = button_template+" "+str(state)
      else:
        text = button_template+" "+str(state)
    else:
      text = button_template+" "+str(state)
    switch.setText(text)

  def _switch_popup(self, *args):
    """
    Pop up a 1xN selector if a button is pressed

    Arguments consist of a row name, a column key and the associated switch.
    Condition is something set by the widget.

    @param args : (rowname, key, switch, condition)
    @type  args : tuple of ints
    """
    self.logger.debug(" _switch_popup: invoked with %s",str(args))
    frame, rowname, key, switch, condition = args
    self.logger.debug(" _switch_popup: switch is %s", switch)
    selector = Selector_Form(key, parent=self)
    selector.switch = switch
    self.logger.debug(" _switch_popup: selector is type %s", type(selector))
    selector.setupUi(switch.inputs, label_default="Port", cols=2)
    selector.setWindowTitle("IF selection")
    selector.show()
    selector.signal.stateChanged.connect(
          slotgen((selector,key,rowname), selector.update_selector))
    self.logger.debug(
                     " _switch_popup: multi-selector form popup(%s) completed",
                     key)
