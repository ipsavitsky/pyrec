import serial
import serial.tools.list_ports

def findPort():
    ports = serial.tools.list_ports.comports()
    for port in ports:
        if 'STM32 Virtual ComPort' in str(port):
            resport = str(port).split(' ')[0]
    return resport


serport = findPort()
print('found on ' + serport)
sercom = serial.Serial(serport, 115200)
while True:
    a = sercom.read(2)   
    print(a)