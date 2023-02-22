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
            dev       = datapoing['dev']
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
