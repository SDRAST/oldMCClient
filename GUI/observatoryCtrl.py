# -*- coding: utf-8 -*-
"""
Monitor and Control Client

Qt5 GUI to provide control for equipment defined in MonitorControl


"""
import logging
import Pyro5.api
import sys
import warnings

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import QObject, pyqtSignal

from MCClient.GUI.roach_control_new import Ui_Observatory

#load spectrometer related libs

logger = logging.getLogger(__name__)

class ObservatoryClient(object):
    """
    Provides action for associated GUI
    
    This has all the code specific to the equipment being monitored.
    """
    def __init__(self):
        """
        """
        logging.getLogger(logger.name+".ObservatoryClient")
        uri = Pyro5.api.URI("PYRO:DSS-43@localhost:50015")
        self.hardware = Pyro5.api.Proxy(uri)

        self.equipment = self.hardware.get_equipment()
    
    def initialize(self):
        """
        """
        temps = self.hardware.hdwr("FrontEnd", "read_temp")
        self.logger.debug("initialize: phys.temps.: %s", temps)
        #self.ui.lcdLoad1.intValue(int(round(temps['load1'])))
        
        pm_readings = self.hardware.get_tsys()
        self.logger.debug("initialize: PM readings: %s", pm_readings)
        for num in [1,2,3,4]:
          self.ui.labelPM[num].setText(QtWidgets.QApplication.translate(
              "Observatory", ("%5.1f" % pm_readings[num-1]), None))
        
        server_time = self.hardware.server_time()
        self.ui.lcd_year.display(int(server_time[:4]))
        self.ui.lcd_doy.display(int(server_time[5:8]))
        self.ui.lcd_time.display(int(server_time[9:11]
                                    +server_time[12:14]
                                    +server_time[15:17]))
                     
    def connect(self):
        """
        Connections to signals/slots for GUI
        """
        self.ui.actionQuit.triggered.connect(self.exit_clean)

    def exit_clean(self):
        """
        Stop all threads and exit cleanly
        """
        self.logger.debug("exit_clean: quitting")
        self.quit()
        

class observatoryGUI(QtWidgets.QMainWindow, ObservatoryClient):
    """
    GUI for controlling krx43, ROACH, and analysis related functions.
    
    Also defines some simple functions and thread controls.
    """
    def __init__(self):
        """
        Initialises GUI parameters
        """
        self.logger = logging.getLogger(logger.name+".observatoryGUI")
        QtWidgets.QMainWindow.__init__(self)
        self.ui = Ui_Observatory()
        self.ui.setupUi(self)
        ObservatoryClient.__init__(self)
        self.initialize()
        self.connect()
        self.setWindowTitle("DSS43 K-Band Observatory")
        self.logger.debug("__init__: QMainWindow initialized")
        self.logger.debug("__init__: Ui_Observatory set up")

        #Main window title
       
#        self.__connect()
#
#    def __connect(self):
#        """
#        Connections to signals/slots for GUImade here along with the timer 
#        definition of 1 sec interval for GUI LCD updates.
#        """
#        self.ui.actionQuit.triggered.connect(self.exit_clean)

    def thread_group_start(self):
        """Thread collection defined in separate file"""
        self.write_dataset  =  write_datasets(self.ui)
        self.write_dataset.start()

    def keyPressEvent(self, e):
        """
        Manage key events
        """
        if e.key() == QtCore.Qt.Key_Escape:
            #self.exit_clean()
            warnings.warn('Escape pressed...no functions defined for escape key.')
            self.logger.info("Escape pressed...no functions defined for escape key.")

    def quit(self):
        """
        invoke close()
        """
        self.logger.info("close: done")
        self.close()
        
if __name__ == "__main__":
  logging.basicConfig(level=logging.DEBUG)
  mylogger =  logging.getLogger()
  mylogger.setLevel(logging.DEBUG)
  mylogger.debug("logger created")
  
  app = QtWidgets.QApplication(sys.argv)
  mylogger.debug("QApplication initialized")
  app.setStyle("Windows")
  
  GUI = observatoryGUI()
  mylogger.debug("observatoryGUI initialized")
  GUI.show()
  sys.exit(app.exec_())
