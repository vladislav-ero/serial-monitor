import glob
import serial
import sys
import time


def serial_ports():
    start_time = time.time()
    """ Lists serial port names

        :raises EnvironmentError:
            On unsupported or unknown platforms
        :returns:
            A list of the serial ports available on the system
    """

    if sys.platform.startswith('win'):
        ports = ['COM%s' % (i + 1) for i in range(256)]
    elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
        # this excludes your current terminal "/dev/tty"
        ports = glob.glob('/dev/tty[A-Za-z]*')
    elif sys.platform.startswith('darwin'):
        ports = glob.glob('/dev/tty.*')
    else:
        raise EnvironmentError('Unsupported platform')

    print("--- Checked system %.5f seconds ---" % (time.time() - start_time))

    result = []
    for port in ports:
        start_check_time = time.time()
        try:
            s = serial.Serial(port)
            s.close()
            result.append(port)
        except (OSError, serial.SerialException):
            pass
        print("--- Checked port %s %.1f seconds ---" %
              (str(port), (time.time() - start_check_time)))
    return result


if __name__ == '__main__':
    start_time = time.time()
    print(serial_ports())
    print("--- Total time %.5f seconds ---" % (time.time() - start_time))
