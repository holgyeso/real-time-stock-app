from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, ArrayType, DecimalType, TimestampType, LongType
from pyspark.sql.functions import explode, arrays_zip

# 1. create PySpark session
spark = SparkSession \
    .builder \
    .appName("StructuredNetworkWordCount") \
    .config("spark.cassandra.connection.host", "host.docker.internal:9042") \
    .getOrCreate()

# 2. define schema of the json file

schema = StructType([
    StructField('data', ArrayType(
        StructType([
            StructField('p', DecimalType(10,4), False),
            StructField('s', StringType(), False),
            StructField('t', LongType(), False),
            StructField('v', IntegerType(), False)
        ])
    ), False),
    StructField('type', StringType(), False)
])

# 3. define the Data Frame Stream
streaming_df = spark.readStream \
                    .format("json") \
                    .schema(schema) \
                    .option("multiLine", "True") \
                    .load(path="/input")

# process the data

streaming_df = streaming_df \
    .select(explode(arrays_zip("data.p", "data.t", "data.s", "data.v"))) \
    .selectExpr(
        "col.p as price",
        "col.s as symbol",
        "col.t as ts",
        "col.v as volume"
    )

# streaming_df.writeStream \
#            .format("org.apache.spark.sql.cassandra") \
#            .options(table='trades', keyspace='stockapp') \
#            .outputMode("update") \
#            .start()
#         #    .awaitTermination() 

def insert_foreach(row, epoch_id):
    row.write \
        .format("org.apache.spark.sql.cassandra") \
        .options(table='trades', keyspace='stockapp') \
        .mode("append") \
        .save()

streaming_df.writeStream.foreachBatch(insert_foreach).start().awaitTermination() 