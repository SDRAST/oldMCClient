# -*- coding: utf-8 -*-
"""
A gridded monitor and control panel

The ControlPanelGriddedFrame() class will take a possibly nested dictionary
of values or functions.  In order to position the widgets correctly, the
dictionary keys on any level must be in sequential order, e.g., 0,1,2...
or 'a','b','c',...
"""
from PyQt4 import QtGui,QtCore
import logging
import sys
import time
import numpy
from random import random

from MonitorControl.BackEnds.ROACH1 import logpath
from MonitorControl.clients.Roach1.ManagerClient import ManagerClient
from MonitorControl.clients.Roach1.GUI import ControlPanelGriddedFrame
from MonitorControl.clients.Roach1.GUI.kurtosis_GUI import Ui_kurtosisMC
from Qt_widgets import SignalMaker
from Qt_widgets import create_action, add_actions, create_option_menu
from Qt_widgets.TabbedWindow import TabbedWindow
from Qt_widgets.TabbedPlotWindow import TabbedPlotWindow, MPLplotter
from support.pyro import cleanup_tunnels
from support.dicts import flattenDict
from support.logs import init_logging, get_loglevel, set_loglevel

module_logger = logging.getLogger(__name__)

module_logger.debug( "ManagerClient is %s", ManagerClient)

## ad hoc for now; this should go into the spreadsheet
## [u'hires_spec', u'kurt_spec', u'kurt_spec_r1', u'lores_spec', u'sao_spec']
firmware_widgets = {
  'None': None,       # when no firmware has been selected
  0: None,          # hires_spec
  1: Ui_kurtosisMC, # kurt_spec
  2: Ui_kurtosisMC, # kurt_spec_r1
  3: None,          # lores_spec
  4: None           # sao_spec
}

class MySignaller(SignalMaker):
  """
  Custom signals for the GUI application

  The arguments to the signal emit are passed to the action.
  gainChanged   is emitted when 'update_gain'     is called.
  signalChanged is emitted when 'update_RF_state' is called and
  .                        when 'switch_changed'  is called for IF row
  fwChanged     is emitted when 'switch_changed'  is called for firmware row
  """
  gainChanged   = QtCore.pyqtSignal(object,str,tuple,float,name='gainChanged')
  signalChanged = QtCore.pyqtSignal(object,str,tuple,float,
                                    name='signalChanged')
  fwChanged     = QtCore.pyqtSignal(object,str,tuple,str,name='fwChanged')

module_logger.debug(" MySignaller defined")

class ActionConfiguration(ManagerClient):
  """
  Describes the appearance and actions of the client GUI

  Public attributes::
    ADC_keys      - dict of numeric list of ADC keys for each roach index
    ADC_labels    - multilevel (roach index, ADC index) of ADC named
    fan_labels    -
    logger        - logger for this class instance
    MMS_opt_lbl   -
    optimize_lbl  - multilevel dict (roach, ADC, RF) with text "Go!"
    RF_keys       - multilevel dict (roach, ADC) of RF inputs
    RF_labels     - multilevel dict (roach, ADC, RF) with ADC labels
    roach_names   - dict of ROACH names (keyed with roach index)
    signal        - MySignaller instance

  Attributes inherited from ManagerClient::
    ADC_levels      - dict of ADC levels
    ADC_source      - number of IF switch output for this ADC
    amb_temps       - temps[roach][adc]['ambient']
    available       - dict of lists of available boffiles
    boffiles        - dict of running boffiles
    chip_temps      - temps[roach][adc]['IC']
    firmware        - dict of firmware parameters
    firmware_dict   - index of loaded boffile in list of available
    firmware_ID     - short name for loaded firmware
    firmware_index  - index of loaded firmware in dict of available
    firmware_keys   - names of all the available firmware
    fw_details      - result from mgr.get_firmware_summary()
    fw_states       - same as mgr.firmware_states
    gain            - dict of RF section gains
    IF_input_labels - same as mgr.IFsw[0].multipoles
    IF_on           - dict of RF section states
    IFsw_state      - dict of switch states
    logic           - KurtosisClient instance
    mgr             - remote Manager() instance
    power_on        -
    register        - dict of dicts of register data
    roach_IPs       - dict of ROACH IP addresses
    roach_keys      - number IDs of the remote Roach() instances
    roach_status    - dict of ROACH status
    signal_sources  - result from mgr.report_signal_sources()
    sw_keys         - same as mgr.IFsw.keys()
    switch_states   - list of inputs for each switch output
    synth_data      - parameters for the synthesizers
    synth_freq      - dict in form for use by UI
    synth_pwr       - dict in form for use by UI
    temps           - ADC temperatures   
  """
  def __init__(self):
    mylogger = logging.getLogger(module_logger.name+".ActionConfiguration")
    mylogger.debug(" initializing %s", self)
    ManagerClient.__init__(self)
    self.logger = mylogger
    self.signal = MySignaller()
    self.logger.debug("Created signal attribute %s",self.signal)
    self.signal.signalChanged.connect(self.refresh_RF_labels)
    self.signal.gainChanged.connect(self.update_gain_labels)
    self.initUIs()

  def initUIs(self):
    self.logger.debug("Firmware is %s", self.firmware)
    if (self.firmware['roach1'] and self.firmware['roach1'] != "Unknown") or \
       (self.firmware['roach2'] and self.firmware['roach2'] != "Unknown"):
      #  I'm assuming for expedience that the firmware state of both ROACH
      # boards is the same
      self.initUIs_w_fw()
    else:
      self.initUIs_wo_fw()

  def make_value_dicts(self):
    """
    """
    self.roach_names = {}
    self.fan_labels = {}
    self.MMS_opt_lbl = {}
    self.ADC_keys = {}
    self.ADC_labels = {}
    self.RF_keys = {}
    self.RF_labels = {}
    self.optimize_lbl = {}
    self.analog_labels = {}
    for roach in self.roach_keys:
      self.roach_names[roach] = roach
      self.fan_labels[roach] = {}
      for fan in self.fan_rpm[roach].keys():
        self.fan_labels[roach][fan] = "Fan "+str(fan+1)
      self.MMS_opt_lbl[roach] = {0: "EEPROM boot",
                                 1: "Selfprotect",
                                 2: "Auto Pwr Up"}
      self.analog_labels[roach] = {0: "Min",
                                   1: "Actual",
                                   2: "Max"}

      if self.firmware_dict[roach] > -1:
        self.ADC_keys[roach] = self.fw_details[roach]['ADC inputs'].keys()
        #self.fw_details[self.roach_names[roach]]['ADC inputs'].keys()
        self.ADC_keys[roach].sort()
        self.ADC_labels[roach] = {}
        self.RF_keys[roach] = {}
        self.RF_labels[roach] = {}
        self.optimize_lbl[roach] = {}
        for ADC in self.ADC_keys[roach]:
          self.ADC_labels[roach][ADC] = "ADC "+str(ADC)
          self.RF_labels[roach][ADC] = {}
          self.RF_keys[roach][ADC] = self.fw_details[roach]['ADC inputs'][ADC]
          # self.fw_details[self.roach_names[roach]]['ADC inputs'][ADC]
          self.RF_keys[roach][ADC].sort()
          self.optimize_lbl[roach][ADC] = {}
          for RF in self.RF_keys[roach][ADC]:
            self.RF_labels[roach][ADC][RF] = "RF "+str(RF)
            self.optimize_lbl[roach][ADC][RF] = "Go!"
        self.logger.debug("make_value_dicts: RF keys: %s",
                          self.RF_keys)
      else:
        self.ADC_labels[roach] = {}
        self.RF_keys[roach] = {}
        self.RF_labels[roach] = {}
        self.optimize_lbl[roach] = {}
    self.logger.debug("make_value_dicts: ROACH names: %s",self.roach_names)
    self.logger.debug("make_value_dicts: ADC labels: %s", self.ADC_labels)
    self.logger.debug("make_value_dicts: RF  labels: %s", self.RF_labels)
    self.logger.debug("make_value_dicts: Optimize labels: %s",
                      self.optimize_lbl)
    self.logger.debug("make_value_dicts: Fan labels: %s", self.fan_labels)
    
  def initUIs_w_fw(self):
    """
    This initializes the UI when the firmware is recognized.

    This permits monitor and control of the KATADC RF sections.
    """
    #self.update_data()
    self.make_value_dicts()
    self.rows = {}
    # ---------------------------- Overview Tab ----------------------------
    self.rows['Overview'] = [
        {'widget': 'label',
         'name': 'Board',
         'values': self.roach_names},
        {'widget': 'label',
         'name': 'Accessible',
         'values': self.roach_status},
        {'widget': 'switch',
         'name': 'Firmware',
         'values': self.firmware_index,
         'labels': self.firmware_keys,
         'label_template': ''},
        {'widget': 'label',
         'name': 'ADC',
         'values': self.ADC_labels},
        {'widget': 'label',
         'name': 'Ambient Temp. (C)',
         'values': self.amb_temps,
         'format': "%5.2f"},
        {'widget': 'label',
         'name': 'ADCchip Temp.',
         'values': self.chip_temps,
         'format': "%5.2f"},
        {'widget': 'label',
         'name': 'RF',
         'values': self.RF_labels},
        {'widget': 'check',
         'name': 'Enabled',
         'values': self.IF_on,
         'action': self.update_RF_state},
        {'widget': 'label',
         'name': 'Gain (dB)',
         'values': self.gain,
         'format': "%5.1f",
         'slots': [[self.signal.gainChanged, self.update_gain_labels],
                   [self.signal.signalChanged, self.refresh_RF_labels]]},
        {'widget': 'label',
         'name': 'RF level (dBm)',
         'values': self.ADC_levels,
          'format': "%5.2f",
          'slots': [[self.signal.signalChanged, self.refresh_RF_labels]]},
      ]
    # ---------------------------- Signals Tab -----------------------------
    self.rows['Signals'] = [
        {'widget': 'label',
         'name': 'Board',
         'values': self.roach_names},
        {'widget': 'label',
         'name': 'IP address',
         'values':self.roach_IPs},
        {'widget': 'label',
         'name': 'Bit File',
         'values': self.boffiles,
         'slots': [[self.signal.fwChanged, self.update_firmware_label]]},
        {'widget': 'label',
         'name': 'ADC',
         'values': self.ADC_labels},
        {'widget': 'label',
         'name': 'RF',
         'values': self.RF_labels},
        {'widget': 'switch',
         'name': 'IF',
         'values': self.ADC_source,
         'labels': self.IF_input_labels},
        {'widget': 'dial',
         'name': 'Set Gain',
         'values': self.gain,
         'action': self.update_gain,
         'range': [-11.5, 20],
         'format': "%6.1f",
         'converters': [self.gainToInt, self.intToGain]},
        {'widget': 'label',
         'name': 'Gain (dB)',
         'values': self.gain,
         'format': "%5.1f",
         'slots': [[self.signal.gainChanged, self.update_gain_labels],
                   [self.signal.signalChanged, self.refresh_RF_labels]]},
        {'widget': 'label',
         'name': 'RF level (dBm)',
         'values': self.ADC_levels,
          'format': "%5.2f",
          'slots': [[self.signal.signalChanged, self.refresh_RF_labels]]},
        {'widget': 'push',
         'name': 'Optimize Gain',
         'values': self.optimize_lbl,
         'action': self.optimize_RF},
        {'widget': 'spinslider',
         'name': 'Sample Clock (MHz)',
         'values': self.synth_freq,
         'range': [200,1500],
         'action': self.set_clock},
        {'widget': 'spinbox',
         'name': 'Clock power (dBm)',
         'values': self.synth_pwr,
         'range': [-4,5,3],
          'action': self.set_clock}
      ]
    # ---------------------------- Board Tab -------------------------------
    self.rows['Board'] = [
        {'widget': 'label',
         'name': 'Board',
         'values': self.roach_names},
        {'widget': 'check',
         'name': 'Power',
         'values': self.power_on,
         'action': self.update_power_state},
        {'widget': 'label',
         'name': 'Fan',
         'values': self.fan_labels},
        {'widget': 'label',
         'name': 'RPM',
         'values': self.fan_rpm},
        {'widget': 'label',
         'name': 'MMS Opt.',
         'values': self.MMS_opt_lbl},
        {'widget': 'check',
         'name': 'Opt enabled',
         'values': self.MMS_opt,
         'action': self.update_MMS_opt},
        {'widget': 'label',
         'name': 'Analog vals',
         'values': self.analog_labels},
      ]
    self.rows['Board'] = self._append_rows(self.rows['Board'],
                                           'label',
                                           self.temps)
    self.rows['Board'] = self._append_rows(self.rows['Board'],
                                           'label',
                                           self.volts,
                                           format="%5.2f")
    # -------------------------- Firmware Tab ------------------------------
    self.rows['Firmware'] = [
        {'widget': 'label',
         'name': 'Board',
         'values': self.roach_names},
        {'widget': 'custom',
         'name': 'Firmware',
         'values': self.firmware_index,
         'widgets': firmware_widgets}
      ]
    
  def _append_rows(self,row_dict, row_type, values, format="%6.1f"):
    for key in values.keys():
      row_dict.append({'widget': row_type,
                       'name':   key,
                       'values': values[key],
                       'format': format})
    return row_dict
    
  def initUIs_wo_fw(self):
    """
    This initializes the UI when the firmware is not recognized.
    """
    self.update_roach_data()
    self.make_value_dicts()
    self.rows = {}
    # ------------------------ Overview Tab -----------------------------
    self.rows['Overview'] = [
        {'widget': 'label',
         'name': 'Board',
         'values': self.roach_names},
        {'widget': 'label',
         'name': 'Accessible',
         'values': self.roach_status},
        {'widget': 'switch',
         'name': 'Firmware',
         'values': self.firmware_index,
         'labels': self.firmware_keys,
         'label_template': ''}]
    self.rows['Signals'] = [
        {'widget': 'label',
         'name': 'Board',
         'values': self.roach_names},
        {'widget': 'label',
         'name': 'IP address',
         'values':self.roach_IPs},
        {'widget': 'label',
         'name': 'Bit File',
         'values': self.boffiles,
         'slots': [[self.signal.fwChanged, self.update_firmware_label]]}]
    # ---------------------------- Board Tab -------------------------------
    self.rows['Board'] = [
        {'widget': 'label',
         'name': 'Board',
         'values': self.roach_names},
        {'widget': 'check',
         'name': 'Power',
         'values': self.power_on,
         'action': self.update_power_state},
        {'widget': 'label',
         'name': 'Fan',
         'values': self.fan_labels},
        {'widget': 'label',
         'name': 'RPM',
         'values': self.fan_rpm},
        {'widget': 'label',
         'name': 'MMS Opt.',
         'values': self.MMS_opt_lbl},
        {'widget': 'check',
         'name': 'Enabled',
         'values': self.MMS_opt,
         'action': self.update_MMS_opt},
      ]
    self.rows['Board'] = self._append_rows(self.rows['Board'],
                                           'label',
                                           self.temps)
    self.rows['Board'] = self._append_rows(self.rows['Board'],
                                           'label',
                                           self.volts)
    # -------------------------- Firmware Tab ------------------------------
    self.rows['Firmware'] = [
        {'widget': 'label',
         'name': 'Board',
         'values': self.roach_names}]

  def update_RF_state(self, frame, rowname, roach, ADC, RF, state):
    """
    Action for the "RF on" buttons: turns RF section off or on

    @param rowname : row invoking this method
    @type  rowname : str
    
    @param roach : roach index of column
    @type  roach : int
    
    @param ADC : ADC index of the column
    @type  ADC : int
    
    @param RF : RF input index of column
    @type  RF : int
    
    @param state   : new state for RF section
    """
    self.logger.debug(
                     "update_RF_state: ROACH %d ADC %d RF %d state will be %s",
                     roach, ADC, RF,
          frame.checkbuttons[rowname][(roach,ADC,RF)].isChecked())
    self.set_RF(roach, adc=ADC, inp=RF, enabled=state)
    self.refresh_gain()              # updates self.gain
    r_index = self.roach_keys.index(roach)
    column = (r_index,ADC,RF)
    self.logger.debug("update_RF_state: emitting signalChanged for %s, %s, %s",
                      rowname, column, self.ADC_levels[r_index][ADC][RF])
    self.signal.signalChanged.emit(frame,rowname,column,
                                   self.ADC_levels[r_index][ADC][RF])

  def update_power_state(self,*args):
    self.logger.debug("update_power_state: entered with %s", args)
    self.logger.warning("update_power_state: not yet implemented")

  def update_RF_labels(self):
    """
    """
    levels = flattenDict(self.ADC_levels)
    for key in levels.keys():
      #roach = key[0]
      #adc = key[1]
      #rf = key[2]
      #self.ADC_levels[key[0]][key[1]][key[2]] = levels[key]
      #self.ADC_levels[roach][adc][rf] = levels[key]
      self.frames['Overview'].labels["RF level (dBm)"][key].setText(
        ("%5.2f" % levels[key]) )
      self.frames['Signals'].labels["RF level (dBm)"][key].setText(
        ("%5.2f" % levels[key]) )
      self.logger.debug(
             "refresh_RF_labels: Changed row 'RF level' column %s value to %s",
             key,levels[key])
  
  def refresh_RF_labels(self,*args):
    """
    Slot for the signal 'signalChanged'

    This updates the RF levels in all columns.
    'signalChanged' is emitted when the RF section state or gain is changed.

    The 'signalChanged' arguments are intended for obsolete method
    'update_RF_label' and ignored.
    """
    self.logger.debug('refresh_RF_labels: called with %s', args)
    if args:
      frame = args[0] # frame which generated the signal
      calling_tab = args[1]
      roach,adc,rf = args[2]
      value = args[3]

    self.refresh_ADC_levels()
    self.update_RF_labels()
    for roach in self.roach_keys:  # self.roach_names.keys()
      self.update_spectra(roach)
    
  def update_RF_label(self,*args):
    """
    Obsolete slot for the signal 'signalChanged'

    'signalChanged' is emitted when the RF section state or gain is changed.
    This changes only the RF value in the column which was changed.
    """
    self.logger.debug("update_RF_label: called with args %s", args)
    row = args[0]
    key = args[1]
    value = args[2]
    self.logger.debug('update_RF_label: key = %s, value = %f', key, value)
    self.ADC_levels[key[0]][key[1]][key[2]] = value
    self.central_frame.labels["RF level"][key].setText(("%5.2f" % value))
    self.logger.debug(
              "update_RF_label: Changed row 'RF level' column %s value to %s",
              key,value)

  def update_gain(self,*args):
    """
    Action for when the gain dial changes
    """
    self.logger.debug("update_gain: called with args %s", args)
    self.logger.debug("update_gain: widget value = %d", args[-1])
    realValue = self.intToGain(args[-1])
    frame = args[0]
    row = args[1]
    column = args[2:-1]
    roach,ADC,RF = column
    self.set_RF(roach, adc=ADC, inp=RF, gain=realValue)
    self.logger.debug("update_gain: Changed row '%s' column %s gain to %f",
                      row, str(column),realValue)
    self.logger.debug("update_gain: emitting gainChanged for %s, %s, %s",
                                                      row,column,realValue)
    try:
      self.signal.gainChanged.emit(frame,row,column,realValue)
    except AttributeError, details:
      print details
      self.close()
    self.refresh_ADC_levels()
    self.logger.debug("update_gain: ADC levels: %s",self.ADC_levels)
    self.logger.debug("update_gain: emitting signalChanged for %s, %s, %s",
                      row,column,self.ADC_levels[roach][ADC][RF])
    self.signal.signalChanged.emit(frame,row,column,
                                   self.ADC_levels[roach][ADC][RF])

  def update_gain_labels(self,*args):
    """
    """
    self.logger.debug('update_gain_labels: args = %s', args)
    frame,row,column,value = args
    self.logger.debug('update_gain_labels: key = %s', column)
    self.logger.debug('update_gain_labels: old gains: %s', self.gain)
    self.gain[column[0]][column[1]][column[2]] = value
    self.logger.debug('update_gain_labels: new gains: %s', self.gain)
    self.frames['Overview'].labels['Gain (dB)'][column].setText(str(value))
    self.frames['Signals'].labels['Gain (dB)'][column].setText(str(value))
      
  def gainToInt(self,gain):
    """
    Convert gain to integer 0.5 dB steps

    This needs to be generalized
    """
    dial_num = int(gain*2)
    self.logger.debug("%f converted to %d", gain, dial_num)
    return dial_num # int((gain*2)+23)

  def intToGain(self,num):
    """
    Convert 0.5 dB step value to gain

    This needs to be generalized
    """
    value = float(num/2)
    self.logger.debug("%d converted to %f",num,value)
    return value # float(num-23)/2

  def switch_changed(self, switch, rowname, column_ID):
    """
    Action to take when the IF_selector signals a new state.

    The IF selector only reports the chosen state.  The non-GUI ManagerClient
    instance actually sends the switch change request to the remote Manager()
    instance.  Then the displayed values are updated.

    @param switch :
    @type  switch :

    @param rowname :
    @type  rowname :

    @param column_ID :
    @type  column_ID :
    """
    self.logger.debug("switch_changed: call for switch %s, row %s, column %s",
                      switch, rowname, column_ID)
    if rowname == 'IF':
      index = 2*column_ID[0] + column_ID[2]
      new_state = switch.state
      self.logger.debug("switch_changed: IF switch %s state changed to %s",
                        index, new_state)
      self.set_IF_switch(index, new_state)
      self.refresh_ADC_levels()
      self.logger.debug("switch_changed: ADC levels: %s",self.ADC_levels)
      [R,ADC,RF] = column_ID
      self.logger.debug("switch_changed: signal signalChanged emitting")
      self.signal.signalChanged.emit(switch.parent, rowname, column_ID,
                                     self.ADC_levels[R][ADC][RF])
      
    elif rowname == 'Firmware':
      index = column_ID[0]
      new_firmware_key = switch.state
      self.logger.debug("switch_changed: Firmware index %s is changed to %s",
                     index, new_firmware_key)
      self.firmware[index] = self.firmware_keys[new_firmware_key]
      self.boffiles[index] = self.load_firmware(index,self.firmware[index])
      self.update_data()
      self.make_value_dicts()
      self.signal.fwChanged.emit(switch.parent,'Bit File', column_ID,
                                 self.boffiles[index])
      self.logger.debug("switched_changed: signal fwChanged was emitted")
      self.rebuildUI()
      
  def update_firmware_label(self,*args):
    """
    slot for fwChanged
    """
    self.logger.debug('update_firmware_label: args = %s', args)
    frame, row, column, bitfile = args
    self.logger.debug('update_firmware_label: new text: %s',bitfile)
    frame.labels[str(row)][column].setText(str(bitfile))

  def optimize_RF(self,*args):
    """
    """
    self.logger.debug("optimize_RF: entered with %s", args)
    self.logger.warning("optimize_RF: not yet implemented")

  def set_clock(self,*args):
    """
    """
    self.logger.debug("set_clock: arguments = %s", args)
    widget, rowname, row, column, state = args
    self.logger.warning("set_clock: not yet implemented")

  def update_MMS_opt(self, *args):
    """
    """
    self.logger.debug("update_MMS_opt: entered with %s", args)
    self.logger.warning("update_MMS_state: not yet implemented")

  def update_spectra(self,roach):
    """
    """
    roachname = roach # self.roach_names[roach]
    self.logger.debug("update_spectra: entered for roach %s", roach)
    for ADC in self.ADC_keys[roach]:
      for RF in self.RF_keys[roach][ADC]:
        # get the data
        r_index = self.roach_keys.index(roach)
        samples = self.get_ADC_samples(roach,ADC,RF)
        accums = self.get_accums(r_index, ADC, RF)
        if accums and type(samples) == numpy.ndarray:
          spectrum = accums[2]
          self.logger.debug("update_spectra: spectrum: %s", spectrum)
          if accums.has_key(4):
            kurtosis = accums[4]
            self.logger.debug("update_spectra: kurtosis: %s", kurtosis)
          # generate the plots
          try:
            ADC_frame = self.tabbedPlotWindows[roachname].frames['ADC']
          except KeyError:
            self.logger.warning(
                          "update_spectra: there is no ADC plot window for %s",
                          roachname)
          else:
            ADC_frame.axes[RF].cla()
            ADC_frame.axes[RF].hist(samples, bins=21)
            ADC_frame.axes[RF].grid()
            if ADC_frame.titles:
              ADC_frame.axes[RF].set_title(ADC_frame.titles[RF])
            ADC_frame.canvas.draw()
          try:
            overview_frame = \
                           self.tabbedPlotWindows[roachname].frames['Overview']
          except KeyError:
            self.logger.warning("update_spectra: there is no overview for %s",
                                roachname)
            overview_frame_exists = False
          else:
            overview_frame_exists = True
            overview_frame.axes[RF+2].cla()
            overview_frame.axes[RF+2].hist(samples, bins=21)
            overview_frame.axes[RF+2].grid()
            if RF == 0:
              overview_frame.axes[0].cla()
              overview_frame.axes[0].grid()
              overview_frame.axes[1].cla()
              overview_frame.axes[1].grid()
          # power and kurtosis spectra
          try:
            pwr_frame = self.tabbedPlotWindows[roachname].frames['Power']
          except KeyError:
            self.logger.warning(
                               "update_spectra: there is no power plot for %s",
                               roachname)
          else:
            pwr_frame.axes[RF].cla()
            if self.power_scale == "Linear":
              pwr_frame.axes[RF].plot(spectrum[1:])
            else:
              pwr_frame.axes[RF].semilogy(spectrum[1:])
            pwr_frame.axes[RF].grid()
            if pwr_frame.titles:
              pwr_frame.axes[RF].set_title(pwr_frame.titles[RF])
            pwr_frame.canvas.draw()
            if overview_frame_exists:
              if self.power_scale == "linear":
                overview_frame.axes[0].plot(spectrum[1:],
                                            label=pwr_frame.titles[RF])
              else:
                overview_frame.axes[0].semilogy(spectrum[1:],
                                            label=pwr_frame.titles[RF])
        
          if accums.has_key(4):
            try:
              kurt_frame = self.tabbedPlotWindows[roachname].frames['Kurtosis']
            except KeyError:
              self.logger.warning(
                            "update_spectra: there is no kurtosis plot for %s",
                            roachname)
            else:
              kurt_frame.axes[RF].cla()
              kurt_frame.axes[RF].plot(kurtosis[1:])
              kurt_frame.axes[RF].grid()
              if kurt_frame.titles:
                kurt_frame.axes[RF].set_title(kurt_frame.titles[RF])
              kurt_frame.canvas.draw()
            try:
              overview_frame.axes[1].plot(kurtosis[1:],
                                        label=kurt_frame.titles[RF])
            except UnboundLocalError:
              pass
            else:
              if overview_frame.titles:
                for axID in overview_frame.axes.keys():
                  overview_frame.axes[axID].set_title(
                                                   overview_frame.titles[axID])
              overview_frame.axes[0].legend()
              overview_frame.axes[1].legend()
              overview_frame.canvas.draw()
        else:
          self.logger.error("update_spectra: no response from server")
          
class myTabbedPlotWindow(TabbedWindow):
  def __init__(self, frames, roach, parent=None):
    super(myTabbedPlotWindow,self).__init__(frames)
    self.name = roach
    self.parent =parent
    self.logger = logging.getLogger(__name__+".myTabbedPlotWindow")
    
  def closeEvent(self,*args):
    self.logger.debug("closeEvent: called with %s", args)
    if self.parent.tabbedPlotWindows.has_key(self.name):
      try:
        self.parent.tabbedPlotWindows.pop(self.name)
        
      except Exception, details:
        self.logger.error("closeEvent: failed: %s", details)
    else:
      self.logger.warning("closeEvent: tabbedPlotWindows has no key %s",
                          self.name)

class MPLsubplots(MPLplotter):
  """
  Regular subplot array on a matplotlib canvas
  """
  def __init__(self,rows=1,columns=1,titles=[],fill=False):
    """
    Initialize MPLsubplots

    @param rows : number of rows of plots
    @type  rows : int

    @param columns : number of columns of plots
    @type  columns : int

    @param fill : if True put random data in the plt
    @type  fill : bool
    """
    super(MPLsubplots,self).__init__()
    self.logger = logging.getLogger(__name__+".MPLsubplots")
    self.titles = titles
    num_subplots = rows*columns
    self.axes = {}
    if fill:
      x = range(100)
      y = [random() for i in range(100)]
    for i in range(num_subplots):
      self.logger.debug("__init__: making subplot %d",i)
      self.axes[i] = self.fig.add_subplot(rows,columns,i+1)
      if fill:
        self.lines = self.axes[i].plot(x,y)
      self.logger.debug("__init__: axes: %s",str(self.axes))
    self.canvas.show()

class MPLmanyaxes(MPLplotter):
  """
  Arbitrary axes on a matplotlib canvas
  """
  def __init__(self,bounds=[[0.1,0.1,0.9,0.9]],
                    titles=[],
                    fill=False):
    """
    Initialize MPLmanyaxes

    @param bounds : [[llx,lly,urx,ury], [...]]
    @type  bounds : list of lists of floats 

    @param fill : if True put sine waves in the plt
    @type  fill : bool
    """
    super(MPLmanyaxes,self).__init__()
    self.logger = logging.getLogger(__name__+".MPLmanyaxes")
    num_subplots = len(bounds)
    self.titles = titles
    self.axes = {}
    if fill:
      x = np.arange(0, 10, 0.2)
      y = np.sin(x)
    for i in range(num_subplots):
      self.logger.debug("__init__: making subplot %d",i)
      coords = bounds[i]
      box = [coords[0], coords[1], coords[2]-coords[0], coords[3]-coords[1]]
      self.axes[i] = self.fig.add_axes(box)
      if fill:
        self.lines = self.axes[i].plot(x,y)
      self.logger.debug("__init__: axes: %s",str(self.axes))
    self.canvas.show()

class MainWindow(QtGui.QMainWindow, ActionConfiguration):
  """
  Main window for testing ControlPanelGriddedFrame
  """
  def __init__(self, parent=None):
    """
    Create an instance main GUI

    This is a minimal class because the appearance and actions of the actual
    GUI are defined by the ActionConfiguration class instance

    @param parent : needed by QMainWindow but typically None
    @type  parent : QWidget() instance
    """
    mylogger = logging.getLogger(module_logger.name+".MainWindow")
    mylogger.debug(" initializing")
    QtGui.QMainWindow.__init__(self, parent)
    ActionConfiguration.__init__(self)
    self.logger = mylogger
    self.logger.debug(" superclasses initialized")
    self.create_menubar()
    self.create_central_frame()
    self.create_status_bar()
    self.power_scale = 'Linear'
    self.tabbedPlotWindows = {}
    self.timer = QtCore.QTimer()

  def create_central_frame(self):
    self.frames = {
      "Overview": ControlPanelGriddedFrame(self.rows['Overview'],
                                           parent=self),
      "Signals":  ControlPanelGriddedFrame(self.rows['Signals'],
                                           parent=self),
      "Board":    ControlPanelGriddedFrame(self.rows['Board'],
                                           parent=self),
      "Firmware": ControlPanelGriddedFrame(self.rows['Firmware'],
                                           parent=self)}
    self.central_frame = TabbedWindow(self.frames,
                                     ["Overview","Signals","Board","Firmware"])
    self.setCentralWidget(self)

  def rebuildUI(self):
    self.central_frame.close()
    self.initUIs() # to redefine self.rows
    self.create_central_frame()

  def create_menubar(self):
    """
    Create the menu bar for the main window

    In this example, the menubar is not itself instantiated but its components
    -- the file menu, the configuration menu and the help menu are.

    The file and help menus use only action buttons.  The configuration menu
    has a submenu as one of its buttons.  The buttons of the submenu are
    associated with actions.
    """
    # The file menu
    self.file_menu = self.menuBar().addMenu("&File")
    quit_action = create_action(self,"&Quit", slot=self.quit,
            shortcut="Ctrl+Q", tip="Close the application")
    add_actions(self.file_menu, (None, quit_action))

    # The configuration menu
    self.config_menu = self.menuBar().addMenu("&Config")
    create_option_menu(self,
                       self.config_menu,
                       "&Logging level",
                       self.set_loglevel,
                       ['Debug','Info','Warning','Error','Critical'])
    
    create_option_menu(self,
                       self.config_menu,
                       "&Plot window",
                       self.make_plot_window,
                       self.roach_keys+['all'])
    create_option_menu(self,
                       self.config_menu,
                       "Power &Scale",
                       self.set_power_scale,
                       ["Linear","Logarithmic"])
    create_option_menu(self,
                       self.config_menu,
                       "&Refresh timer",
                       self.timer_action,
                       ["Start", "Stop"])
    # The help menu
    self.help_menu = self.menuBar().addMenu("&Help")
    about_action = create_action(self,"&About",
            shortcut='F1', slot=self.on_about,
            tip='About the demo')
    add_actions(self.help_menu, (about_action,))

  def on_about(self):
    """
    Action for Help menu button
    """
    msg = """DTO Manager Client GUI"""
    QtGui.QMessageBox.about(self, "About the demo", msg.strip())

  def quit(self):
    """
    Action for Quit menu button
    """
    self.logger.info("Quitting.")
    self.timer_run = False
    for roach in self.tabbedPlotWindows.keys():
      self.logger.debug("Closing plot window for %s", roach)
      self.tabbedPlotWindows[roach].close()
    self.close()

  def create_status_bar(self):
    """
    Status bar placeholder
    """
    self.status_text = QtGui.QLabel("Welcome to the DTO Manager Client")
    self.statusBar().addWidget(self.status_text, 1)

  def set_loglevel(self, option):
    """
    Change the logging level
    """
    level = option.text()
    if level == 'Debug':
      self.logger.setLevel(logging.DEBUG)
    elif level == 'Info':
      self.logger.setLevel(logging.INFO)
    elif level == 'Warning':
      self.logger.setLevel(logging.WARNING)
    elif level == 'Error':
      self.logger.setLevel(logging.ERROR)
    elif level == 'Critical':
      self.logger.setLevel(logging.CRITICAL)
    self.logger.warning("Logging level set to %s", level)

  def make_plot_window(self, roach):
    """
    """
    self.logger.debug("make_plot_window: entered with %s", roach)
    if str(roach.text()) == 'all':
      names = self.roach_keys # self.roach_names.values()
    else:
      names = [str(roach.text())]
    self.logger.debug("make_plot_window: processing %s", names)
    for roachname in names:
      roachnum = int(str(roachname[-1:]))-1
      self.logger.debug("make_plot_window: entered for %s", roachname)
      self.tabbedPlotWindows[roachname] = {}
      if self.firmware[roachname][:9] == 'kurt_spec':
        overview_axes = [[0.1, 0.1, 0.9, 0.3],
                         [0.1, 0.4, 0.9, 0.6],
                         [0.1, 0.7, 0.45, 0.9],
                         [0.55 ,0.7, 0.9, 0.9]]
        frames = {"Overview": MPLmanyaxes(overview_axes,
                                          titles=["Power","Kurtosis",
                                                  "RF 0","RF 1"]),
                  "ADC": MPLsubplots(columns=2,  titles=["RF 0","RF 1"]),
                  "Power": MPLsubplots(rows=2,   titles=["RF 0","RF 1"]),
                  "Kurtosis": MPLsubplots(rows=2,titles=["RF 0","RF 1"])}
        self.tabbedPlotWindows[roachname] = myTabbedPlotWindow(frames,
                                                               roachname,
                                                               parent = self)
        self.tabbedPlotWindows[roachname].setWindowTitle(roachname)
        self.update_spectra(roachname)
        self.tabbedPlotWindows[roachname].show()
      else:
        self.logger.warning("make_plot_window: not yet implemented.")
      self.logger.debug("make_plot_window: plot tabs: %s",
                        self.tabbedPlotWindows)

  def set_power_scale(self, *args):
    self.logger.debug("set_power_scale: called with %s", args)
    self.logger.debug("set_power_scale: selection = %s", args[0].text() )
    self.power_scale = args[0].text()
    self.logger.debug("set_power_scale: checked? %s", args[0].isChecked() )
    for roach in self.tabbedPlotWindows.keys():
      self.update_spectra[roach]
   
  def timer_action(self, *args):
    self.logger.debug("timer_action: called with %s", args)
    action = args[0].text()
    if action == "Start":
      self.logger.debug("timer_action: %s", action)
      self.timer_loop = 1
      self.timer.singleShot(1000, self.timer_update)
    elif action == "Stop":
      self.logger.debug("timer_action: %s", action)
      self.timer_loop = 0
    else:
      self.logger.debug("timer_action: unknown action %s", action)

  def timer_update(self):
    if self.timer_loop:
      if self.timer_loop  == 1:
        self.refresh_RF_labels()
      if self.timer_loop % 2 == 0:
        for key in self.frames["Firmware"].custom["Firmware"].keys():
          self.frames["Firmware"].custom["Firmware"][key].refresh_UI()
      self.timer_loop += 1
      self.timer.singleShot(1000, self.timer_update)
    else:
      print "Timer stopped"

from optparse import OptionParser
p = OptionParser()
p.set_usage('managerClientUI.py [options]')
p.set_description(__doc__)

p.add_option('-l', '--log_level',
             dest = 'loglevel',
             type = 'str',
             default = 'warning',
             help = 'Logging level for main program and modules')
opts, args = p.parse_args(sys.argv[1:])

mylogger = logging.getLogger()
init_logging(mylogger,
             loglevel = logging.INFO,
             consolevel = logging.DEBUG,
             logname = logpath+"client.log")

set_loglevel(mylogger, get_loglevel(opts.loglevel))

from support.tunneling import module_logger as Tlogger
Tlogger.setLevel(logging.WARNING)

app = QtGui.QApplication(sys.argv)
app.setStyle("motif")
mylogger.debug(" creating MainWindow")
client = MainWindow()
mylogger.warning("""If the program raises an exception, do
  cleanup_tunnels()
before exiting python.""")

client.show()
sys.exit(app.exec_())
