import csv
from datetime import datetime
import glob
import matplotlib.pyplot as plt
import numpy as np
import statistics
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


def get_duration(array, num_bytes, frequency):
    ammount_bytes = len(array) // num_bytes
    duration = float(ammount_bytes) / frequency
    return duration


def check_minimum_meas_duration(first_array,
                                first_num_bytes,  # num of bytes per package
                                second_array,
                                second_num_bytes,  # num of bytes per package
                                freq1=200,
                                freq2=50,
                                sample_time=10
                                ):
    first_duration = get_duration(first_array, first_num_bytes, freq1)
    second_duration = get_duration(second_array, second_num_bytes, freq2)

    if first_duration < second_duration:
        return first_duration
    return second_duration


def listen_port(sample_time=10, frequency=50):
    """
        Listens to a specified port
        Recieves 3 packets of 4 bits
        Combines them together into single 12 bit digit
    """
    print("Available ports:")
    # print(dict_of_ports)
    print('---------------------------------------')
    print(' Num | Port')
    print('---------------------------------------')
    for key in dict_of_ports:
        print(f'{key: ^5}| {dict_of_ports[key]}')
    print('---------------------------------------')
    try:
        port_number = int(input("Choose the port's number: "))
    except ValueError:
        print("Wrong input. Enter integer.")
        return

    print("Measuring...")
    listen_port_start_time = time.time()

    ser = serial.Serial()
    ser.baudrate = 115200
    ser.parity = serial.PARITY_EVEN
    ser.port = dict_of_ports[port_number]
    # ser.port = '/dev/tty.SLAB_USBtoUART'
    print(ser)
    print()
    ser.open()
    # ser.write(b'1')
    read_bytes = ser.read(5 * 50 * 10 + 3 * 200 * 10)
    # read_bytes = ser.read(5*50)
    # read_bytes = ser.read_until(b'\xFF')
    ser.close()

    print("--- Listening time %.5f seconds ---"
          % (time.time() - listen_port_start_time))

    print(read_bytes)
    ecg_max30105_processing(read_bytes, frequency, sample_time)


def ppg_ecg_processing(read_bytes, frequency, sample_time):
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

    with open(f'{csv_location}/{csv_filename}',
              mode='w',
              newline='') as csv_file:
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


def max30105_processing(read_bytes, frequency, sample_time):
    start_time = time.time()

    max30105_results = [0] * (200)
    max30105_byte_counter = 0

    for byte in read_bytes:
        packet_position = ((byte >> 4) & 0x7)
        packet = (byte & 0xF) << (packet_position * 4)
        max30105_results[max30105_byte_counter // 5] += packet
        max30105_byte_counter += 1

    # for i in range(len(max30105_results) - 1):
    #     max30105_results[i+1] -= max30105_results[i]
    # max30105_results[0] = max30105_results[1]

    for i in range(len(max30105_results)):
        max30105_results[i] = abs(2**18 - max30105_results[i])

    for i in range(2, len(max30105_results) - 2):
        items = [max30105_results[i-2],
                 max30105_results[i-1],
                 max30105_results[i],
                 max30105_results[i+1],
                 max30105_results[i+2]]
        max30105_results[i] = statistics.median(items)

    print("--- Converting time %.5f seconds ---"
          % (time.time() - start_time))
    print(f"MAX30105 results {len(max30105_results)}:")
    print(max30105_results)

    print("Forming array of time counts")
    minimal_length = len(max30105_results)
    if minimal_length > frequency * sample_time:
        minimal_length = frequency * sample_time
    t = [0] * minimal_length
    print(len(t))
    dt = 1 / frequency
    for i in range(len(t)):
        t[i] = round((i * (dt)), 3)

    plt.plot(t, max30105_results[:minimal_length])
    plt.title('PPG MAX30105')
    plt.xlabel('time (s)')
    plt.show()


def ecg_max30105_processing(read_bytes, frequency, sample_time):
    start_time = time.time()

    unprocessed_ecg = []
    unprocessed_ppg = []

    for byte in read_bytes:
        if (byte >> 7):
            unprocessed_ecg.append(byte)
        else:
            unprocessed_ppg.append(byte)

    print(f"Unprocessed ecg length: {len(unprocessed_ecg)}")
    print(f"Unprocessed ppg length: {len(unprocessed_ppg)}")

    min_duration = check_minimum_meas_duration(unprocessed_ecg,
                                               3,
                                               unprocessed_ppg,
                                               5
                                               )

    print(f'Value {min_duration} of {type(min_duration)} type')

    # ecg_size = len(np.arange(0, (min_duration + (1 / 200)), (1 / 200)))

    ecg_size = len(np.arange(0, min_duration, (1 / 200)))
    # min_duration can be float type. np.full() only accepts int
    ecg_results = np.full(ecg_size, 0)
    # ecg_results = [0] * (int(min_duration * 200))
    ecg_byte_counter = 0
    # for byte in unprocessed_ecg[:int(min_duration * 3 * 200)]:
    for byte in unprocessed_ecg[:(ecg_size * 3)]:
        packet_position = 3 - ((byte >> 4) & 0x3)
        packet = (byte & 0xF) << (packet_position * 4)
        ecg_results[ecg_byte_counter // 3] += packet
        ecg_byte_counter += 1
        if ecg_byte_counter // 3 == min_duration * 200:
            break

    # max30105_size = len(np.arange(0, (min_duration + (1 / 50)), (1 / 50)))
    max30105_size = len(np.arange(0, min_duration, (1 / 50)))
    max30105_results = np.full(max30105_size, 0)
    # max30105_results = [0] * (int(min_duration * 50))
    max30105_byte_counter = 0

    # for byte in unprocessed_ppg[:int(min_duration * 5 * 50)]:
    for byte in unprocessed_ppg[:(max30105_size * 5)]:
        packet_position = ((byte >> 4) & 0x7)
        packet = (byte & 0xF) << (packet_position * 4)
        max30105_results[max30105_byte_counter // 5] += packet
        max30105_byte_counter += 1
        if max30105_byte_counter // 5 == min_duration * 50:
            break

    # for i in range(len(max30105_results) - 1):
    #     max30105_results[i+1] -= max30105_results[i]
    # max30105_results[0] = max30105_results[1]

    # for i in range(len(max30105_results)):
    #     max30105_results[i] = abs(2**18 - max30105_results[i])

    max30105_results = np.power(2, 18) - max30105_results

    for i in range(2, len(max30105_results) - 2):
        items = [max30105_results[i-2],
                 max30105_results[i-1],
                 max30105_results[i],
                 max30105_results[i+1],
                 max30105_results[i+2]]
        max30105_results[i] = statistics.median(items)

    print("--- Converting time %.5f seconds ---"
          % (time.time() - start_time))

    print(f"MAX30105 results {len(max30105_results)}:")
    print(max30105_results)

    print(f'ECG results {len(ecg_results)}')
    print(ecg_results)

    print("Forming array of time counts")
    # minimal_length = len(max30105_results)
    # if minimal_length > frequency * sample_time:
    #     minimal_length = frequency * sample_time

    # t = [0] * int(min_duration * 50)
    # np
    # print(len(t))
    # dt = 1 / 50
    # for i in range(len(t)):
    #     t[i] = round((i * (dt)), 3)

    print('--- t_ppg time ---')
    t_ppg_time = time.time()
    # t_ppg = np.arange(0, (min_duration + (1 / 50)), (1 / 50))
    t_ppg = np.arange(0, min_duration, (1 / 50))
    t_ppg = np.round(t_ppg, 3)
    print(len(t_ppg))
    print(t_ppg)
    print("--- t_ppg forming time %.5f seconds ---"
          % (time.time() - t_ppg_time))

    # t1_time = time.time()
    # t1 = [0] * int(min_duration * 200)
    # print(len(t1))
    # dt1 = 1 / 200
    # for i in range(len(t1)):
    #     t1[i] = round((i * (dt1)), 3)
    # print(t1)
    # print("--- t1 forming time %.5f seconds ---"
    #       % (time.time() - t1_time))

    print('--- t_ecg time ---')
    t_ecg_time = time.time()
    # t_ecg = np.arange(0, (min_duration + (1 / 200)), (1 / 200))
    t_ecg = np.arange(0, min_duration, (1 / 200))
    t_ecg = np.round(t_ecg, 3)
    print(len(t_ecg))
    print(t_ecg)
    print("--- t_ecg forming time %.5f seconds ---"
          % (time.time() - t_ecg_time))

    # print(f't1 has {len(t1): >6} elements\nt2 has {len(t2): >6} elements')

    plt.subplot(2, 1, 1)
    plt.plot(t_ppg, max30105_results)
    plt.title('PPG MAX30105')
    plt.xlabel('time (s)')
    plt.grid(True)

    plt.subplot(2, 1, 2)
    plt.plot(t_ecg, ecg_results)
    plt.title('ECG')
    plt.xlabel('time (s)')
    plt.grid(True)

    plt.show()


if __name__ == '__main__':
    start_time = time.time()
    print(serial_ports())
    print("--- Total checking time %.5f seconds ---"
          % (time.time() - start_time))
    print()
    start_time = time.time()
    listen_port()
    # print("--- Total listening time %.5f seconds ---"
    #   % (time.time() - start_time))
