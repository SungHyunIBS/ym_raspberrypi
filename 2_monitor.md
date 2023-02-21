# Monitor
<hr/>

### Contents
1. [Install](#install)
2. [Script](#script)
	* [Webcam](#webcam-script)
	* [RAD7](#rad7-script)
	* [UA10](#ua10-script)
3. [Supervisor](#supervisor)
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

## Script
### Webcam-script
* `webcam.py`

```
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
* UA58 : Airborne Chemical (O~2~, CO~2~, CO, H~2~S)

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

def read(dev_md, dev_usb, dev_pos):
    datapoint = {}
    with serial.Serial(dev_usb, 19200, timeout=5) as ser:
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
        'name' : 'temphum',
        'dev'  : sn,
        'model': dev_md,
        'time' : int(time.time()),
        'temp' : float(temp),
        'hum'  : float(hum),
        'pos'  : dev_pos
    }
    
    return datapoint

def main():

    dev_md  = os.getenv('DEVICE_MD', '')
    dev_usb = os.getenv('DEVICE_USB', '')
    dev_pos = os.getenv('DEVICE_POS', '')
    
    while True:
        data = []
        try:
            datapoint = read(dev_md, dev_usb, dev_pos)
            data.append(datapoint)
            dev   = datapoint['dev']
            model = dev_md
            pos   = dev_pos
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

def read(dev_md, dev_usb, dev_pos):
    datapoint = {}
    with serial.Serial(dev_usb, 19200, timeout=5) as ser:
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
        'model' : dev_md,
        'time'  : int(time.time()),
        'Rn'    : int(rn),
        'pos'   : dev_pos
    }

    return datapoint
        
def main():

    dev_md  = os.getenv('DEVICE_MD', '')
    dev_usb = os.getenv('DEVICE_USB', '')
    dev_pos = os.getenv('DEVICE_POS', '')

    while True:
        data = []
        try:
            datapoint = read(dev_md, dev_usb, dev_pos)
            data.append(datapoint)
            dev   = datapoint['dev']
            model = dev_md
            pos   = dev_pos
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
### ApexP3-script

### Start-up-script

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
erxitgcodes=0
user = pi
stopsignal=KILL
stdout_logfile = /opt/monitor/log/ssh_tunnel.out
stderr_logfile = /opt/monitor/log/ssh_tunnel.err
```

### RAD7-supervisor


### Radionode-supervisor
### FTLab-supervisor
#### RS9A-supervisor
#### DSM101-supervisor
### ApexP3-supervisor

### Start-up-supervisor


## ETC
* In the [files](./files/2_supervisor),
	* `supervisord.conf`
		* (move to `/etc/supervisor/` with `sudo`)
	* Supervisor script ([files/supervisor](./files/2_supervisor/supervisor))
		* (move to `/opt/monitor/supervisor/available` and make a link)
	* Python script ([files/script](./files/2_supervisor/script))
		* (move to `/opt/monitor/script`)
		
		