from pyspark.sql import SparkSession
import time
import datetime
import logging
from cassandra.cluster import Cluster, NoHostAvailable, DriverException

while True:

    # 0. set the current datetime stamp
    timestamp_now = int((datetime.datetime.now() - datetime.datetime(1970, 1, 1)).total_seconds() * 1000)

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
            
            # 3. read from Cassandra current rows
            cassandra_content = spark.read \
                            .format("org.apache.spark.sql.cassandra") \
                            .options(table='trades', keyspace='stockapp') \
                            .load()
            
            # 4. truncate the table
            connection.execute("TRUNCATE stockapp.trades;")

            # 5. send to hadoop
            cassandra_content.write.mode('append').parquet("hdfs://namenode:8020/data/trades")
    
            
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

    time.sleep(60)