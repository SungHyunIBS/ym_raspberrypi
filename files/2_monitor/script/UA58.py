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
