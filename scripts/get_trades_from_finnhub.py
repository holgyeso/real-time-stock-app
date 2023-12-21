from cassandra.cluster import Cluster, NoHostAvailable, DriverException
import time, logging, websocket, datetime, json, os
from pyspark.sql import SparkSession

def get_stocks_from_Hadoop():
    spark = SparkSession \
            .builder \
            .appName("Ex") \
            .config("spark.sql.warehouse.dir", "hdfs://namenode:8020/user/hive/warehouse") \
            .config("hive.metastore.uris", "thrift://host.docker.internal:9083") \
            .enableHiveSupport() \
            .getOrCreate()
    
    logging.info(" ... Getting Hadoop data")
    
    spark.sql("CREATE EXTERNAL TABLE IF NOT EXISTS stocks(Symbol CHAR(100), Security CHAR(200), Sector CHAR(200), Index char(200)) STORED AS PARQUET location 'hdfs://namenode:8020/data/stocks';")
    data = spark.sql("SELECT * from stocks;")
    symbols = [row.Symbol for row in data.select('Symbol').distinct().sort('Symbol').limit(10).collect()]
    symbols = ['AAPL', 'MMM', 'GOOGL', 'TSLA']
    return symbols
    

def on_message(ws, message): # save input as JSON file
    
    curr_time = round(datetime.datetime.timestamp(datetime.datetime.now()) * 1000)

    with open(f"/input/input_{curr_time}", "w") as f:
        json.dump(json.loads(message), f) # the message received is a dictionary as string => parsed with json

def on_error(ws, error):
    print("ERROR", error)

def on_close(ws):
    print("### closed ###")

def on_open(ws):
    # ws.send('{"type":"subscribe","symbol":"AAPL"}')
    stocklist = get_stocks_from_Hadoop()
    logging.info(" ... Subscribing to data")

    for stock in stocklist:
        ws.send('{"type":"subscribe","symbol":"' + stock + '"}')


def pull_data_from_Finnhub(stock_list):
    websocket.enableTrace(True) #TODO: to delete, it's for debug purposes
    ws = websocket.WebSocketApp("wss://ws.finnhub.io?token=" + os.getenv('FINNHUB_TOKEN'),
                               on_message = on_message)
                            #   on_error = on_error,
                            #   on_close = on_close)
    ws.on_open = on_open
    ws.run_forever(reconnect=2)

connection_failed = True

while True:
    try:
        while connection_failed:
            try:
                time.sleep(2)
                logging.info("Try to connect Cassandra [host.docker.internal:9042]...")
                cluster = Cluster(['host.docker.internal'])
                cluster.connect('stockapp')
                connection_failed = False
                logging.info("...Successful")

                # if connection can be made with Cassandra, it means that the Finnhub data pull can be started
                stock_list = get_stocks_from_Hadoop()
                if stock_list == []:
                    connection_failed = True
                else:
                    logging.info(" ... Data should be pulled")
                    pull_data_from_Finnhub(stock_list)

            except NoHostAvailable:
                logging.warning("   ...Cassandra [host.docker.internal:9042] is not available - will try again later")
                continue
            except DriverException:
                logging.warning("   ...Cassandra [host.docker.internal:9042] shut down - will try again later")
                continue
            except Exception as err:
                raise err
    except Exception as e:
        logging.debug("Reconnecting to websocket after 3 sec")
        time.sleep(3)