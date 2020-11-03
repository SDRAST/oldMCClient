"""
WBDC2 monitor and control panel

To Do:
* Attenuator controls left of polarization
* Voltages, currents, temperatures
"""
from PyQt4 import QtGui, QtCore
import logging
import sys
import time

from support.logs import init_logging, get_loglevel, set_loglevel
from support.pyro import get_device_server, cleanup_tunnels
from Qt_widgets import create_action, add_actions, create_option_menu

from MonitorControl.Receivers.WBDC.WBDC2 import WBDC2

TIMER_INTERVAL = 3000

logpath = "/tmp/"

module_logger = logging.getLogger(__name__)

class MainWindow(QtGui.QMainWindow):
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
    self.logger = logging.getLogger(module_logger.name+".MainWindow")
    self.logger.debug(" initializing")
    QtGui.QMainWindow.__init__(self, parent)
    self.logger = mylogger
    self.logger.debug(" superclasses initialized")
    self.wbdc = get_device_server('wbdc2hw_server-mmfranco-0571605')
    # When using a slow connection, the above can take a while
    time.sleep(1)
    self.power_scale = 'mW'
    self.power = {'R1 E': 0.0, 'R1 H': 0.0, 'R2 E':0.0, 'R2 H':0.0}
    self.create_menubar()
    self.logger.debug("menubar created")
    self.central_frame = self.CentralFrame(self)
    self.logger.debug("central_frame: created")
    self.setCentralWidget(self.central_frame)
    self.create_status_bar()
    self.timer = QtCore.QTimer()

  class CentralFrame(QtGui.QFrame):
    def __init__(self, parent):
      self.parent = parent
      self.logger = logging.getLogger(self.parent.logger.name+".Central_Frame")
      self.logger.debug("central_frame: creating...")
      QtGui.QFrame.__init__(self, parent)
      page_layout = QtGui.QHBoxLayout(self)
    
      RF_layout = QtGui.QVBoxLayout()
      RF_layout.setSpacing(0)
      RF_layout.setMargin(0)
      
      Pol_layout = QtGui.QVBoxLayout()
      Pol_layout.setSpacing(0)
      Pol_layout.setMargin(0)
    
      IF_layout = QtGui.QVBoxLayout()
      IF_layout.setSpacing(0)
      IF_layout.setMargin(0)

      self.logger.debug("central_frame: layouts defined")

      self.parent.refresh_data()
      
      self.crossoverCheck = QtGui.QCheckBox("Feeds crossed")
      self.crossoverCheck.stateChanged.connect(self.set_crossover)
      RF_layout.addWidget(self.crossoverCheck)
      
      RFtitle = QtGui.QLabel("RF Section")
      RFtitle.setAlignment(QtCore.Qt.AlignHCenter)
      RF_layout.addWidget(RFtitle)
      self.RFpower = QtGui.QLabel(self.parent.power_scale)
      self.RFpower.setAlignment(QtCore.Qt.AlignHCenter)
      RF_layout.addWidget(self.RFpower)
      pwr_widget = {}
      self.pwr_val = {}
      for chan in ['R1 E', 'R1 H', 'R2 E', 'R2 H']:
        pwr_widget[chan] = QtGui.QHBoxLayout(self)
        lbl = QtGui.QLabel(chan)
        lbl.setAlignment(QtCore.Qt.AlignLeft)
        pwr_widget[chan].addWidget(lbl)
        self.pwr_val[chan] = QtGui.QLabel("%6.3f" % self.parent.power[chan])
        self.pwr_val[chan].setFrameShadow(QtGui.QFrame.Sunken)
        self.pwr_val[chan].setAlignment(QtCore.Qt.AlignRight)
        pwr_widget[chan].addWidget(self.pwr_val[chan])
        RF_layout.addLayout(pwr_widget[chan])

      temp_widget = {}
      self.temp_val = {}
      pwr_points = self.parent.pwr_data.keys()
      pwr_points.sort()
      self.logger.debug(" pwr points: %s", pwr_points)
      for key in pwr_points:
        if key[-5:] == 'plate':
          temp_widget[key] = QtGui.QHBoxLayout(self)
          lbl = QtGui.QLabel(key)
          temp_widget[key].addWidget(lbl)
          temp_widget[key].setAlignment(QtCore.Qt.AlignLeft)
          self.temp_val[key] = QtGui.QLabel("%6.2f" % self.parent.pwr_data[key])
          self.temp_val[key].setAlignment(QtCore.Qt.AlignRight)
          temp_widget[key].addWidget(self.temp_val[key])
          RF_layout.addLayout(temp_widget[key])

      Pol_title = QtGui.QLabel("Polarization")
      Pol_layout.addWidget(Pol_title)
      pol_states = QtGui.QVBoxLayout(self)
      self.polCheck = {}
      for rx in ["R1", "R2"]:
        Pol_layout.addWidget(QtGui.QLabel(rx))
        for band in ["18", "20", "22", "24", "26"]:
          key = rx+'-'+band
          self.polCheck[key] = QtGui.QCheckBox(band)
          self.polCheck[key].setCheckState(self.parent.pol_states[key])
          self.polCheck[key].stateChanged.connect(self.set_pol_state)
          Pol_layout.addWidget(self.polCheck[key])
    
      IFtitle = QtGui.QLabel("Down-converters")
      IF_layout.addWidget(IFtitle)
      IFpolLayout = {}
      for pol in ["P1", "P2"]:
        IFpolRLayout = {}
        IFpolLayout[pol] = QtGui.QHBoxLayout(self)
        for rx in ["R1", "R2"]:
          if rx == 'R1':
            IFpolLayout[pol].addWidget(QtGui.QLabel(pol))
          IFpolRLayout[rx] = QtGui.QVBoxLayout(self)
          IFpolRLayout[rx].addWidget(QtGui.QLabel(rx))
          for band in ["18", "20", "22", "24", "26"]:
            IFpolRLayout[rx].addWidget(QtGui.QCheckBox(band))
          IFpolLayout[pol].addLayout(IFpolRLayout[rx])
        IF_layout.addLayout(IFpolLayout[pol])

      self.VI_points = self.parent.supply_data.keys()
      self.VI_points.sort()
      self.logger.debug(" VI points: %s", self.VI_points)
      self.gridLayout = QtGui.QGridLayout(self)
      row = 0
      self.voltage = {}
      for pt in self.VI_points:
        mon_datum = self.parent.supply_data[pt]
        if pt[-1] == "V" or pt[-3:] == 'ana' or pt[-3:] == 'dig':
          label = QtGui.QLabel(pt)
          self.gridLayout.addWidget(label, row, 0, 1, 1,
                              QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)
          self.voltage[pt] = QtGui.QLabel("%7.3f" % mon_datum)
          self.gridLayout.addWidget(self.voltage[pt], row, 1, 1, 1,
                              QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)
          row += 1
      
      page_layout.addLayout(RF_layout)
      page_layout.addLayout(Pol_layout)
      page_layout.addLayout(IF_layout)
      page_layout.addLayout(self.gridLayout)

      self.logger.debug("central_widget: widgets created")

      self.refresh()

    def refresh(self):
      """
      """
      self.crossoverCheck.setChecked(self.parent.crossSwitch_state)
      # detector powers
      for chan in ['R1 E', 'R1 H', 'R2 E', 'R2 H']:
        self.pwr_val[chan].setText("%6.3f" % self.parent.power[chan])
      
      # temperatures
      for key in self.temp_val.keys():
          self.temp_val[key].setText("%6.2f" % self.parent.pwr_data[key])

      # polarizers
      for key in self.polCheck.keys():
        self.polCheck[key].setCheckState(self.parent.pol_states[key])
      
      # power supply data
      self.RFpower.setText(self.parent.power_scale)
      row = 0
      for pt in self.VI_points:
        mon_datum = self.parent.supply_data[pt]
        if pt[-1] == "V" or pt[-3:] == 'ana' or pt[-3:] == 'dig':
          self.voltage[pt].setText("%7.3f" % mon_datum)
          row += 1

    def set_crossover(self):
      state = self.crossoverCheck.isChecked()
      self.logger.debug("set_crossover: setting state to %s", state)
      self.parent.wbdc.request("self.crossSwitch.set_state("+str(state)+")")

    def set_pol_state(self, *args):
      self.logger.warning("set_pol_state: args = %s", args)
     
  def rebuildUI(self):
    self.central_frame.close()
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
                       "Power &Scale",
                       self.set_power_scale,
                       ["mW","dBm"])
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
    msg = """WBDC2 Client GUI"""
    QtGui.QMessageBox.about(self, "About the demo", msg.strip())

  def quit(self):
    """
    Action for Quit menu button
    """
    self.logger.info("Quitting.")
    self.timer_run = False
    self.close()
    cleanup_tunnels()

  def create_status_bar(self):
    """
    Status bar placeholder
    """
    self.status_text = QtGui.QLabel("Welcome to the WBDC2 Client")
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

  def set_power_scale(self, *args):
    """
    """
    self.logger.debug("set_power_scale: called with %s", args)
    self.logger.debug("set_power_scale: selection = %s", args[0].text() )
    self.power_scale = args[0].text()
    self.logger.debug("set_power_scale: checked? %s", args[0].isChecked() )
    self.central_frame.RFpower.setText(self.power_scale)

  def timer_action(self, *args):
    self.logger.debug("timer_action: called with %s", args)
    action = args[0].text()
    if action == "Start":
      self.logger.debug("timer_action: %s", action)
      self.timer_loop = 1
      self.timer.singleShot(TIMER_INTERVAL, self.timer_update)
    elif action == "Stop":
      self.logger.debug("timer_action: %s", action)
      self.timer_loop = 0
    else:
      self.logger.debug("timer_action: unknown action %s", action)

  def timer_update(self):
    if self.timer_loop:
      if self.timer_loop  == 1:
        self.refresh_data()
      self.timer_loop += 1
      self.timer.singleShot(TIMER_INTERVAL, self.timer_update)
    else:
      print "Timer stopped"

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
    """
    """
    self.logger.debug("timer_update: called")
    if self.timer_loop:
      self.refresh_data()
      self.central_frame.refresh()
      self.timer_loop += 1
      self.timer.singleShot(1000, self.timer_update)
    else:
      print "Timer stopped"

  def refresh_data(self):
    self.crossSwitch_state = bool(self.wbdc.request(
                                               "self.crossSwitch.get_state()"))
    self.logger.debug("cross switch state is %s", self.crossSwitch_state)

    self.pol_states = self.wbdc.request("self.get_pol_sec_states()")
    self.logger.debug("Pol section states: %s", self.pol_states)

    self.DC_states = self.wbdc.request("self.get_DC_states()")
    self.logger.debug("Down-converter states: %s", self.DC_states)
    
    self.supply_data = self.wbdc.request(
                                     "self.analog_monitor.get_monitor_data(1)")
    self.logger.debug("refresh_data: power supplies: %s", self.supply_data)
    self.pwr_data = self.wbdc.request(
                                     "self.analog_monitor.get_monitor_data(2)")
    self.logger.debug("refresh_data: power and temperature: %s", self.pwr_data)
    for chan in self.power.keys():
      for key in self.pwr_data.keys():
        if key[:4] == chan:
            self.power[chan] = self.pwr_data[key]
    

from optparse import OptionParser
p = OptionParser()
p.set_usage('WBDC2_GUI.py [options]')
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
             logname = logpath+"WBDC2_client.log")

set_loglevel(mylogger, get_loglevel(opts.loglevel))

app = QtGui.QApplication(sys.argv)
app.setStyle("motif")
mylogger.debug(" creating MainWindow")
client = MainWindow()
mylogger.warning("""If the program raises an exception, do
  cleanup_tunnels()
before exiting python.""")

client.show()

sys.exit(app.exec_())
