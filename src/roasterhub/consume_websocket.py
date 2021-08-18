import asyncio
from json import dumps as jdumps
from json import loads as jloads
import time
import websockets


async def consume1():
    # ws://127.0.0.1:8080/websocket
    uri = "ws://127.0.0.1:8080/websocket"
    async with websockets.connect(uri) as websocket:
        await websocket.send("")
        data = await websocket.recv()
        print(data)

while True:
    time.sleep(1)
    data_json = asyncio.get_event_loop().run_until_complete(consume1())
    data_dict = jloads(data_json)
    bt = data_dict['data'].get('bt', None)
    et = data_dict['data'].get('et', None)
    roastTime = data_dict['data'].get('time', None)
    if bt:
        print(f'bt temp = {bt}')

    if et:
        print(f'et temp = {et}')

    if roastTime:
        print(f'Roast Time = {roastTime}')

    print('\n')
    bt = data_dict['data']['bt']
    et = data_dict['data']['et']
    roastTime = data_dict['data']['time']
    if roastTime != '00:00':
        print('record and send')

    print(f'bt = {bt}, et = {et}, time = {roastTime}')
    print(data_dict)