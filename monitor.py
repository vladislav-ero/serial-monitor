import csv
from datetime import datetime
import glob
import matplotlib.pyplot as plt
import numpy as np
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


def listen_port(sample_time=5):
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

    print("Measuring...")
    frequency = 200
    listen_port_start_time = time.time()

    ser = serial.Serial()
    ser.baudrate = 115200
    ser.parity = serial.PARITY_EVEN
    # ser.port = dict_of_ports[port_number]
    ser.port = '/dev/tty.SLAB_USBtoUART'
    print(ser)
    ser.open()
    # ser.write(b'1')
    read_bytes = ser.read(3 * 2 * frequency * sample_time)
    # read_bytes = ser.read(5*50)
    # read_bytes = ser.read_until(b'\xFF')
    ser.close()

    print("--- Listening time %.5f seconds ---"
          % (time.time() - listen_port_start_time))

    print(read_bytes)

    unprocessed_ecg = []
    unprocessed_ppg = []

    for byte in read_bytes:
        if ((byte >> 6) & 0x3 == 0):
            unprocessed_ecg.append(byte)
        elif ((byte >> 6) & 0x3 == 1):
            unprocessed_ppg.append(byte)

    print(f"Unprocessed ecg has {len(unprocessed_ecg)} samples")
    print(f"Unprocessed ppg has {len(unprocessed_ppg)} samples")

    start_time = time.time()

    ecg_results = [0] * ((len(unprocessed_ecg) // 3) + 1)
    ecg_byte_counter = 0
    for byte in unprocessed_ecg:
        packet_position = 3 - ((byte >> 4) & 0x3)
        packet = (byte & 0xF) << (packet_position * 4)
        ecg_results[ecg_byte_counter // 3] += packet
        ecg_byte_counter += 1

    ppg_results = [0] * ((len(unprocessed_ppg) // 3) + 1)
    ppg_byte_counter = 0
    for byte in unprocessed_ppg:
        packet_position = 3 - ((byte >> 4) & 0x3)
        packet = (byte & 0xF) << (packet_position * 4)
        ppg_results[ppg_byte_counter // 3] += packet
        ppg_byte_counter += 1

    # ecg_results.pop()
    # ppg_results =[]
    # ppg_byte_counter

    print("--- Converting time %.5f seconds ---"
          % (time.time() - start_time))

    print(f"ECG results {len(ecg_results)}:")
    print(ecg_results)

    print(f"PPG results {len(ppg_results)}:")
    print(ppg_results)
    print("--- Converting time %.5f seconds ---"
          % (time.time() - start_time))

    print("Forming array of time counts")
    if (len(ecg_results) <= len(ppg_results)):
        minimal_length = len(ecg_results)
    else:
        minimal_length = len(ppg_results)
    if minimal_length > frequency * sample_time:
        minimal_length = frequency * sample_time
    t = [0] * minimal_length
    print(len(t))
    dt = 1 / 200
    for i in range(len(t)):
        t[i] = round((i * (dt)), 3)

    csv_filename = datetime.now().strftime("%d_%m_%Y_%H_%M_%S") + '.csv'
    csv_location = 'measurements'

    with open(f'{csv_location}/{csv_filename}', mode='w') as csv_file:
        fieldnames = ['Time', 'ECG', 'PPG']
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)

        writer.writeheader()
        for i in range(len(t)):
            writer.writerow({'Time': t[i],
                             'ECG': ecg_results[i],
                             'PPG': ppg_results[i]
                             })
    print(f"Output: '{csv_filename}'")

    print(f"Time: {len(t)}")
    print(f"ECG: {len(ecg_results[:minimal_length])}")
    print(f"PPG: {len(ppg_results[:minimal_length])}")

    plt.subplot(2, 1, 1)
    plt.plot(t, ecg_results[:minimal_length])
    plt.title('ECG')
    plt.xlabel('time (s)')
    # plt.ylabel('Damped oscillation')

    plt.subplot(2, 1, 2)
    plt.plot(t, ppg_results[:minimal_length])
    plt.title('PPG')
    plt.xlabel('time (s)')
    # plt.ylabel('Undamped')

    plt.show()


if __name__ == '__main__':
    start_time = time.time()
    print(serial_ports())
    print("--- Total checking time %.5f seconds ---"
          % (time.time() - start_time))
    start_time = time.time()
    listen_port()
    print("--- Total listening time %.5f seconds ---"
          % (time.time() - start_time))
