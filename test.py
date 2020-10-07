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
    print('found '+ conf['SERIAL']['DEVICE'] +' on ' + serport)
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
        # sercom.write(str.encode(conf['SERIAL']['CHECKBYTE']))
    print("Starting recording")
    stream = p.open(format=pyaudio.paInt16,
                    channels=int(conf['AUDIO']['CHANNELS']),
                    rate=int(conf['AUDIO']['RATE']),
                    input=True,
                    frames_per_buffer=int(conf['AUDIO']['CHUNK']))

    frames = []

    try:
        while 1:
            data = stream.read(int(conf['AUDIO']['CHUNK']))
            frames.append(data)
            if sercom.inWaiting() != 0:
                # print('in first if')
                if sercom.read(2) == b'11':
                    # print('i want to break free')
                    break
            # sercom.write(str.encode(conf['SERIAL']['CHECKBYTE']))
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
    return sample_width, frames


def record_to_file(conf, file_path):
    wf = wave.open(file_path, 'wb')
    wf.setnchannels(int(conf['AUDIO']['CHANNELS']))
    sample_width, frames = record(conf)
    wf.setsampwidth(sample_width)
    wf.setframerate(int(conf['AUDIO']['RATE']))
    wf.writeframes(b''.join(frames))
    wf.close()


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
    filename = str(employee_id) + "-" + \
        datetime.now().strftime("%H%M%S-%Y%m%d") + ".wav"
    record_to_file(config, filename)
    print("Result written to " + filename)
    wav_2_mp3_convert(filename)
    filename = filename.split(".")[0] + ".mp3"
    print("Converted to " + filename)
    upload_ftp(filename, config)
    print('file sent to ' + config['FTP']['HOST'] + config['FTP']['DIRECTORY'])
    print('#' * 80)
