from cassandra.cluster import Cluster, NoHostAvailable, DriverException
import time, logging, websocket, datetime, json, os

def on_message(ws, message): # save input as JSON file
    
    curr_time = round(datetime.datetime.timestamp(datetime.datetime.now()) * 1000)

    with open(f"/input/input_{curr_time}", "w") as f:
        json.dump(json.loads(message), f) # the message received is a dictionary as string => parsed with json

def on_error(ws, error):
    print("ERROR", error)

def on_close(ws):
    print("### closed ###")

def on_open(ws, stocklist=['AAPL', 'GOOGL', 'TSLA']):
    # ws.send('{"type":"subscribe","symbol":"AAPL"}')
    for stock in stocklist:
        ws.send('{"type":"subscribe","symbol":"' + stock + '"}')


def pull_data_from_Finnhub(stock_list):
    websocket.enableTrace(True)
    ws = websocket.WebSocketApp("wss://ws.finnhub.io?token=" + os.getenv('FINNHUB_TOKEN'),
                               on_message = on_message)
                            #   on_error = on_error,
                            #   on_close = on_close)
    ws.on_open = on_open
    ws.run_forever()

connection_failed = True

while connection_failed:
    try:
        time.sleep(2)
        logging.info("Try to connect Cassandra [host.docker.internal:9042]...")
        cluster = Cluster(['host.docker.internal'])
        cluster.connect('stockapp')
        connection_failed = False
        logging.info("...Successful")

        # if connection can be made with Cassandra, it means that the Finnhub data pull can be started
        pull_data_from_Finnhub(['AAPL', 'GOOGL', 'TSLA'])

    except NoHostAvailable:
        logging.warning("   ...Cassandra [host.docker.internal:9042] is not available - will try again later")
        continue
    except DriverException:
        logging.warning("   ...Cassandra [host.docker.internal:9042] shut down - will try again later")
        continue
    except Exception as err:
        raise err