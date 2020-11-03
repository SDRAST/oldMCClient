# -*- coding: utf-8 -*-
"""
kurtosis_client - module for client to interact with kurtosis firmware
"""
import logging

module_logger = logging.getLogger(__name__)
 
class KurtosisClient():
  """
  Class to interact with kurtosis logic on the server

  This is used to read and write to registers in the kurtosis firmware
  in a context that implies understanding of the firmware.  ManagerClient
  can read (and write to) registers but it doesn't understand what they do.
  """
  def __init__(self, parent, roach):
    """
    @param roach : a server roach which has kurtosis firmware
    """
    self.logger = logging.getLogger(__name__+".KurtosisClient")
    self.roach = roach
    self.logger.debug("__init__: invoked for ROACH %s", self.roach)
    self.parent = parent

  def get_synch_select(self):
    self.synch_select[self.roach] = self.parent.mgr.fpga_read_uint(roach,
                                                                'sync_in_sel')
    return self.synch_select[self.roach]

  def sync_DSP(self,*args):
    self.logger.debug("sync_DPS: called with: %s",args)
    roach = self.parent.roach_keys[args[0]]
    self.parent.mgr.request("self.roaches["+str(roach)+"].logic.sync_DSP()")

  def update_sync_select(self,*args):
    self.logger.debug("update_sync_select: called with: %s", args)
    roach       = self.parent.roach_keys[args[0]]
    buttongroup = args[1]
    value       = args[2]
    self.logger.debug("update_sync_select: writing %d to ROACH %d sync_in_sel",
                      value, roach) 
    self.parent.mgr.fpga_write_int(roach,'sync_in_sel',value)
    readback = self.parent.mgr.fpga_read_int(roach,'sync_in_sel')
    self.parent.register_values[roach]['sync_in_sel'] = readback
    return readback

  def change_ADC_snap_trigger(self, *args):
    self.logger.debug("change_ADC_snap_trigger: called with: %s", args)
    roach = self.parent.roach_keys[args[0]]
    buttongroup = args[1]
    value = args[2]
    self.logger.debug(
            "change_ADC_snap_trigger: writing %d to ROACH %d adc_snap_trig",
            value, roach)
    self.parent.mgr.fpga_write_int(roach,'adc_snap_trig',value)
    readback = self.parent.mgr.fpga_read_int(roach,'adc_snap_trig')
    self.parent.register_values[roach]['adc_snap_trig'] = readback
    return readback

  def update_reset_select(self,*args):
    self.logger.debug("update_reset_select: called with: %s", args)
    roach = self.parent.roach_keys[args[0]]
    buttongroup = args[1]
    value = args[2]
    readback = self._write_register(roach,'pkt_cnt_sec_rst_ctrl', value)
    return readback

  def reset_sec_cntr(self, *args):
    self.logger.debug("reset_sec_cntr: called with: %s", args)
    roach = self.parent.roach_keys[args[0]]
    self.parent.mgr.request("self.roaches[" +
                            str(roach) + "].logic.seconds_cntr_reset()")

  def _write_register(self, roach, register, value):
    self.logger.debug("_write_register: writing %d to ROACH %d %s",
                      value, roach, register)
    self.parent.mgr.fpga_write_int(roach, register, value)
    readback = self.parent.mgr.fpga_read_int(roach, register)
    self.parent.register_values[roach][register] = readback
    self.logger.debug("_write_register: returned %d", readback)
    return readback

  def set_power_bits(self,*args):
    self.logger.debug("set_power_bits: called with: %s",args)
    roach = self.parent.roach_keys[args[0]]
    value = args[1]
    readback = self._write_register(roach, 'select_bits_pow', value)
    return readback

  def set_acc_len(self, *args):
    self.logger.debug("set_acc_len: called with: %s", args)
    roach = self.parent.roach_keys[args[0]]
    value = args[1]
    readback = self._write_register(roach, 'acc_len_m1', value)
    return readback

  def change_counter_units(self,*args):
    self.logger.debug("change_counter_units: called with: %s", args)
    roach = self.parent.roach_keys[args[0]]
    buttongroup = args[1]
    value = args[2]
    readback = self._write_register(roach, 'raw_pkt_cnt_is_fpga_clocks', value)
    return readback

  def counter_reset_select(self,*args):
    self.logger.debug("counter_reset_select: called with: %s", args)
    roach = self.parent.roach_keys[args[0]]
    buttongroup = args[1]
    value = args[2]
    readback = self._write_register(roach, 'raw_pkt_cnt_rst_ctrl', value)
    return readback

  def select_gbe0_data_source(self,*args):
    self.logger.debug("select_gbe0_data_source: called with: %s", args)
    roach = self.parent.roach_keys[args[0]]
    buttongroup = args[1]
    value = args[2]
    readback = self._write_register(roach, 'bit_select_counter_out', value)
    return readback

  def reset_DSP(self, *args):
    self.logger.debug("reset_DSP: called with: %s", args)
    roach = self.parent.roach_keys[args[0]]
    self.parent.mgr.request("self.roaches[" +
                            str(roach) + "].logic.dsp_user_reset()")
    
    
