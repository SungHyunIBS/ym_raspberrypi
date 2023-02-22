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
