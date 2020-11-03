# Command line clients for ROACH servers

Repo: `MCClients`

`kurtosis_client.py` provides class `KurtosisClient` which provides a command-line interface to the kurtosis firmware. It implements most if not all the functions in the firmware interface by means of calls to the kurtosis spectrometer server.

`ManagerClient.py` provides class `ManagerClient` which provides a command line interface to a server called `DTO_mgr-dto` which, as far as I know, doesn't exist.  However, the socket port 50015 is now used by the `MonitorControl` central server.

Sub-directory `GUI` has Qt5 clients.

  * `kurtosisGUI.py` has a class the kurtosis firmware, which could be put in its own `QMainWindow` or on a tab of a large application.
  * `managerClientUI.py` is such a client, which provides an interface to the DSN Transient Observatory.
  * `observatoryCtrl.py` ia a version of the K-band observing software used at DSS-43.
  * `ui_kurt_spec.py` has the ugly PyQT5 code produced with Qt Designer.
  * `WBDC2_GUI.py` is an old Qt3 GUI designed for use with an original Pyro server.

Sub-directory `Qt_widgets` has various useful widgets for building monitor and control GUIs.

Sub-directory `SpecCtrl` has a PyQt5 client for the `MonitorControl` central server.