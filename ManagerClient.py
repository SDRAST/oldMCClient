# -*- coding: utf-8 -*-
"""
Client class for DTO manager server.
"""
import Pyro5
import Pyro5.api
import Pyro5.errors
import logging
import time
import sys

from MCClient.kurtosis_client import KurtosisClient

module_logger = logging.getLogger(__name__)

class ManagerClient(object):
  """
  Pyro client to communicate with Supervisor server

  Public attributes::
    ADC_levels      - dict of ADC levels
    adc_snap_trigger- dict of kurt_spec snap trigger selections
    ADC_source      - number of IF switch output for this ADC
    amb_temps       - temps[roach][adc]['ambient']
    available       - dict of lists of available boffiles
    boffiles        - dict of running boffiles
    chip_temps      - temps[roach][adc]['IC']
    firmware        - dict of firmware names indexed by roach name
    firmware_dict   - index of loaded boffile in list of available
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
    register_details- information about registers
    register_values - contents of the registers
    roach_IPs       - dict of ROACH IP addresses
    roach_keys      - sorted list of remote Roach() namess
    roach_status    - dict of ROACH status
    signal_sources  - result from mgr.report_signal_sources()
    sw_keys         - same as mgr.IFsw.channel.keys()
    switch_states   - list of inputs for each switch output
    synth_data      - parameters for the synthesizers
    synth_freq      - dict in form for use by UI
    synth_pwr       - dict in form for use by UI
    temps           - ADC temperatures

  The source code for this class is organized in the following way::
    * Methods for the IF switches
    * Methods for the synthesizers
    * Methods for the ROACH boards
    * Methods for managing firmware
    * Methods requiring firmware
  """
  def __init__(self):
    """
    Instantiate a client
    """
    #server = 'DTO_mgr-dto'
    self.logger = logging.getLogger(__name__+".ManagerClient")
    self.logger.debug("__init__: logger is %s",self.logger.name)
    #self.mgr = PyroTaskClient(server)
    uri = Pyro5.api.URI("PYRO:DSS-43@localhost:50015")
    self.hardware = Pyro5.api.Proxy(uri)
    try:
      self.hardware.__get_state__()
    except Pyro5.errors.CommunicationError as details:
      self.logger.error("__init__: %s", details)
      raise Pyro5.errors.CommunicationError("is the front end server running?")
    except AttributeError:
      # no __get_state__ because we have a connection
      self.hardware._pyroClaimOwnership()
    else:
      # use the simulator
      self.hardware = hardware # that is, False
    # get data from supervisor
    self.register_details = {} # for self.get_register_details(roach)
    self.register_values = {}
    self.update_data()
    

  def update_data(self):
    """
    """
    # 1) data for the switch
    #self.get_IFsw_states()      # updates IFsw_state
    #self.update_switch_data()   # switch labels and sources

    # 2) data for each roach
    self.update_roach_data()    # updates 
    self.get_temperatures()     # temperatures
    self.get_firmware_details() # sets firmware, fw_details, fw_states
    self.refresh_gain(index=-1) # refresh gain, IF_on for [roach][ADC]{RF]
    
    # 3) data for synthesizers
    self.refresh_synth_data()

    # 4) data for spectrometers
    self.refresh_ADC_levels()
    self.get_ADC_sources()

    # 5) data for the board monitor
    self.fan_rpm = self.mgr.check_fans()
    self.logger.debug("update_data: fan report: %s", self.fan_rpm)
    self.MMS_opt = self.mgr.get_MMS_options()
    self.logger.debug("update_data: MMS options: %s", self.MMS_opt)
    self.volts, self.temps = self.mgr.get_MMS_analog()
    for key in list(self.volts.keys()):
      self.logger.debug("update_data: %s: %s", key, self.volts[key])
    for key in list(self.temps.keys()):
      self.logger.debug("update_data: %s: %s", key, self.temps[key])

    # 6) register data from the firmware, without knowledge of firmware

    for roachname in self.roach_keys:
      roach_index = self.roach_keys.index(roachname)
      self.get_register_values(roachname)
      if roachname in self.firmware:
        if ((self.firmware[roachname] == 'kurt_spec') or
            (self.firmware[roachname] == 'kurt_spec_r1') or
            (self.firmware[roachname] == 'kurt_spec_gain')):
          self.logic = KurtosisClient(self, roach_index)
    
  # ------------------ methods for the IF switches -----------------------

  def get_IFsw_states(self):
    """
    Get the inputs for all switches

    This returns a list with the states (input numbers) of the IF switches.
    It also creates an attribute 'IFsw_state' which is a dictionary with
    integer keys  0, 1, 2, 3.  The values are integers corresponding to the
    list of possible inputs.
    
    get_switch_states() causes the server to set the attributes IFsw[].state
    each IFsw[].  It also creates an ordered list of the switch states and
    returns that.
    """
    self.switch_states = self.mgr.get_switch_states()
    self.logger.debug("get_IFsw_states: Server returned IF switch states: %s",
                        str(self.switch_states))
    self.sw_keys = self.mgr.request("self.IFsw.channel.keys()")
    self.sw_keys.sort()
    self.logger.debug("get_IFsw_states: Server returned IF switch keys: %s",
                      self.sw_keys)
    self.IFsw_state = {}
    for sw in self.sw_keys:
      index = self.sw_keys.index(sw)
      self.IFsw_state[index] = self.switch_states[index]
    self.logger.debug("get_IFsw_states: state dict: %s",self.IFsw_state)
    return self.switch_states
  
  def update_switch_data(self):
    """
    Update the data for the IF switch
    """
    self.IF_input_labels = self.mgr.request("self.IFsw.inputs.keys()")
    self.IF_input_labels.sort()
    self.logger.debug("update_switch_data: IF switch inputs: %s",
                      self.IF_input_labels)

    self.signal_sources = self.mgr.report_signal_sources()
    self.logger.debug("update_switch_data: Signal sources: %s",
                      self.signal_sources)

  def set_IF_switch(self, index, state):
    """
    Set an IF switch

    @param index : switch number (0 -- 3)
    @type  index : int

    @param state : input number (0 -- 23)
    @type  state : int
    """
    self.logger.debug("set_IF_switch: %s set to %s", index, state)
    self.IFsw_state[index] = self.mgr.set_IFsw_state(index,state)

  def get_ADC_sources(self):
    """
    Returns the switch state for the corresponding IF switch output
    """
    self.ADC_source = {}
    self.logger.debug("get_ADC_sources: IF switch states: %s",
                      self.IFsw_state)
    for roachname in self.roach_keys:
      r_index = self.roach_keys.index(roachname)
      self.ADC_source[r_index] = {}
      for ADC in list(self.gain[roachname].keys()):
        self.ADC_source[r_index][ADC] = {}
        for RF in list(self.gain[roachname][ADC].keys()):
          self.logger.debug(
            "get_ADC_sources: getting signal source for roach %s ADC %s RF %s",
            r_index,ADC,RF)
          response = self.mgr.request("self.spec["+str(r_index)+"]["
                                                  +str(ADC)+"]["
                                                  +str(RF)+"].sources")
          self.logger.debug("get_ADC_sources: Response is %s", response)
          # Take the name part, strip off outer quotes, get index
          IFsw_outport = int(self.sw_keys.index(eval(response[0].split()[1])))
          self.logger.debug("IF switch output port is %d, type %s",
                            IFsw_outport, type(IFsw_outport))
          self.ADC_source[r_index][ADC][RF] = self.IFsw_state[IFsw_outport]
    self.logger.debug("__init__: ADC_source: %s", self.ADC_source)

  def get_register_values(self, roachname):
    """
    """
    self.logger.debug("get_register_values: for %s", roachname)
    if roachname in self.firmware:
      # There is firmware for this roach
      self.register_values[roachname] = self.mgr.get_register_values(roachname)
      self.logger.debug("get_register_values: ROACH %s register values> %s",
                        roachname,
                        self.register_values[roachname])
    else:
      self.register_values[roachname] = {}
    return self.register_values[roachname]
      
  # --------------------- methods for the synthesizers -------------------

  def refresh_synth_data(self):
    """
    """
    self.mgr.request('self.get_sampler_clocks_status()')
    self.synth_data = {}
    self.synth_freq = {}
    self.synth_pwr = {}
    for roachname in self.roach_keys:
      synth = self.roach_keys.index(roachname)+1
      self.synth_data[synth] = self.mgr.request(
                              'self.roaches["'+roachname+'"].clock_synth.status')
      self.synth_freq[roachname] = self.synth_data[synth]["frequency"]
      self.synth_pwr[roachname] = self.synth_data[synth]["rf_level"]
    self.logger.debug("refresh_synth_data: synthesizers: %s",self.synth_data)

  # --------------------- methods for the ROACH boards -------------------
  
  def update_roach_data(self):
    """
    Update the data for the ROACH boards

    Sets these attributes::
     available     - names of boffiles available to each ROACH
     boffiles      - name of currently loaded boffiles
     firmware_dict - index of loaded boffile in list of available
     roach_IPs     - dict of ROACH IP addresses
     roach_keys    - names of the remote Roach() instances
     roach_status  - dict of ROACH status
    """
    report = self.hardware.hdwr('Backend', "roach_report", [], {})
    self.roach_IPs = report['IP']
    self.roach_status = report['alive']
    self.boffiles     = report['bof']
    self.available    = report['avail']
    self.power_on     = report['power']
    self.logger.debug("update_roach_data: roach_IPs = %s",self.roach_IPs)
    self.logger.debug("update_roach_data: roach_status = %s",self.roach_status)
    self.logger.debug("update_roach_data: boffiles = %s",self.boffiles)
    self.logger.debug("update_roach_data: boffiles available:\n%s",
                      self.available)
    self.logger.debug("update_roach_data: power state = %s",self.power_on)
    
    self.firmware_dict = {}
    self.roach_keys = list(self.roach_status.keys())
    self.roach_keys.sort()
    for roachname in self.roach_keys:
      try:
        self.firmware_dict[roachname] = \
                    self.available[roachname].index(self.boffiles[roachname])
      except ValueError:
        self.firmware_dict[roachname] = -1
    self.logger.debug("update_roach_data: firmware_dict = %s",
                      self.firmware_dict)

  def refresh_gain(self,index=-1):
    """
    Get the current RF section gains

    @param index : logical spectrometer ID (-1 for all spectrometers)
    @type  index : int
    """
    if index == -1:
      keys = self.roach_keys
    else:
      keys = [index]
    response = {}
    self.IF_on = {}
    self.gain = {}
    for roachname in keys:
      if self.firmware[roachname]:
        self.logger.debug("refresh_gain: for ROACH %s", roachname)
        response[roachname] = self.mgr.request(
            "self.roaches['"+roachname+"'].get_gains()")
        self.logger.debug("refresh_gain: ROACH %s gain is %s",
                          roachname,response[roachname])
        self.gain[roachname] = {}
        self.IF_on[roachname] = {}
        for adc in list(response[roachname].keys()):
          self.gain[roachname][adc] = {}
          self.IF_on[roachname][adc] = {}
          for RF in response[roachname][adc]:
            self.gain[roachname][adc][RF] = response[roachname][adc][RF]['gain']
            self.IF_on[roachname][adc][RF] = response[roachname][adc][RF]['enabled']
      else:
        self.gain[roachname] = {}
        self.IF_on[roachname] = {}
    return response
    
  def refresh_ADC_levels(self):
    """
    Get the RF levels

    Returns a nested dict like this::
      {0: {0: {0: -2.7489310975880006, 1: -3.08088387439668}},
       1: {0: {0:  4.3043415708265451, 1: -3.03297909588116}}}
    """
    try:
      self.ADC_levels = self.mgr.get_ADC_levels()
    except RuntimeError:
      self.logger.error("refresh_ADC_levels: no response from server")
    else:
      self.logger.debug("refresh_ADC_levels: new levels: %s",
                       self.ADC_levels)

  def set_RF(self, roach, adc = 0, inp = 0, gain = None, enabled = True):
    """
    Configure an RF section

    If the gain is None, the current gain will be retained.

    @param roach : ID of the ROACH
    @type  roach : int

    @param adc : number of the ZDOC slot for the ADC (0 or 1)
    @type  adc : int

    @param inp : RF input number for the ADC
    @type  inp : int

    @param gain : RF section gain in dB (-11.5 to +20)
    @type  gain : float

    @param enabled : True for the RF section to pass the signal
    @type  enabled : bool
    """
    self.logger.debug("set_RF: called for ROACH %s ADC %d RF %d",
                      roach,adc,inp)
    if gain:
      self.logger.debug("set_RF: gain is %s",gain)
    self.logger.debug("set_RF: enabled is %s", enabled)
    self.IF_on[roach][adc][inp], self.gain[roach][adc][inp] = \
                      self.mgr.set_RF_section(roach,
                                              adc = adc,
                                              inp = inp,
                                              gain = gain,
                                              enabled = bool(enabled))
    self.logger.debug("set_RF: server returned enabled %s, gain %s",
                      self.IF_on[roach][adc][inp], self.gain[roach][adc][inp])

  def get_accums(self,roach,adc,rf):
    """
    """
    r_index = self.roach_keys[roach]
    self.logger.debug("get_accums: entered for ROACH %s ADC %d RF %d",
                      r_index,adc,rf)
    try:
      response = self.mgr.get_spectra(r_index,adc,rf)
    except RuntimeError:
      self.logger.warning("get_accums: no response")
      return None
    else:
      self.logger.debug("get_accums: response: %s", response)
      return response

  def get_ADC_samples(self,roach,adc,rf):
    """
    Request ADC samples from the server

    @param roach : roach name
    @type  roach : str

    @param adc : ADC number
    @type  adc : int

    @param rf : RF number
    @type  rf : int
    """
    self.logger.debug("get_ADC_samples: entered for ROACH %s ADC %d RF %d",
                      roach,adc,rf)
    try:
      response = self.mgr.get_ADC_samples(roach,adc,rf)
    except RuntimeError:
      response = None
    else:
      self.logger.debug("get_ADC_samples: response: %s", response)
      return response
    
  def get_temperatures(self):
    """
    """
    self.temps = self.mgr.get_temperatures()
    self.amb_temps = {}
    self.chip_temps = {}
    for roach in list(self.temps.keys()):
      self.amb_temps[roach] = {}
      self.chip_temps[roach] = {}
      for adc in list(self.temps[roach].keys()):
        self.amb_temps[roach][adc] = self.temps[roach][adc]['ambient']
        self.chip_temps[roach][adc] = self.temps[roach][adc]['IC']
    return self.temps

  def list_devices(self, roach_keys=[]):
    """
    List the registers for the designated firmware in a list

    @param roach_keys : optional list of ROACH numbers; default all
    @type  roach_keys : list of int

    @return: sorted list of register names
    """
    if roach_keys == []:
      try:
        roach_keys = self.roach_keys
      except NameError:
        self.roach_keys = self.mgr.request("self.spec.keys()")
        self.roach_keys.sort()
        roach_keys = self.roach_keys
    regs = self.mgr.list_dev(roach_keys)
    return regs

  def get_registers(self,roach):
    """
    List the registers of a ROACH's firmware.

    Convenient way to call list_dev using ROACH name

    @param roach : ROACH name
    @type  roach : str

    @return: sorted list of register names
    """
    roachnum = int(roach[-1:])
    roachID = (roachnum/2)*2
    return self.list_devices([roachID])

  def get_board_IDs(self):
    """
    Gets the manufacturer's board IDs
    """
    return self.mgr.get_board_IDs()

  def get_register_details(self,roach):
    """
    Get the details for the registers in ROACH's firmware.

    This first gets the ROACH's firmware ID and then returns the
    register details.

    @param roach : ROACH name
    @type  roach : str
    """
    self.logger.debug("get_register_details: for %s",roach)
    keys = self.mgr.request("self.firmware.keys()")
    self.logger.debug("get_register_details: Firmware keys: %s", keys)
    if keys:
      try:
        fw = self.mgr.request("self.firmware['"+roach+"']")
      except KeyError:
        fw = "Unknown"
    else:
      fw = "Unknown"
    if fw == "Unknown":
      self.logger.warning("get_register_details: firmware for %s is unknown",
                          roach)
      return {}
    else:
      self.logger.debug("get_register_details: requesting for %s",fw)
      self.register_details[roach] = self.mgr.request(
                         "self.firmware_server.parse_registers('"+fw+"')")
      return self.register_details[roach]

  # ---------------- methods for managing firmware ----------------------
  
  def get_firmware_details(self):
    """
    Get the details for the firmware loaded in the ROACH boards
    """
    self.firmware = {}
    self.fw_details = {}
    self.firmware_index = {}
    self.mgr.request("self.get_firmware_states()")
    self.fw_states = self.mgr.request("self.firmware_states")
    self.logger.debug("get_firmware_details: firmware states: %s",
                     self.fw_states)
    for roach in self.roach_keys:
      roachnum = int(roach[-1])-1
      self.logger.debug("get_firmware_details: processing roach %s",roach)
      self.firmware_index[roachnum] = self.fw_states[roachnum]
      self.firmware[roach] = self.mgr.request("self.firmware['"+roach+"']")
      self.logger.debug("get_firmware_details: %s has firmware '%s'",
                            roach, self.firmware[roach])
      if self.firmware[roach] != 'None':
        try:
          self.fw_details[roach] = self.mgr.get_firmware_summary(
                                                          self.firmware[roach])
        except KeyError:
          self.logger.warning("get_firmware_details: %s has no firmware",
                                roach)
          self.fw_details[roach] = None
        except Exception as details:
          self.logger.error(
                     "get_firmware_details: could not get %s firmware details",
                     roach, exc_info=True)
          self.fw_details[roach] = None
      else:
        self.firmware[roach] = None
        self.fw_details[roach] = None
    return self.fw_details

  def load_firmware(self,roach,firmware):
    """
    Load the designated firmware without software initialization

    Since 'attach_roach' returns a Roach() instance, which Pyro
    cannot handle, we use the 'request' method.

    @param roach : ROACH name
    @type  roach : str

    @param firmware : firmware name (column A in spreadsheet
    @type  firmware : str
    """
    self.logger.debug("load_firmware: requesting: %s", firmware)
    bitfile = self.mgr.attach_roach(self.roach,firmware)
    self.logger.debug("load_firmware: bitfile: %s", bitfile)
    return bitfile

  def validate_spreadsheet(self, roach, firmware, fs):
    """
    This checks the sheet for the designated firmware

    It checks to see if all the actual registers in the firmware are in
    the spreadsheet.  If not, it appends missing registers as the bottom
    row.  It also checks for registers in the spreadsheet that are not
    in the firmware and reports those.

    This uses the local copy of the spreadsheet, not the one on the server.
    The user can then do updates and commit them when ready.
    """
    # Load the firmware
    self.logger.info('validate_spreadsheet: loading %s into %s',
                     firmware, roach)
    try:
      self.load_firmware(roach,firmware)
    except Exception:
      self.logger.error("validate_spreadsheet: failed", exc_info=True)
      return
    loaded_firmware = self.get_firmware_details()
    self.logger.info("validate_spreadsheet: current firmware: %s",
                     loaded_firmware)
    # Get a list of registers
    registers = self.get_registers(roach)[1]
    registers.sort()
    self.logger.debug("validate_spreadsheet: registers: %s",registers)
    # Get a list of register keys from the spreadsheet
    try:
      reg_keys = fs.get_keys(sheetname=firmware)
    except AttributeError:
      self.logger.warning("validate_spreadsheet: no sheet for %s",firmware)
      sh = fs.firmware_wb.create_sheet(title=firmware)
      self.logger.warning("validate_spreadsheet: created sheet for %s",
                          firmware)
      sh.cell(row=0,column=0).value = "Register"
      reg_keys = []
    except Exception:
      self.logger.error("validate_spreadsheet: problem getting keys for %s",
                          firmware, exc_info=True)
      return
    else:
      reg_keys.sort()
      self.logger.debug("validate_spreadsheet: known registers: %s", reg_keys)
    # Open the firmware sheet
    try:
      sheet = fs.firmware_wb.get_sheet_by_name(firmware)
    except Exception:
      self.logger.error("validate_spreadsheet: problem getting sheet for %s",
                        firmware, exc_info=True)
      return
    if sheet == None:
      self.logger.warning("validate_spreadsheet: no sheet found for %s",
                          firmware)
      return
    high_row = sheet.get_highest_row()
    self.logger.info("validate_spreadsheet: highest row = % d", high_row)
    # Are all the known registers in the spreadsheet?
    for key in registers:
      try:
        reg_keys.index(key)
      except ValueError:
        self.logger.error("validate_spreadsheet: %s is not in sheet",key)
        sheet.cell(row=sheet.get_highest_row(), column=0).value = key
    # Are all the registers in the spreadsheet in the firmware?
    for reg in reg_keys:
      # Ignore empty cells
      if reg:
        try:
          registers.index(reg)
        except ValueError:
          self.logger.error("validate_spreadsheet: %s in not in the firmware",
                            reg)

  # ------------------------ methods requiring firmware -----------------------

  def get_ADC_level(self,roachnum,ADCnum,RFnum):
    """
    """
    return self.mgr.request("self.spec["+str(roachnum)+"]["\
                                        +str(ADCnum)+"]["\
                                        +str(RFnum)+"].get_ADC_input()")

  def fpga_read_int(self, roachID, register):
    return self.mgr.fpga_read_int(roachID, register)

  def fpga_read_uint(self, roachID, register):
    return self.mgr.fpga_read_uint(roachID, register)

  def fpga_read(self, roachID, register, size, offset=0):
    return self.mgr.fpga_read(roachID, register, size, offset)

  def fpga_write(self, roachID, register, data, offset=0):
    return self.mgr.fpga_write(roachID, register, data, offset)

  def fpga_write_int(self, roachID, register, integer,
                     blindwrite=False, offset=0):
    return self.mgr.fpga_write_int(roachID, register, integer,
                     blindwrite, offset)

  def get_kurt_gbe0_state(self, roachID):
    return self.mgr.request(
                 "self.roaches["+str(roachID)+"].get_gbe0_states()")

if __name__ == "__main__":
  """
  Simple test of ManagerClient()

  This shows how a client GUI might be initialized
  """
  from local_dirs import log_dir as logpath
  #from support.tunneling import module_logger as Tlogger
  from support.logs import init_logging, get_loglevel, set_loglevel
  
  from optparse import OptionParser
  p = OptionParser()
  p.set_usage('ManagerClient.py [options]')
  p.set_description(__doc__)

  p.add_option('-l', '--log_level',
               dest = 'loglevel',
               type = 'str',
               default = 'warning',
               help = 'Logging level for main program and modules')
  opts, args = p.parse_args(sys.argv[1:])

  __name__ = "DTO_mgr_client"
  logging.basicConfig(level=logging.WARNING)
  mylogger = logging.getLogger()
  mylogger = init_logging(mylogger,
               loglevel = logging.INFO,
               consolevel = logging.WARNING,
               logname = logpath+"DTO_client.log")
  set_loglevel(mylogger, get_loglevel(opts.loglevel))
  #Tlogger.setLevel(logging.WARNING)

  client = ManagerClient()

  fw_keys = client.firmware_keys
  mylogger.info(" Firmware available: %s", fw_keys)
  #try:
  mylogger.info(" Temperatures: %s",str(client.temps))
  mylogger.info(" Switch states: %s", client.switch_states)
  mylogger.info(" Synthesizer states: %s", client.synth_data)
  mylogger.info(" ROACH IDs: %s", client.get_board_IDs())
  mylogger.info(" Registers: %s", client.get_register_values('roach1'))
  print("\nBefore closing ipython, do: cleanup_tunnels()")
