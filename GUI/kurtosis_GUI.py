# -*- coding: utf-8 -*-
"""
Widgets for kurtosis firmware monitor and control
"""
from PyQt4 import QtCore, QtGui
import logging

from Qt_widgets import slotgen, slot_wrapper

module_logger = logging.getLogger(__name__)

class RadioGroup(QtGui.QGroupBox):
  """
  A group of radio buttons
  """
  def __init__(self,
               parent=None, frame=None, title=None, tooltip=None, font=None,
               buttons=[], check_selection=-1, action=None):
    """
    Initialize a RadioGroup
    
    @param parent : a Ui_kurtosisMC instance
    @param frame : a ControlPanelGriddedFrame instance
    @param title : text at the top of the box with the group name
    @param tooltip : pop-up text when the cursor is over the box
    @param font : font used in the box
    @param buttons : a set of labels for the radio buttons
    @param check_selection : the ID of the button to be selected initially
    @param action : a method associated with a button selection
    """
    self.logger = logging.getLogger(__name__+".RadioGroup")
    QtGui.QGroupBox.__init__(self,frame)
    if title:
      self.setTitle(title)
    if tooltip:
      self.setToolTip(tooltip)
    if font:
      self.setFont(font)
    self.layout = QtGui.QVBoxLayout(self)
    self.layout.setSpacing(0)
    self.layout.setMargin(0)
    self.labels = buttons
    self.buttons = {}
    #self.height = 25
    for index in range(len(buttons)):
      self.buttons[index] = QtGui.QRadioButton(self)
      self.buttons[index].setText(self.labels[index])
      if index == check_selection:
        self.buttons[index].setChecked(True)
      self.layout.addWidget(self.buttons[index])
      #self.height += 20
      if action:
        wrapped_slot = slotgen((action,
                                parent.refresh_UI,
                                parent.column,
                                title,
                                index),
                               slot_wrapper)
        self.buttons[index].clicked.connect(wrapped_slot)
  
class Ui_kurtosisMC(QtGui.QFrame):
    """
    Lays out a frame with M&C functions for the kurtosis firmware.

    The frame is a widget in a row, one cell for each ROACH.

    Public attributes::
      column    -
      logger    -
      parent    -
      roachname -
    """
    def __init__(self, parent, column):
        """
        Create a Ui_kurtosisMC instance
        
        @param parent : parent of this frame
        @type  parent : ControlPanelGriddedFrame object

        @param column : column index for this widget
        @type  column : tuple
        """
        self.logger = logging.getLogger(__name__+".Ui_kurtosisMC")
        QtGui.QFrame.__init__(self,parent=parent)
        self.logger.debug("Ui_kurtosisMC parent = %s",parent)
        self.logger.debug("Ui_kurtosisMC grandparent = %s",parent.parent)
        self.logger.debug("Ui_kurtosisMC column = %s",column)
        self.parent = parent
        self.column = column
        self.roachname = 'roach'+str(column+1)
        self.setupUi(parent)
        self.refresh_UI()

    def mousePressEvent(self, *args):
        print "Blimey!", args, "in", self.roachname
      
    def setupUi(self, kurtosisMC):
        """
        Generate the Ui_kurtosisMC

        @param kurtosisMC : the gridded frame to which this belongs
        @type  kurtosisMC : ControlPanelGriddedFrame object
        """
        self.logger.debug("Ui_kurtosisMC setting up UI for %s in %s",
                          self.roachname, kurtosisMC)
        font = QtGui.QFont()
        font.setWeight(50)
        font.setBold(False)

        register_vals = kurtosisMC.parent.register_values[self.roachname]
        self.logger.debug("setupUI: %s register values: %s",
                          self.roachname, register_vals)

        page_layout = QtGui.QHBoxLayout(self)
        left_layout = QtGui.QVBoxLayout()
        left_layout.setSpacing(0)
        left_layout.setMargin(0)
        right_layout = QtGui.QVBoxLayout()
        right_layout.setSpacing(0)
        right_layout.setMargin(0)
        #-------------------------------------------------------------------
        ADCsnapLayoutWidget = QtGui.QWidget(kurtosisMC)
        ADCsnapLayout = QtGui.QVBoxLayout(ADCsnapLayoutWidget)
        ADCsnapLayout.setSpacing(0)
        ADCsnapLayout.setMargin(0)
        self.ADCsnapGroup = RadioGroup(
                     parent = self,
                     frame = ADCsnapLayoutWidget,
                     title = "ADC Snap Trigger",
                     tooltip = "Selects trigger source for ADC BRAM snapshots",
                     font=font,
                     buttons=["Pol 0","Pol 1","Both pols"],
                     check_selection = register_vals['adc_snap_trig'],
                     action=kurtosisMC.parent.logic.change_ADC_snap_trigger)
        ADCsnapLayout.addWidget(self.ADCsnapGroup)
        left_layout.addWidget(ADCsnapLayoutWidget)
        #----------------------------------------------------------------------
        syncLayoutWidget = QtGui.QWidget(kurtosisMC)
        syncLayout = QtGui.QVBoxLayout(syncLayoutWidget)
        syncLayout.setSpacing(0)
        syncLayout.setMargin(0)
        self.syncSelGroup = RadioGroup(
                     parent = self,
                     frame = syncLayoutWidget,
                     title = "Sync Select",
                     tooltip = "Source of DSP sync pulses",
                     font=font,
                     buttons=["1 PPS", "User"],
                     check_selection = register_vals['sync_in_sel'],
                     action=kurtosisMC.parent.logic.update_sync_select)
        syncLayout.addWidget(self.syncSelGroup)
        self.syncPush = QtGui.QPushButton(syncLayoutWidget)
        self.syncPush.setText("Sync pulse")
        self.syncPush.setToolTip(
                              "Re-synchronize the DSP, if Sync Select is User")
        wrapped_slot = slotgen((kurtosisMC.parent.logic.sync_DSP,
                                self.refresh_UI,
                                self.column,),
                               slot_wrapper)
        self.syncPush.pressed.connect(wrapped_slot)
        syncLayout.addWidget(self.syncPush)
        left_layout.addWidget(syncLayoutWidget)
        #----------------------------------------------------------------------
        secCntrLayoutWidget = QtGui.QWidget(kurtosisMC)
        secCntrLayout = QtGui.QVBoxLayout(secCntrLayoutWidget)
        secCntrLayout.setSpacing(0)
        secCntrLayout.setMargin(0)
        self.secondsCntr = QtGui.QLabel(secCntrLayoutWidget)
        self.secondsCntr.setAlignment(QtCore.Qt.AlignCenter)
        self.secondsCntr.setToolTip("Seconds counter in packet header")
        self.secondsCntr.setText("Seconds Counter")
        self.secondsCntr.setWordWrap(True)
        secCntrLayout.addWidget(self.secondsCntr)
        self.secCntrRst = QtGui.QPushButton(secCntrLayoutWidget)
        self.secCntrRst.setText("Reset")
        self.secCntrRst.setToolTip("Set seconds counter to zero")
        wrapped_slot = slotgen((kurtosisMC.parent.logic.reset_sec_cntr,
                                self.refresh_UI,
                                self.column,),
                               slot_wrapper)
        self.secCntrRst.pressed.connect(wrapped_slot)
        secCntrLayout.addWidget(self.secCntrRst)
        left_layout.addWidget(secCntrLayoutWidget)
        #----------------------------------------------------------------------
        pktCntRstSelectWidget = QtGui.QWidget(kurtosisMC)
        pktCntRstSelectLayout = QtGui.QVBoxLayout(pktCntRstSelectWidget)
        pktCntRstSelectLayout.setSpacing(0)
        pktCntRstSelectLayout.setMargin(0)
        self.pktCntRstSelectGroup = RadioGroup(
                 parent = self,
                 frame =pktCntRstSelectWidget,
                 title="reset select",
               tooltip = "Source of reset for current second's packet counter",
                 font=font,
                 buttons=["sync","1 PPS"],
                 check_selection = register_vals['pkt_cnt_sec_rst_ctrl'],
                 action=kurtosisMC.parent.logic.update_reset_select)
        pktCntRstSelectLayout.addWidget(self.pktCntRstSelectGroup)
        left_layout.addWidget(pktCntRstSelectWidget)
        #----------------------------------------------------------------------
        self.pwrBitsSelLayoutWidget = QtGui.QWidget(kurtosisMC)
        self.powerBitsSelectLayout = QtGui.QVBoxLayout(
                                                   self.pwrBitsSelLayoutWidget)
        self.powerBitsSelectLayout.setSpacing(0)
        self.powerBitsSelectLayout.setMargin(0)
        self.powerBitsLabel = QtGui.QLabel(self.pwrBitsSelLayoutWidget)
        self.powerBitsLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.powerBitsLabel.setText("Power bit select for 10GbE")
        self.powerBitsLabel.setWordWrap(True)
        self.powerBitsSelectLayout.addWidget(self.powerBitsLabel)
        self.powerBitsSpinBox = QtGui.QSpinBox(self.pwrBitsSelLayoutWidget)
        self.powerBitsSpinBox.setToolTip(
        "Offset from MSB for the 16 bits of power accumulator to send to 10 GbE")
        self.powerBitsSpinBox.setMinimum(5)
        self.powerBitsSpinBox.setMaximum(31)
        power_bits =  register_vals['select_bits_pow']
        self.powerBitsSpinBox.setValue(power_bits)
        wrapped_slot = slotgen((kurtosisMC.parent.logic.set_power_bits,
                                self.refresh_UI,
                                self.column),
                               slot_wrapper)
        self.powerBitsSpinBox.valueChanged.connect(wrapped_slot)
        self.powerBitsSelectLayout.addWidget(self.powerBitsSpinBox)
        self.powerBitsSlider = QtGui.QSlider(self.pwrBitsSelLayoutWidget)
        self.powerBitsSlider.setMaximum(63)
        self.powerBitsSlider.setValue(5)
        self.powerBitsSlider.setPageStep(16)
        self.powerBitsSlider.setOrientation(QtCore.Qt.Horizontal)
        self.powerBitsSlider.setDisabled(True)
        self.powerBitsSpinBox.valueChanged.connect(
                                                 self.powerBitsSlider.setValue)
        self.powerBitsSelectLayout.addWidget(self.powerBitsSlider)
        left_layout.addWidget(self.pwrBitsSelLayoutWidget)
        #----------------------------------------------------------------------
        self.accumLayoutWidget = QtGui.QWidget(kurtosisMC)
        self.accumLayout = QtGui.QVBoxLayout(self.accumLayoutWidget)
        self.accumLayout.setSpacing(0)
        self.accumLayout.setMargin(0)
        self.accumLabel = QtGui.QLabel(self.accumLayoutWidget)
        self.accumLabel.setFont(font)
        self.accumLabel.setToolTip("Number of spectra per accumulation")
        self.accumLabel.setText("Spectra per intgn")
        self.accumLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.accumLayout.addWidget(self.accumLabel)
        self.accumSpin = QtGui.QSpinBox(self.accumLayoutWidget)
        self.accumSpin.setToolTip("63 spectra = 100 us")
        self.accumSpin.setLayoutDirection(QtCore.Qt.RightToLeft)
        self.accumSpin.setMinimum(1)
        self.accumSpin.setMaximum(63)
        acc_len = register_vals['acc_len_m1']
        self.accumSpin.setProperty("value", acc_len)
        wrapped_slot = slotgen((kurtosisMC.parent.logic.set_acc_len,
                                self.refresh_UI,
                                self.column),
                               slot_wrapper)
        self.accumSpin.valueChanged.connect(wrapped_slot)
        self.accumLayout.addWidget(self.accumSpin)
        left_layout.addWidget(self.accumLayoutWidget)
        #----------------------------------------------------------------------
        self.integsLayoutWidget = QtGui.QWidget(kurtosisMC)
        self.integsLayout = QtGui.QVBoxLayout(self.integsLayoutWidget)
        self.integsLayout.setSpacing(0)
        self.integsLayout.setMargin(0)
        self.integsLabel = QtGui.QLabel(self.integsLayoutWidget)
        self.integsLabel.setFont(font)
        self.integsLabel.setToolTip("Number of integrations since reset")
        self.integsLabel.setText("Integrations")
        self.integsLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.integsLayout.addWidget(self.integsLabel)
        self.integsValue = QtGui.QLineEdit(self.integsLayoutWidget)
        self.integsValue.setAlignment(QtCore.Qt.AlignRight)
        self.integsValue.setMaxLength(10)
        self.integsValue.setReadOnly(True)
        spec_count = register_vals['spec_count']
        self.integsValue.setText(str(spec_count))
        self.integsLayout.addWidget(self.integsValue)
        left_layout.addWidget(self.integsLayoutWidget)
        #----------------------------------------------------------------------
        self.totalCountLayoutWidget = QtGui.QWidget(kurtosisMC)
        self.totalCountLayout = QtGui.QVBoxLayout(self.totalCountLayoutWidget)
        self.totalCountLayout.setSpacing(0)
        self.totalCountLayout.setMargin(0)
        self.pktCntLabel = QtGui.QLabel(self.totalCountLayoutWidget)
        self.pktCntLabel.setText("Total count")
        self.pktCntLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.totalCountLayout.addWidget(self.pktCntLabel)
        self.pktCntValue = QtGui.QLineEdit(self.totalCountLayoutWidget)
        self.pktCntValue.setAlignment(QtCore.Qt.AlignRight)
        self.pktCntValue.setToolTip(
                         "Counts packets or FPGA clock ticks since last reset")
        self.pktCntValue.setMaxLength(10)
        self.pktCntValue.setReadOnly(True)
        self.totalCountLayout.addWidget(self.pktCntValue)
        right_layout.addWidget(self.totalCountLayoutWidget)
        #----------------------------------------------------------------------
        cntTypeLayoutWidget = QtGui.QWidget(kurtosisMC)
        cntTypeLayout = QtGui.QVBoxLayout(cntTypeLayoutWidget)
        cntTypeLayout.setSpacing(0)
        cntTypeLayout.setMargin(0)
        self.cntTypeGroup = RadioGroup(
               parent = self,
               frame =cntTypeLayoutWidget,
               title="Counter units", font=font,
               buttons=["packets","system ticks"],
               check_selection=register_vals['raw_pkt_cnt_is_fpga_clocks'],
               action=kurtosisMC.parent.logic.change_counter_units)
        cntTypeLayout.addWidget(self.cntTypeGroup)
        right_layout.addWidget(cntTypeLayoutWidget)
        #----------------------------------------------------------------------
        rawCountResetWidget = QtGui.QWidget(kurtosisMC)
        rawCountResetLayout = QtGui.QVBoxLayout(rawCountResetWidget)
        rawCountResetLayout.setSpacing(0)
        rawCountResetLayout.setMargin(0)
        self.rawCountResetGroup = RadioGroup(
                        parent = self,
                        frame =rawCountResetWidget,
                        title="Counter reset by", font=font,
                        buttons=["sync","1 PPS", "User"],
                        check_selection=register_vals['raw_pkt_cnt_rst_ctrl'],
                        action=kurtosisMC.parent.logic.counter_reset_select)
        rawCountResetLayout.addWidget(self.rawCountResetGroup)
        self.rawRstUserPush = QtGui.QPushButton(kurtosisMC)
        self.rawRstUserPush.setText("Reset")
        wrapped_slot = slotgen((kurtosisMC.parent.logic.reset_DSP,
                                self.refresh_UI,
                                self.column,),
                               slot_wrapper)
        self.rawRstUserPush.pressed.connect(wrapped_slot)
        rawCountResetLayout.addWidget(self.rawRstUserPush)
        right_layout.addWidget(rawCountResetWidget)
        #----------------------------------------------------------------------
        self.verticalLayoutWidget_11 = QtGui.QWidget(kurtosisMC)
        self.gbe0layout = QtGui.QVBoxLayout(self.verticalLayoutWidget_11)
        self.gbe0layout.setSpacing(0)
        self.gbe0layout.setMargin(0)
        self.gbe0label = QtGui.QLabel(self.verticalLayoutWidget_11)
        self.gbe0label.setText("10 GbE 0")
        self.gbe0label.setAlignment(QtCore.Qt.AlignCenter)
        self.gbe0layout.addWidget(self.gbe0label)
        
        self.gbe0linkCheck = QtGui.QCheckBox(self.verticalLayoutWidget_11)
        self.gbe0linkCheck.setText("linked up")
        self.gbe0linkCheck.setToolTip("10 GbE port 0 has a connection")
        self.gbe0linkCheck.setDisabled(True)
        self.gbe0layout.addWidget(self.gbe0linkCheck)
        
        self.gbe0xmitCheck = QtGui.QCheckBox(self.verticalLayoutWidget_11)
        self.gbe0xmitCheck.setToolTip("10 GbE port 0 is sending data")
        self.gbe0xmitCheck.setText("transmitting")
        self.gbe0xmitCheck.setDisabled(True)
        self.gbe0layout.addWidget(self.gbe0xmitCheck)
        
        self.gbe0fullCheck = QtGui.QCheckBox(self.verticalLayoutWidget_11)
        self.gbe0fullCheck.setToolTip("10 GbE 0 buffer is almost full")
        self.gbe0fullCheck.setText("full")
        self.gbe0fullCheck.setDisabled(True)
        self.gbe0layout.addWidget(self.gbe0fullCheck)
        
        self.gbe0oflowCheck = QtGui.QCheckBox(self.verticalLayoutWidget_11)
        self.gbe0oflowCheck.setToolTip(
                               "10 GbE 0 buffer has overflowed; data was lost")
        self.gbe0oflowCheck.setText("overflowed")
        self.gbe0oflowCheck.setDisabled(True)
        self.gbe0layout.addWidget(self.gbe0oflowCheck)
        right_layout.addWidget(self.verticalLayoutWidget_11)
        #----------------------------------------------------------------------
        self.gbePktCntWidget = QtGui.QWidget(kurtosisMC)
        self.gbePktCntLayout = QtGui.QVBoxLayout(self.gbePktCntWidget)
        self.gbePktCntLayout.setSpacing(0)
        self.gbePktCntLayout.setMargin(0)
        self.gbe0pktCntLabel = QtGui.QLabel(self.gbePktCntWidget)
        self.gbe0pktCntLabel.setText("Packet count")
        self.gbe0pktCntLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.gbePktCntLayout.addWidget(self.gbe0pktCntLabel)
        self.gbe0pktCntValue = QtGui.QLineEdit(self.gbePktCntWidget)
        self.gbe0pktCntValue.setAlignment(QtCore.Qt.AlignRight)
        self.gbe0pktCntValue.setMaxLength(10)
        tx_pkt_cnt = register_vals['gbe0_tx_cnt']
        self.gbe0pktCntValue.setText(str(tx_pkt_cnt))
        self.gbePktCntLayout.addWidget(self.gbe0pktCntValue)
        right_layout.addWidget(self.gbePktCntWidget)
        #----------------------------------------------------------------------
        gbe0sourceWidget = QtGui.QWidget(kurtosisMC)
        gbe0sourceLayout = QtGui.QVBoxLayout(gbe0sourceWidget)
        gbe0sourceLayout.setSpacing(0)
        gbe0sourceLayout.setMargin(0)
        self.gbe0sourceGroup = RadioGroup(
                       parent = self,
                       frame =gbe0sourceWidget,
                       title="Data source", font=font,
                       buttons=["DSP output","Test data"],
                       check_selection=register_vals['bit_select_counter_out'],
                       action=kurtosisMC.parent.logic.select_gbe0_data_source)
        gbe0sourceLayout.addWidget(self.gbe0sourceGroup)
        right_layout.addWidget(gbe0sourceWidget)

        page_layout.addLayout(left_layout)
        page_layout.addLayout(right_layout)

        #QtCore.QMetaObject.connectSlotsByName(kurtosisMC)

    def refresh_gbe0(self):
        """
        Gets the 10 GbE port 0 status and sets the radiobuttons
        """
        roachID = self.column
        client = self.parent.parent
        server = client.mgr

        request = "self.roaches['"+self.roachname+"'].get_gbe0_states()"
        gbe0_state = server.request(request)
        self.logger.debug("refresh_gbe0: gbe0 state = %s", gbe0_state)
        self.gbe0linkCheck.setChecked(bool(gbe0_state['linkup']))
        self.gbe0xmitCheck.setChecked(bool(gbe0_state['tx']))
        self.gbe0fullCheck.setChecked(bool(gbe0_state['full']))
        self.gbe0oflowCheck.setChecked(bool(gbe0_state['over']))

    def refresh_UI(self):
        """
        Update the Ui_kurtosisMC widget

        Left column::
          ADCsnapGroup         adc_snap_trig
          syncSelGroup         sync_in_sel
          pktCntRstSelectGroup pkt_cnt_sec_rst_ctrl
          powerBitsSpinBox     select_bits_pow
          accumSpin            acc_len_m1
          integsValue          spec_count

        Right column::
          pktCntValue
          cntTypeGroup         raw_pkt_cnt_is_fpga_clocks
          rawCountResetGroup   raw_pkt_cnt_rst_ctrl
          gbe0linkCheck        gbe0_linkup
          gbe0xmitCheck        gbe0_tx
          gbe0fullCheck        gbe0_tx_full
          gbe0oflowCheck       gbe0_tx_over
          gbe0pktCntValue      gbe0_tx_cnt
          gbe0sourceGroup      bit_select_counter_out
        """
        roachID = self.column
        frame = self.parent
        client = self.parent.parent
        server = client.mgr

        roachname = "roach"+str(roachID+1)
        self.parent.parent.get_register_values(roachname)
        register_vals = self.parent.parent.register_values[roachname]
        self.logger.debug("refresh_UI: ROACH %d register values: %s",
                          roachID, register_vals)

        # left column
        ADC_snap_trigger = register_vals['adc_snap_trig']
        self.ADCsnapGroup.buttons[ADC_snap_trigger].setChecked(True)

        sync_select = register_vals['sync_in_sel']
        self.syncSelGroup.buttons[sync_select].setChecked(True)

        pkt_cnt_reset_sel = register_vals['pkt_cnt_sec_rst_ctrl']
        self.pktCntRstSelectGroup.buttons[pkt_cnt_reset_sel].setChecked(True)

        power_bits =  register_vals['select_bits_pow']
        self.powerBitsSpinBox.setValue(power_bits)

        spec_count = register_vals['spec_count']
        self.integsValue.setText(str(spec_count))

        # right column
        raw_pkt_count = register_vals['raw_pkt_cnt_out']
        self.pktCntValue.setText(str(raw_pkt_count))

        cnt_type = register_vals['raw_pkt_cnt_is_fpga_clocks']
        self.cntTypeGroup.buttons[cnt_type].setChecked(True)

        pkt_cnt_rst_ctrl = register_vals['raw_pkt_cnt_rst_ctrl']
        self.rawCountResetGroup.buttons[pkt_cnt_rst_ctrl].setChecked(True)
        
        self.refresh_gbe0()

        tx_pkt_cnt = register_vals['gbe0_tx_cnt']
        self.gbe0pktCntValue.setText(str(tx_pkt_cnt))

        pkt_data_source = register_vals['bit_select_counter_out']
        self.gbe0sourceGroup.buttons[pkt_data_source].setChecked(True)
        