import json
import websocket
import time

data_frame = list()
time_frame = list()


def on_message(ws, message):
    msg = json.loads(message)
    data_msg = msg.get('data', None)
    if data_msg:
        data_bt = data_msg.get('bt', None)
        data_et = data_msg.get('et', None)
        data_time = data_msg.get('time', None)
        # if data_bt and data_time != '00:00':
        #     data_frame.append([data_bt, data_et])
        if data_time and data_time != '00:00':
            data_frame.append([data_bt, data_et])
            time_frame.append(data_time)
        print(data_frame)
        print(time_frame)

    # global df
    # `ignore_index=True` has to be provided, otherwise you'll get
    # "Can only append a Series if ignore_index=True or if the Series has a name" errors
    # df = df.append(msg, ignore_index=True)


def on_error(ws, error):
    print(error)


def on_close(ws):
    print("### closed ###")


def on_open(ws):
    return


def readSendData():
    ws = websocket.WebSocketApp(
        "ws://127.0.0.1:8080/websocket", on_open=on_open, on_message=on_message, on_error=on_error, on_close=on_close
    )
    ws.run_forever()


if __name__ == "__main__":
    readSendData()