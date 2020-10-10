import pyaudio
import wave
import pydub
import os
import serial
import serial.tools.list_ports
from ftplib import FTP
from datetime import datetime
import configparser


def findPort(conf):
    ports = serial.tools.list_ports.comports()
    for port in ports:
        if conf['SERIAL']['DEVICE'] in str(port):
            resport = str(port).split(' ')[0]
    return resport


def record(conf):

    p = pyaudio.PyAudio()

    serport = findPort(conf)
    print('found ' + conf['SERIAL']['DEVICE'] + ' on ' + serport)
    sercom = serial.Serial(serport, 115200)

    print("waiting for recording")
    # sercom.write(str.encode(conf['SERIAL']['CHECKBYTE']))
    while True:
        a = sercom.read(2)
        if a == b'10':
            print('channel 1 shorted!')
            break
        elif a == b'01':
            print('channel 2 shorted!')
            break
        pass
    print("Starting recording")
    stream = p.open(format=pyaudio.paInt16,
                    channels=int(conf['AUDIO']['CHANNELS']),
                    rate=int(conf['AUDIO']['RATE']),
                    input=True,
                    frames_per_buffer=int(conf['AUDIO']['CHUNK']))
    main_counter = 0
    ch1 = 0
    ch2 = 0
    rec1 = False
    rec2 = False
    frames_list = []
    dates_list = []
    try:
        while True:
            data = stream.read(int(conf['AUDIO']['CHUNK']))
            if a == b'10':
                if rec1 == False:
                    main_counter += 1
                    ch1 = main_counter
                    print(f'starting recording on channel 1; file {ch1}')
                    frames_list.append([])
                    dates_list.append(datetime.now())
                    rec1 = True
                frames_list[ch1 - 1].append(data)
                rec2 = False
            elif a == b'01':
                if rec2 == False:
                    main_counter += 1
                    ch2 = main_counter
                    print(f'starting recording on channel 2; file {ch2}')
                    frames_list.append([])
                    dates_list.append(datetime.now())
                    rec2 = True
                frames_list[ch2 - 1].append(data)
                rec1 = False
            elif a == b'00':
                if rec1 == False:
                    main_counter += 1
                    ch1 = main_counter
                    print(f'starting recording on channel 1; file {ch1}')
                    frames_list.append([])
                    dates_list.append(datetime.now())
                    rec1 = True
                if rec2 == False:
                    main_counter += 1
                    ch2 = main_counter
                    print(f'starting recording on channel 2; file {ch2}')
                    frames_list.append([])
                    dates_list.append(datetime.now())
                    rec2 = True
                frames_list[ch1 - 1].append(data)
                frames_list[ch2 - 1].append(data)
            else:
                break
            if sercom.inWaiting() != 0:
                a = sercom.read(2)
    except KeyboardInterrupt:
        print("Done recording")
    except Exception as e:
        print(str(e))

    # try:
    #     while True:
    #         data = stream.read(int(conf['AUDIO']['CHUNK']))
    #         frames.append(data)
    # except KeyboardInterrupt:
    #     print("Done recording")
    # except Exception as e:
    #     print(str(e))
    print("Done recording")
    sample_width = p.get_sample_size(pyaudio.paInt16)

    sercom.close()
    stream.stop_stream()
    stream.close()
    p.terminate()
    return sample_width, frames_list, dates_list


def record_to_file(employee_id, conf):
    sample_width, frames_list, time_list = record(conf)
    i = 0
    file_list = []
    for frames in frames_list:
        time = time_list[i].strftime("%Y%m%d-%H%M%S")
        filename = f"{employee_id}-{time}.wav"
        file_list.append(filename)
        wf = wave.open(filename, 'wb')
        wf.setnchannels(int(conf['AUDIO']['CHANNELS']))
        wf.setsampwidth(sample_width)
        wf.setframerate(int(conf['AUDIO']['RATE']))
        wf.writeframes(b''.join(frames))
        wf.close()
        i += 1
    return file_list


def wav_2_mp3_convert(filename):
    sound = pydub.AudioSegment.from_wav(filename)
    sound.export(filename.split(".")[0] + ".mp3", format="mp3")
    os.remove(filename)


def upload_ftp(filename, conf):
    ftp = FTP(conf['FTP']['HOST'])
    ftp.login()
    ftp.cwd(conf['FTP']['DIRECTORY'])
    with open(filename, 'rb') as fobj:
        ftp.storbinary('STOR ' + filename, fobj, 1024)
    ftp.quit()
    os.remove(filename)


if __name__ == '__main__':
    config = configparser.ConfigParser()
    config.read("conf.ini")
    print('#' * 80)
    employee_id = input("Enter your id: ")
    # print("Please speak word(s) into the microphone")
    # print('Press Ctrl+C to stop the recording')
    # employee_id = 1111

    filename_list = record_to_file(employee_id, config)
    for filename in filename_list:
        print("Result written to " + filename)
        wav_2_mp3_convert(filename)
        filename = filename.split(".")[0] + ".mp3"
        print("Converted to " + filename)
        upload_ftp(filename, config)
        print('file sent to ' + config['FTP']
              ['HOST'] + config['FTP']['DIRECTORY'])
    print('#' * 80)
