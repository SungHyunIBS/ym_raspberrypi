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

outputdir = '/opt/monitor/out'
def main():
    cnt = 0

    subject  = os.getenv('DEVICE_SUB','')
    devn     = os.getenv('DEVICE_NUM','')
    ismulti  = os.getenv('ISMULTICAM','')
    ismon    = int(os.getenv('ISMONITOR',''))
    if(ismon == 1):
        monmin = int(os.getenv('MONMIN',''))
    capwait  = int(os.getenv('CAPWAIT',''))

    wait     = capwait*60
    idevn    = int(devn)*4
    while True:
        try:
            cap = cv2.VideoCapture(idevn)
            cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M','J','P','G'))
            cap.set(cv2.CAP_PROP_FRAME_WIDTH,  1920) #3840
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080) #2160

            ret, image = cap.read()
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
            now = datetime.now()
            current_time = now.strftime("%Y%m%d_%H%M")

            if(int(ismulti) == 0):
                camdir = outputdir
                cpdir  = subject
            else:
                camdir = outputdir+'/webcam'+devn
                cpdir  = subject+devn

            output = 'webcam.png'
            outtxt = 'webcam.txt'
            outfile = Path(camdir) / output
            outtime = Path(camdir) / outtxt
            cv2.imwrite(f'{outfile}', image)
            cap.release()
            
            with outtime.open('w') as f:
                f.write(str(int(time.time()) * 1000)+'\n')
                
            logging.info("Save {} : {}, \t{}".format(output, current_time, cnt))
            os.popen("scp {} ymmon:/monitor/www/html/{}/".format(outfile, cpdir))
            os.popen("scp {} ymmon:/monitor/www/html/{}/".format(outtime, cpdir))
            if(ismon == 1):
                cnt += 1
                if(cnt == monmin):
                    cnt = 0
                    outfile_t = webcam+'_'+current_time+'.png'
                    logging.info("Copy {} : {}".format(output, current_time))
                    os.popen("scp {} ymmon:{}/{}".format(outfile, cpdir, outfile_t))
                
            time.sleep(wait)
        except KeyboardInterrupt:
            logging.info('Good bye')
            break
        except:
            logging.exception('Exception')
            time.sleep(wait)

if __name__ == '__main__':
    main()
