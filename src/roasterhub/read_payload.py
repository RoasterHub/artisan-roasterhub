import time as libtime
from json import dumps as jdumps
from json import load as jload
import time
import paho.mqtt.client as mqtt
import socket

from os import environ
from pathlib import Path

import platform
                                                                                                                                            

local_mode = False
server1 = "MQTT_SERVER_1"
server2 = "MTQTT_SERVER_1"

if local_mode:
    server = "127.0.0.1"

port = 1883                                                                                                                                                       
                                                                                                                                                              

if platform.system() == 'Windows':
    Path(environ['HOMEPATH']+'/.rhub').mkdir(parents=True, exist_ok=True)
    usercrpath = environ['HOMEPATH'] + '\\.rhub\\usercr.json'
                                                                                                                                                                
else:
    usercrpath = environ['HOME'] + '/.rhub/usercr.json'

with open(usercrpath) as f:
    data_user = jload(f)

# with open(devidpath) as f:
#     data_devid = jload(f)


username = data_user['user']
password = data_user['password']
serialid = data_user['data']

client_id = serialid
topic = 'roasterhubdatasensorbtet/' + username


def on_publish(client, userdata, mid):
    print("mid: "+str(mid))


client = mqtt.Client(client_id=client_id)
client.on_publish = on_publish

# roasterhub as vhost
mqtt_username = 'roasterhub:'+username

client.username_pw_set(mqtt_username, password)
error_conn = False
try:
    client.connect(server1, port, 30)
except socket.gaierror:
    print('No internet')
    error_conn = True
except TimeoutError:
    client.connect(server2, port, 30)
except OSError:
    print("No Internet!")
    error_conn = True
    
finally:
    if not error_conn:
        print('connected!')
        client.loop_start()
        client.reconnect_delay_set(min_delay=1, max_delay=30)


initial_state = False


def readData(payload: str, state: bool, session_var: str):

    if state:
        payload['data']['username'] = username
        payload['data']['serialid'] = serialid
        payload['data']['session'] = session_var
        data = jdumps(payload)
        client.publish(topic, str(data), qos=1)
        initial_state = True
    if not state and initial_state:
        print('end connection')
        client.disconnect()
        client.loop_stop()
