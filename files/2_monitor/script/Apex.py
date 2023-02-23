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
