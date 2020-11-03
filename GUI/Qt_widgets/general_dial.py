from PyQt5 import QtCore, QtGui, QtWidgets

class GeneralDial(QtWidgets.QDial):
  """
  Dial with floating point values
  """
  def __init__(self,limits,format,valueToInt,intToValue):
    """
    QDial re-implemented with floating point value

    Notes
    =====

    Notch positions
    ---------------
    I haven't figured out a way for the large notch ticks to align with
    major notch numbers, like -10,-5,0,5,10... if the lowest number is
    not a major one, e.g., is -11.5 instead -10.

    @param limits : (minimum value, maximum value)
    @type  limits : tuple of float

    @param format : format for dial labels, like "%6.1f"
    @type  format : str

    @param valueToInt : function to convert values to int dial setting
    @type  valueToInt : int public method with one argument

    @param intToValue : function to convert int dial setting to value
    @type  intToValue : float public method with one argument
    """
    super(GeneralDial,self).__init__()
    self.valueToInt = valueToInt
    self.intToValue = intToValue
    minimum = self.valueToInt(limits[0])
    maximum = self.valueToInt(limits[1])
    self.setRange(minimum,maximum)

  @staticmethod
  def valueFromText(text):
    """
    Floating point gain text to dial integer value
    """
    try:
      value = float(text)
    except ValueError:
      value = 0.
    return valueToInt(value)

  @staticmethod
  def textFromValue(value):
    """
    Label text from dial integer value
    """
    num = intToValue(value)
    return ("%6.1f" % num)

  def setRealValue(self,value):
    """
    """
    self.setValue(self.valueToInt(value))
