# Monitor
<hr/>

### Contents
1. [Install](#install)
2. [Script](#script)
	* [Webcam](#webcam-script)
	* [RAD7](#rad7-script)
	* [UA10](#ua10-script)
	* [UA58](#ua58-script)
	* [RS9A](#rs9a-script)
	* [DSM101](#dsm101-script)
	* [APEXP3](#apexp3-script)
3. [Supervisor](#supervisor)
	* [Webcam](#webcam-supervisor)
	* [RAD7](#rad7-supervisor)
	* [UA10](#ua10-supervisor)
	* [UA58](#ua58-supervisor)
	* [RS9A](#rs9a-supervisor)
	* [DSM101](#dsm101-supervisor)
	* [APEXP3](#apexp3-supervisor)
4. [ETC](#etc)

<hr/>

## Install
* Install supervisor
	* `sudo apt install supervisor`
	* modify `/etc/supervisor/supervisord.conf`
		* [supervisord] logfile : location &rarr; /opt/monitor/log
		* [supervisord] childlogdir : location &rarr; /opt/monitor/log
		* [include] files : location &rarr; /opt/monitor/supervisor
* All supervisor config files will be located in 
	* `/opt/monitor/supervisor/available`
	* and make a link to `/opt/monitor/supervisor/`

* Run supervisor
	* `sudo systemctl start supervisor`
	* `sudo systemctl enable supervisor`

### Webcam
* Install webcam related libraries

```
sudo apt install cmake libhdf5-dev libhdf5-103 \
libgtk2.0-dev libgtk-3-dev \
gfortran libavformat-dev \
libxvidcore-dev libx264-dev libv4l-dev \
libtiff5-dev libswscale-dev libatlas-base-dev \
libjasper-dev libgdk-pixbuf2.0-dev
```
`pip install picamera[array] imutils`

* Currently (2023.02.04), V4.6.0.66 can be installed

`pip install opencv-python==4.6.0.66`

### Module-communication
* Install py-serial
	* `pip install pyserial`

### APEX P3
* Install pyModbusTCP (APEXP3)
	* `pip install pyModbusTCP`
* Need wired connection using cross-cable
	* Settings for simultaneous use of wired and wireless Internet
	* Modify `/etc/dhcpcd.conf` and insert following lines
		* Wireless : 192.168.1.XXX
		* Wired    : 192.168.2.XXX

```
interface eth0
static ip_address=192.168.2.2/24
nogateway
```

## Script
### Webcam-script
* `webcam.py`

```python
#!/opt/monitor/venv/bin/python

from datetime import datetime
import time
import cv2
import numpy as np
import sys
import logging
import os
from pathlib import Path

logging.basicConfig(stream=sys.stdout, format='%(asctime)s %(levelname)-8s %(message)s', level=logging.INFO)

minutes=1
wait=minutes*60
outputdir = '/opt/monitor/out'
def main():
    while True:
        try:
            cap = cv2.VideoCapture(0)
            cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M','J','P','G'))
            cap.set(cv2.CAP_PROP_FRAME_WIDTH,  1920)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)

            ret, image = cap.read()
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
            now = datetime.now()
            current_time = now.strftime("%Y-%m-%d %H:%M")

            output = 'webcam.png'
            outfile = Path(outputdir) / output
            cv2.imwrite(f'{outfile}', image)
            cap.release()

            logging.info("Save {} : {}".format(output, current_time))

            # copy to YemilabMonitor
            os.popen("scp {} ymmon:/monitor/www/html/webcam2/".format(outfile))
            time.sleep(wait)
        except KeyboardInterrupt:
            logging.info('Good bye')
            break
        except:
            logging.exception('Exception')
            time.sleep(wait)

if __name__ == '__main__':
    main()
```

### RAD7-script
* `rad7-serial.py`

```python
#!/opt/monitor/venv/bin/python

import os
import sys
import time
import re
import logging
from pathlib import Path
import json
import serial

logging.basicConfig(stream=sys.stdout, format='%(asctime)s %(levelname)-8s %(message)s', level=logging.DEBUG)

SLOWDIR = '/opt/monitor'
BUFSIZE =102400

def read_until_prompt(ser):
    data = bytearray(BUFSIZE)
    for i in range(BUFSIZE):
        b = ser.read()
        if len(b) > 0:
            data[i] = b[0]
            if i >= 2:
                if data[i-2:i+1] == b'\r\n>':
                    logging.debug('Prompt line founded')
                    break
        else:
            logging.debug('Read timeout or no data')
            break
    return data.decode('ascii')

def test_start(ser):
    logging.info('Send ETX')
    ser.write(b'\x03\r\n')
    res = read_until_prompt(ser)
    ser.write(b'\x03\r\n')
    res = read_until_prompt(ser)
    
    logging.info('Send Test Start')
    ser.write(b'Test Start\r\n')
    buf = ser.read(BUFSIZE)
    if len(buf) > 0:
        logging.info(buf.decode('ascii'))
    else:
        logging.error('No data')

def test_status(ser):
    logging.info('Send ETX')
    ser.write(b'\x03\r\n')
    res = read_until_prompt(ser)
    ser.write(b'\x03\r\n')
    res = read_until_prompt(ser)
    
    logging.info('Send Test Status')
    ser.write(b'Test Status\r\n')
    buf  = ser.read(BUFSIZE)
    if len(buf) > 0:
        logging.info(buf.decode('ascii'))
    else:
        logging.error('No data')
        
    obuf = buf.decode('ascii')
    line = obuf.split('\r\n')
    text = line[2].split()
    status = text[1]

    return status
    
def test_clear(ser):
    logging.info('Send ETX')
    ser.write(b'\x03\r\n')
    res = read_until_prompt(ser)
    ser.write(b'\x03\r\n')
    res = read_until_prompt(ser)
    
    logging.info('Send Test Clear')
    ser.write(b'Test Clear')
    logging.info('Send Yes')
    ser.write(b'Yes\r\n')
    buf = ser.read(BUFSIZE)
    if len(buf) > 0:
        logging.info(buf.decode('ascii'))
    else:
        logging.error('No data')

def data_erase(ser):
    logging.info('Send ETX')
    ser.write(b'\x03\r\n')
    res = read_until_prompt(ser)
    ser.write(b'\x03\r\n')
    res = read_until_prompt(ser)
    
    logging.info('Send Data Erase')
    ser.write(b'Data Erase')
    logging.info('Send Yes')
    ser.write(b'Yes\r\n')
    buf = ser.read(BUFSIZE)
    if len(buf) > 0:
        logging.info(buf.decode('ascii'))
    else:
        logging.error('No data')
        
def test_stop(ser):
    logging.info('Send ETX')
    ser.write(b'\x03\r\n')
    res = read_until_prompt(ser)
    ser.write(b'\x03\r\n')
    res = read_until_prompt(ser)
    
    logging.info('Send Test Stop')
    ser.write(b'Test Stop\r\n')
    buf = ser.read(BUFSIZE)
    if len(buf) > 0:
        logging.info(buf.decode('ascii'))
    else:
        logging.error('No data')

def parse_runnum(data):
    runnum = None
    for line in data.split('\r\n'):
        m = re.search('^([0-9]+)', line)
        if m is not None:
            runnum = int(m.group(1).strip()[:2])
    return runnum

def parse_data(data):

    dlst = list()
    v = data.split('\r\n')
    if(v[2] == "No tests stored."):
        raise NameError('Wait')
    
    for line in data.split('\r\n'):
        d = [ l.strip() for l in line.split(',') ]
        if d[0].isdigit():
            dlst.append(d)
    ret = list()
    for d in dlst:
        if d == dlst[-1]:
            try:
                t = time.strptime(' '.join(d[1:6]), '%y %m %d %H %M')
                tstamp = int(time.mktime(t))
                output = {
                    'time': tstamp,
                    'recnum': int(d[0]),
                    'totc': float(d[6]),
                    'livet': float(d[7]),
                    'totcA': float(d[8]),
                    'totcB': float(d[9]),
                    'totcC': float(d[10]),
                    'totcD': float(d[11]),
                    'hvlvl': float(d[12]),
                    'hvcycle': float(d[13]),
                    'temp': float(d[14]),
                    'hum': float(d[15]),
                    'leaki': float(d[16]),
                    'batv': float(d[17]),
                    'pumpi': float(d[18]),
                    'flag': int(d[19]),
                    'radon': float(d[20]),
                    'radon_uncert': float(d[21]),
                    'unit': int(d[22]),
                }
                ret.append((tstamp, output))
                logging.debug((tstamp, output))
                
            except IndexError:
                logging.exception('Line parsing failed')
                continue
            
    return ret

def fetch(dev):
    with serial.Serial(dev, baudrate=9600, bytesize=8, parity='N', stopbits=1, timeout=30) as ser:
        logging.info('Send ETX')
        ser.write(b'\x03\r\n')
        res = read_until_prompt(ser)
        ser.write(b'\x03\r\n')
        res = read_until_prompt(ser)

        logging.info('Send ETX')
        ser.write(b'\x03\r\n')
        res = read_until_prompt(ser)
        ser.write(b'\x03\r\n')
        res = read_until_prompt(ser)
        logging.info('Send Special Status')
        ser.write(b'Special Status\r\n')
        res = read_until_prompt(ser)
        runnum = parse_runnum(res)
        logging.debug(f'Run number is {runnum}')

        logging.info(f'Send Data Com {runnum:02d}')
        ser.write(f'Data Com {runnum:2d}\r\n'.encode('ascii'))
        res = read_until_prompt(ser)
        logging.info('Parse data')
        ret = parse_data(res)
        val = ret[-1][1]['recnum']
        # check recnum > 997 => run stop, clear
        if(val > 997):
            test_stop(ser)
            test_clear(ser)
            data_erase(ser)
            test_start(ser)
        
        return ret

def main():

    dev = os.getenv('DEVICE', None)
    tag = os.getenv('DEVICE_TAG', '')
    sn = os.getenv('DEVICE_SN', '')
    #dev = "/dev/serial/by-id/usb-FTDI_FT232R_USB_UART_AL05NRVP-if00-port0"
    #tag = "test"
    #sn = "4331"

    if len(tag) == 0 or len(sn) == 0:
        logging.error('No tag or sn error! Stop program.')
        sys.exit(1)
    logging.info('Start loop')

    # Check run Idle / Live ?
    with serial.Serial(dev, baudrate=9600, bytesize=8, parity='N', stopbits=1, timeout=30) as ser:
        rst = test_status(ser)
        print(rst)
        if(rst == "Idle"):
            test_start(ser)
        
    while True:
        try:
            ret = fetch(dev)
            data = list()
            for tstamp, d in ret:
                data.append({
                    'name': 'rad7',
                    'dev': sn,
                    'pos': tag,
                    'time': tstamp,
                    **d,
                })

            p = Path(SLOWDIR) / 'data' / f'rad7-serial_{tag}_{sn}.dat'
            with p.open('w') as f:
                f.write(json.dumps(data)+'\n')
                f.flush()

            cmd = f'scp {p} ymmon:/monitor/raw/'
            os.popen(cmd)
            time.sleep(7200)
        except ValueError:
            logging.exception('Parsing failed. Retry after 10 secs...')
            time.sleep(10)
        except NameError:
            logging.exception('Exception: Wait')
            time.sleep(600)
            
        except KeyboardInterrupt:
            logging.info('Good bye')
            break
        except:
            logging.exception('Exception: ')
            time.sleep(600)

if __name__ == '__main__':
    main()
```

### Radionode
* UA10 : Humidity / Temperature
* UA58 : Airborne Chemical (O<sub>2</sub>, CO<sub>2</sub>, CO, H<sub>2</sub>S)

#### UA10-script
* `UA10.py`

```python
#!/opt/monitor/venv/bin/python
import sys
import time
import logging
from pathlib import Path
import json
import serial
import os

logging.basicConfig(stream=sys.stdout, format="%(asctime)s %(levelname)-8s %(message)s", level=logging.DEBUG)

SLOWDIR = '/opt/monitor'

def read(devinfo):

    datapoint = {}
    with serial.Serial(devinfo['dev'], 19200, timeout=1) as ser:
        ser.write(b'ATCD\r\n')
        line1 = ser.readline()
        ser.write(b'ATCMODEL\r\n')
        line2 = ser.readline()
        
    line1 = line1.decode('utf-8').strip()
    line2 = line2.decode('utf-8').strip()
    logging.debug(f'RESPONSE: {line1} {line2}')
    
    cmd, result = line1.split(' ')
    cmd, sn     = line2.split(' ')
    temp, hum   = result.split(',')

    datapoint = {
        'name'  : 'temphum',
        'dev'   : sn,
        'model' : devinfo['model'],
        'time'  : int(time.time()),
        'temp'  : float(temp),
        'hum'   : float(hum),
        'pos'   : devinfo['pos']
    } 
    return datapoint

def main():
 
    model = os.getenv('DEVICE_MD',  '')
    dev   = os.getenv('DEVICE_USB', '')
    pos   = os.getenv('DEVICE_POS', '')

    devinfo = {
        'model' : model,
        'dev'   : dev,
        'pos'   : pos
    }
    
    while True:
        data = []
        try:
            datapoint = read(devinfo)
            dev       = datapoint['dev']
            data.append(datapoint)
        except:
            logging.exception('Exception: ')

        logging.debug(data)
        try:
            p = Path(SLOWDIR) / 'data' / f'{model}_{pos}_{dev}.dat'
            with p.open('w') as f:
                for d in data:
                    f.write(json.dumps(d)+'\n')
            
            cmd = f'scp {p} ymmon:/monitor/raw/'
            os.popen(cmd)
            time.sleep(60)
            
        except KeyboardInterrupt:
            logging.info('Good bye!')
            break
        
        except:
            logging.exception('Exception: ')
            time.sleep(60)

if __name__ == '__main__':
    main()
```

#### UA58-script
* `UA58.py`

```python
#!/opt/monitor/venv/bin/python
import sys
import time
import logging
from pathlib import Path
import json
import serial
import os

logging.basicConfig(stream=sys.stdout, format="%(asctime)s %(levelname)-8s %(message)s", level=logging.DEBUG)

SLOWDIR = '/opt/monitor'

def read(devinfo):

    datapoint = {}
    with serial.Serial(devinfo['dev'], 19200, timeout=1) as ser:
        ser.write(b'ATCQ\r\n')
        line1 = ser.readline()
        ser.write(b'ATCMODEL\r\n')
        line2 = ser.readline()
        
    line1 = line1.decode('utf-8').strip()
    line2 = line2.decode('utf-8').strip()
    logging.debug(f'RESPONSE: {line1} {line2}')
    
    cmd, result      = line1.split(' ')
    cmd, sn          = line2.split(' ')
    co, o2, h2s, co2 = result.split(',')

    datapoint = {
        'name'  : 'Gas Sensor',
        'dev'   : sn,
        'model' : devinfo['model'],
        'time'  : int(time.time()),
        'co'    : float(co),
        'o2'    : float(o2),
        'h2s'   : float(h2s),
        'co2'   : float(co2),
        'pos'   : devinfo['pos']
    }
    return datapoint

def main():

    model = os.getenv('DEVICE_MD',  '')
    dev   = os.getenv('DEVICE_USB', '')
    pos   = os.getenv('DEVICE_POS', '')

    devinfo = {
        'model' : model,
        'dev'   : dev,
        'pos'   : pos
    }
    
    while True:
        data = []
        try:
            datapoint = read(devinfo)
            dev       = datapoint['dev']
            data.append(datapoint)
        except:
                logging.exception('Exception: ')
                
        logging.debug(data)
        try:
            p = Path(SLOWDIR) / 'data' / f'{model}_{pos}_{dev}.dat'
            with p.open('w') as f:
                for d in data:
                    f.write(json.dumps(d)+'\n')

            cmd = f'scp {p} ymmon:/monitor/raw/'
            os.popen(cmd)
            time.sleep(60)

        except KeyboardInterrupt:
            logging.info('Good bye!')
            break
        except:
            logging.exception('Exception: ')
            time.sleep(60)

if __name__ == '__main__':
    main()
```

### FTLab
* RS9A : Radon
* DSM101 : Dust

#### RS9A-script
* `RS9A.py`

```python
#!/opt/monitor/venv/bin/python
import sys
import time
import logging
from pathlib import Path
import json
import serial
import os

logging.basicConfig(stream=sys.stdout, format="%(asctime)s %(levelname)-8s %(message)s", level=logging.DEBUG)

SLOWDIR = '/opt/monitor'

def read(devinfo):

    datapoint = {}
    with serial.Serial(devinfo['dev'], 19200, timeout=1) as ser:
        ser.write(b'VALUE?\r\n')
        line1 = ser.readline()
        ser.write(b'SERIALNO?\r\n')
        line2 = ser.readline()

    line1 = line1.decode('utf-8').strip()
    line2 = line2.decode('utf-8').strip()
    logging.debug(f'RESPONSE: {line1} {line2}')

    val     = line1.split(' ')
    tmp, sn = line2.split(' ')
    st, tmp = val[1].split(':')
    rn, tmp = val[2].split(':')
    unit    = val[5]

    if st != "NORMAL":
        raise NameError('Wait')
    
    if unit == "0":
        with serial.Serial(dev_usb, 19200, timeout=5) as ser:
            ser.write(b'UNIT 1\r\n')
            tmp = ser.readline()
            time.sleep(1)
            ser.write(b'VALUE?\r\n')
            line1 = ser.readline()   # read a '\n' terminated line
        line1 = line1.decode('utf-8').strip()

        val     = line1.split(' ')
        rn, tmp = val[2].split(':')

    datapoint = {
        'name'  : 'Radon Sensor',
        'dev'   : sn,
        'model' : devinfo['model'],
        'time'  : int(time.time()),
        'Rn'    : int(rn),
        'pos'   : devinfo['pos']
    }
    return datapoint
        
def main():

    model = os.getenv('DEVICE_MD',  '')
    dev   = os.getenv('DEVICE_USB', '')
    pos   = os.getenv('DEVICE_POS', '')

    devinfo = {
        'model' : model,
        'dev'   : dev,
        'pos'   : pos
    }

    while True:
        data = []
        try:
            datapoint = read(devinfo)
            dev       = datapoint['dev']
            data.append(datapoint)
        except:
            logging.exception('Exception: ')

        logging.debug(data)
        try:
            p = Path(SLOWDIR) / 'data' / f'{model}_{pos}_{dev}.dat'
            with p.open('w') as f:
                for d in data:
                    f.write(json.dumps(d)+'\n')

            cmd = f'scp {p} ymmon:/monitor/raw/'
            os.popen(cmd)
            time.sleep(3600)

        except KeyboardInterrupt:
            logging.info('Good bye!')
            break
            
        except NameError:
            logging.exception('Exception: Wait')
            time.sleep(600)
            
        except:
            logging.exception('Exception: ')
            time.sleep(600)
        
if __name__ == '__main__':
    main()
```

#### DSM101-script
* `DSM101.py`

```python
#!/opt/monitor/venv/bin/python
import sys
import time
import logging
from pathlib import Path
import json
import serial
import os

logging.basicConfig(stream=sys.stdout, format="%(asctime)s %(levelname)-8s %(message)s", level=logging.DEBUG)

SLOWDIR = '/opt/monitor'

def read(devinfo):

    w_basic_info  = b'\x02\x12\x00\x00\xED\r\n'
    w_value_query = b'\x02\x10\x00\x00\xEF\r\n'
    datapoint = {}
    
    with serial.Serial(devinfo['dev'], 19200, timeout=1) as ser:
        ser.write(w_basic_info)
        # Read
        # STX(1), CMD(1), Size(2; lsb, msb), Data(23), Chksum(1)
        line = ser.readline()
        stx    = line[0]
        cmd    = line[1]
        if(stx == 0x02 and cmd == 0x13):
            sn = line[5:17].decode('utf-8').strip()
        else:
            raise NameError('Retry')

        ser.write(w_value_query)
    
        # Read
        # STX(1), CMD(1), Size(2; lsb, msb), Data(24), Chksum(1)
        line = ser.readline()
        logging.debug(f'Data size:  {len(line)}')

        if(len(line) == 29):
            stx    = line[0]
            cmd    = line[1]
            chksum = line[-1]
            if(stx == 0x02 and cmd == 0x11):
                size = line[3]*16 + line[2]
                if(size == 24):
                    data = line[4:28]
                    pm1_10min   = data[13] * 16 + data[12]
                    pm2d5_10min = data[15] * 16 + data[14]
                    pm10_10min  = data[17] * 16 + data[16]
                    datapoint = {
                        'name'  : 'Dust Counter',
                        'dev'   : sn,
                        'model' : devinfo['model'],
                        'time'  : int(time.time()),
                        'pm1'   : pm1_10min,
                        'pm2d5' : pm2d5_10min,
                        'pm10'  : pm10_10min,
                        'pos'   : devinfo['pos']
                    }
                    
                else:
                    raise NameError('Retry')
            else:
                raise NameError('Retry')
        else:
            raise NameError('Retry')
    
    return datapoint

def main():

    model = os.getenv('DEVICE_MD',  '')
    dev   = os.getenv('DEVICE_USB', '')
    pos   = os.getenv('DEVICE_POS', '')

    devinfo = {
        'model' : model,
        'dev'   : dev,
        'pos'   : pos
    }
    
    while True:
        data = []
        try:
            datapoint = read(devinfo)
            dev       = datapoint['dev']
            data.append(datapoint)
        except:
            logging.exception('Exception: ')

        logging.debug(data)
        try:
            p = Path(SLOWDIR) / 'data' / f'{model}_{pos}_{dev}.dat'
            with p.open('w') as f:
                for d in data:
                    f.write(json.dumps(d)+'\n')
            f.close()

            cmd = f'scp {p} ymmon:/monitor/raw/'
            os.popen(cmd)
            time.sleep(600)
            
        except KeyboardInterrupt:
            logging.info('Good bye!')
            break
        except NameError:
            logging.exception('Exception: Retry')
            time.sleep(60)
        except:
            logging.exception('Exception: ')
            time.sleep(60)

if __name__ == '__main__':
    main()
```

### ApexP3-script
* Dust-couter
* `Apex.py`

```python
#!/opt/monitor/venv/bin/python
import sys
import time
import logging
from pathlib import Path
import json
import serial
import os
from pyModbusTCP.client import ModbusClient

logging.basicConfig(stream=sys.stdout, format="%(asctime)s %(levelname)-8s %(message)s", level=logging.DEBUG)

v_delay    = 0
v_hold     = 10
v_sample   = 900
v_interval = 890
v_sleep    = 0.5
SLOWDIR    = '/opt/monitor'

def read_serial(client):

    regs   = client.read_holding_registers(4, 2)
    serial = (regs[0] << 16) + regs[1]
    return serial

def read_device_setting(client):

    # check initial setting
    regs   = client.read_holding_registers(28,2)
    delay  = (regs[0] << 16) + regs[1]
    regs   = client.read_holding_registers(30,2)
    hold   = (regs[0] << 16) + regs[1]
    regs   = client.read_holding_registers(32,2)
    sample = (regs[0] << 16) + regs[1]
    if(not(delay == v_delay and hold == v_hold and sample == v_sample)):
       print("Wrong setting")
       print("Set :")
       print("\t delay  = ", v_delay,  " sec")
       print("\t hold   = ", v_hold,   " sec")
       print("\t sample = ", v_sample, " sec")
       client.write_single_register(29, v_delay)
       client.write_single_register(31, v_hold)
       client.write_single_register(33, v_sample)
       client.write_single_register(1, 1)

def read_device_status(client):
    
    # check status
    regs    = client.read_holding_registers( 2, 1)
    data    = {}
    data[0] = regs[0] & 0x1        # running
    data[1] = (regs[0] >> 1) & 0x1 # sampling

    return data

def run_start(client):
    client.write_single_register(1, 11)
            
def run_stop(client):
    client.write_single_register(1, 12)
            
def read_dust(client):

    data = {}
    reg  = client.read_input_registers(1008, 8)
    d0d3  = reg[0] * 65536 + reg[1]
    d0d5  = reg[2] * 65536 + reg[3]
    d5d0  = reg[4] * 65536 + reg[5]
    d10d0 = reg[6] * 65536 + reg[7]

    data[0] = d0d3
    data[1] = d0d5
    data[2] = d5d0
    data[3] = d10d0
   
    return data

def operation(devinfo):

    mod_ip = "192.168.2."+devinfo['dev']
    c      = ModbusClient(host = mod_ip, port =  502)
    serial = read_serial(c)
    read_device_setting(c)
    status_r = 0
    status_s = 0
    status   = read_device_status(c)
    status_r = status[0]
    
    logging.debug("Run Start")
    if(status_r == 0):
        run_start(c)
        
    while status_r == 0:
        status   = read_device_status(c)
        status_r = status[0]
        time.sleep(v_sleep)

    while status_s == 0:
        status   = read_device_status(c)
        status_s = status[1]
        time.sleep(v_sleep)

    time.sleep(v_sample)

    while status_s == 1:
        status   = read_device_status(c)
        status_s = status[1]
        time.sleep(v_sleep)

    run_stop(c)
    logging.debug("Run Stop")
    while status_r == 1:
        status   = read_device_status(c)
        status_r = status[0]
        time.sleep(v_sleep)

    data      = read_dust(c)
    datapoint = {
        'name'   : 'Dust Counter',
        'dev'    : serial,
        'model'  : devinfo['model'],
        'time'   : int(time.time()),
        'd0d3'   : data[0],
        'd0d5'   : data[1],
        'd5d0'   : data[2],
        'd10d0'  : data[3],
        'sample' : v_sample,
        'pos'    : devinfo['pos'],
        'ip'     : devinfo['dev']
    }

    return datapoint

def main():

    model = os.getenv('DEVICE_MD', '')
    dev   = os.getenv('DEVICE_IP', '')
    pos   = os.getenv('DEVICE_POS', '')

    devinfo = {
        'model' : model,
        'dev'   : dev,
        'pos'   : pos
    }

    while True:
        data = []
        try:
            datapoint = operation(devinfo)
            data.append(datapoint)
        except:
            logging.exception('Exception: ')

        logging.debug(data)

        try:
            p = Path(SLOWDIR) / 'data' / f'{model}_{pos}_{dev}.dat'
            with p.open('w') as f:
                for d in data:
                    f.write(json.dumps(d)+'\n')

            cmd = f'scp {p} ymmon:/monitor/raw/'
            os.popen(cmd)
            time.sleep(v_interval)
        except KeyboardInterrupt:
            logging.info('Good bye!')
            break
            
        except NameError:
            logging.exception('Exception: Wait')
            time.sleep(60)
            
        except:
            logging.exception('Exception: ')
            time.sleep(60)
        
if __name__ == '__main__':
    main()
```
### Start-up-script
* `start.sh`

```bash
#!/bin/bash
sleep 30
sudo supervisorctl start ssh_tunnel
sudo supervisorctl start run_cam
sudo supervisorctl start run_UA10
sudo supervisorctl start rad7-4331
sudo supervisorctl start run_DSM101
sleep 30
sudo supervisorctl restart ssh_tunnel
sleep 180
sudo supervisorctl start run_UA58
sleep 330
sudo supervisorctl start run_RS9A
```
## Supervisor

### SSH Tunnel-supervisor
* Internet with KT-LTE router does not allow direct connection
* Make an SSH Tunnel with arbitary port (`12345`)
	* (2023/02/20)
		* webcam1 : 12345 (AMoRE Exp Hall)
		* webcam2 : 12346 (AMoRE Clean Room)
		* pi1     : 12347 (AMoRE Exp Room)
		* rrs     : 12348 (RRS)
		* knu     : 12349 (KNU)

* `ssh.conf`

```
command = ssh -i /home/pi/.ssh/cup_desk_id_rsa -R 12345:localhost:22 ymmon
process_name = %(program_name)s
autostart = false
autorestart = true
user = pi
stopsignal=KILL
stdout_logfile = /opt/monitor/log/ssh_tunnel.out
stderr_logfile = /opt/monitor/log/ssh_tunnel.err
```

### RAD7-supervisor
* `rad7.conf`

```
[program:rad7-3775]
command = /opt/monitor/script/rad7-serial.py
process_name = %(program_name)s
autostart = false
autorestart = true
user = pi
redirect_stderr = true
stdout_logfile = /opt/monitor/log/rad7-serial_3775.out
stderr_logfile = /opt/monitor/log/rad7-serial_3775.err
environment = DEVICE = "/dev/serial/by-id/usb-FTDI_FT232R_USB_UART_A9KGLBIW-if00-port0", DEVICE_TAG = "AMoRE_EXP_HALL", DEVICE_SN = "3775"
```

### Radionode-supervisor
#### UA10-supervisor
* `UA10.conf`

```
[program:run_UA10]
command = /opt/monitor/script/UA10.py
process_name = %(program_name)s
autostart = false
autorestart = true
user = pi
redirect_stderr = true
stdout_logfile = /opt/monitor/log/UA10.out
stderr_logfile = /opt/monitor/log/UA10.err
environment = DEVICE_MD = "UA10", DEVICE_USB = "/dev/serial/by-id/usb-Dekist_Co.__Ltd._UA_SERIES__19040041-if00", DEVICE_POS = "AMoRE_EXP_HALL"
```

#### UA58-supervisor
* `UA58.conf`

```
[program:run_UA58]
command = /opt/monitor/script/UA58.py
process_name = %(program_name)s
autostart = false
autorestart = true
user = pi
redirect_stderr = true
stdout_logfile = /opt/monitor/log/UA58.out
stderr_logfile = /opt/monitor/log/UA58.err
environment = DEVICE_MD = "UA58", DEVICE_USB = "/dev/serial/by-id/usb-Dekist_Co.__Ltd._UA_SERIES__22110010-if00", DEVICE_POS = "AMoRE_EXP_HALL"
```

### FTLab-supervisor
#### RS9A-supervisor
* `RS9A.conf`

```
[program:run_RS9A]
command = /opt/monitor/script/RS9A.py
process_name = %(program_name)s
autostart = false
autorestart = true
user = pi
redirect_stderr = true
stdout_logfile = /opt/monitor/log/RS9A.out
stderr_logfile = /opt/monitor/log/RS9A.err
environment = DEVICE_MD = "RS9A", DEVICE_USB = "/dev/serial/by-id/usb-Silicon_Labs_CP2102_USB_to_UART_Bridge_Controller_0001-if00-port0", DEVICE_POS = "AMoRE_EXP_HALL"
```

#### DSM101-supervisor
* `DSM101.conf`

```
[program:run_DSM101]
command = /opt/monitor/script/DSM101.py
process_name = %(program_name)s
autostart = false
autorestart = true
user = pi
redirect_stderr = true
stdout_logfile = /opt/monitor/log/DSM101.out
stderr_logfile = /opt/monitor/log/DSM101.err
environment = DEVICE_MD = "DSM101", DEVICE_USB = "/dev/serial/by-id/usb-Prolific_Technology_Inc._USB-Serial_Controller_D-if00-port0", DEVICE_POS = "AMoRE_EXP_HALL"
```

### ApexP3-supervisor
* `Apex.conf`

```
[program:run_APEXP3]
command = /opt/monitor/script/Apex.py
process_name = %(program_name)s
autostart = false
autorestart = true
user = pi
redirect_stderr = true
stdout_logfile = /opt/monitor/log/Apex.out
stderr_logfile = /opt/monitor/log/Apex.err
environment = DEVICE_MD = "ApexP3", DEVICE_POS = "AMoRE_EXP_HALL", DEVICE_IP = "200"
```

### Start-up-supervisor
* `start.conf`

```
[program:startup]
command = /opt/monitor/script/start.sh
startsecs = 0
autostart = true
autorestart = false
startretries = 1
priority = 1
stdout_logfile = /opt/monitor/log/startup.out
stderr_logfile = /opt/monitor/log/startup.err
```

## ETC
* In the [files](./files/2_supervisor),
	* `dhcpcd.conf`
		* (move to `/etc/` with `sudo`)
	* `supervisord.conf`
		* (move to `/etc/supervisor/` with `sudo`)
	* Supervisor script ([files/supervisor](./files/2_supervisor/supervisor))
		* (move to `/opt/monitor/supervisor/available` and make a link)
	* Python script ([files/script](./files/2_supervisor/script))
		* (move to `/opt/monitor/script`)
		
		