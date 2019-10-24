import glob
import sys
import time

import serial

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


def listen_port(array_size=50):
    """
        Listens to a specified port
        Recieves 3 packets of 4 bits
        Combines them together into single 12 bit digit
    """
    print("Available ports:")
    print(dict_of_ports)
    # try:
    #     port_number = int(input("Choose the port's number: "))
    # except ValueError:
    #     print("Wrong input. Enter integer.")
    #     return

    listen_port_start_time = time.time()

    ser = serial.Serial()
    ser.baudrate = 115200
    ser.parity = serial.PARITY_EVEN
    # ser.port = dict_of_ports[port_number]
    ser.port = '/dev/tty.SLAB_USBtoUART'
    ser.open()
    read_bytes = ser.read(3 * array_size)
    ser.close()

    print("--- Listening time %.5f seconds ---"
          % (time.time() - listen_port_start_time))

    print(read_bytes)

    start_time = time.time()
    adc_results = [0] * array_size
    byte_counter = 0
    for byte in read_bytes:
        print('0x%x' % int(bin(byte), 2))
        packet_position = 2 - (byte_counter - ((byte_counter // 3) * 3))
        packet = (int(bin(byte), 2) & 0xF) << (packet_position * 4)
        adc_results[byte_counter // 3] += packet
        byte_counter += 1
    # print(bin(ord(read_bytes)))
    print("--- Converting time %.5f seconds ---"
          % (time.time() - start_time))
    print("ADC results:")
    print(adc_results)


if __name__ == '__main__':
    start_time = time.time()
    print(serial_ports())
    print("--- Total checking time %.5f seconds ---"
          % (time.time() - start_time))
    listen_port()
