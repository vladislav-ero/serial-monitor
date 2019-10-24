import glob
import serial
import sys
import time

dict_of_ports = {}


def serial_ports():
    """ Lists serial port names

        :raises EnvironmentError:
            On unsupported or unknown platforms
        :returns:
            A list of the serial ports available on the system
    """
    start_time = time.time()

    if sys.platform.startswith('win'):
        ports = ['COM%s' % (i + 1) for i in range(256)]
    elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
        # this excludes your current terminal "/dev/tty"
        ports = glob.glob('/dev/tty[A-Za-z]*')
    elif sys.platform.startswith('darwin'):
        ports = glob.glob('/dev/tty.*')
    else:
        raise EnvironmentError('Unsupported platform')

    print("--- Checked system in %.5f seconds ---"
          % (time.time() - start_time))

    result = []
    port_counter = 1
    for port in ports:
        start_check_time = time.time()
        try:
            ser = serial.Serial(port)
            ser.close()
            result.append(port)
            dict_of_ports[port_counter] = port
            port_counter += 1
        except (OSError, serial.SerialException):
            pass
        print("--- Checked port %s in %.5f seconds ---" %
              (str(port), (time.time() - start_check_time)))
    return result


def listen_port():
    """ Listens to a specified port
    """
    print("Available ports:")
    print(dict_of_ports)
    try:
        port_number = int(input("Choose the port's number: "))
    except ValueError:
        print("Wrong input. Enter integer.")
        return

    start_time = time.time()

    ser = serial.Serial()
    ser.baudrate = 115200
    ser.parity = serial.PARITY_EVEN
    ser.port = dict_of_ports[port_number]
    ser.open()
    ser.close()

    print("--- Listening time %.5f seconds ---"
          % (time.time() - start_time))


if __name__ == '__main__':
    start_time = time.time()
    print(serial_ports())
    print("--- Total checking time %.5f seconds ---"
          % (time.time() - start_time))
    listen_port()
