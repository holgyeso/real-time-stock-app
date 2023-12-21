from pyspark.sql import SparkSession
import time
import logging
import datetime
from cassandra.cluster import Cluster, NoHostAvailable, DriverException

transfer_data_seconds = 60

while True:

    # 0. set the current datetime stamp
    # timestamp_now = int(time.time() * 1000)
    timestamp_now = round((datetime.datetime.now() - datetime.timedelta(seconds=transfer_data_seconds) - datetime.datetime(1970, 1, 1)).total_seconds() * 1000)

    with open("/log.txt", mode="a") as f:
        f.writelines(["-------\n", "Beginning in time " + str(timestamp_now) + "\n"])

    # 1. connect to Cassandra
    connected = False

    while not connected:
        
        try:
            # try to connect to Cassandra
            cluster = Cluster(['host.docker.internal'])
            connection = cluster.connect('stockapp')
            connected = True

            # 2. create PySpark session
            spark = SparkSession \
                .builder \
                .appName("StructuredNetworkWordCount") \
                .config("spark.cassandra.connection.host", "host.docker.internal:9042") \
                .config("confirm.truncate", True) \
                .getOrCreate()
            with open("/log.txt", mode="a") as f:
                f.writelines(["Read rows\n"])

            # 3. read from Cassandra current rows
            cassandra_content = spark.read \
                            .format("org.apache.spark.sql.cassandra") \
                            .options(table='trades', keyspace='stockapp') \
                            .load() \
                            .filter(f"ts < from_unixtime({timestamp_now})")

            # 4. send to hadoop
            with open("/log.txt", mode="a") as f:
                f.writelines(["Writing to Hadoop\n"])
            cassandra_content.write.mode('append').parquet("hdfs://namenode:8020/data/trades")

            # 5. delete from Cassandra
            for stock in [row.symbol for row in cassandra_content.select('symbol').distinct().collect()]:
                with open("/log.txt", mode="a") as f:
                    f.writelines([f"DELETE FROM stockapp.trades WHERE ts <= {timestamp_now} and symbol='{stock}';\n"])
                connection.execute(f"DELETE FROM stockapp.trades WHERE ts <= {timestamp_now} and symbol='{stock}';")
    
            
        except NoHostAvailable:
            logging.warning("   ...Cassandra [host.docker.internal:9042] is not available - will try again later")
            time.sleep(2)
            continue
        except DriverException:
            logging.warning("   ...Cassandra [host.docker.internal:9042] shut down - will try again later")
            time.sleep(2)
            continue
        except Exception as err:
            raise err    

    time.sleep(transfer_data_seconds)