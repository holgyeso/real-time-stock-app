import streamlit as st
import stockapp_utils

# set the icon and title appearing in browser
stockapp_utils.setup_page()

# TODO: set the title of the page
st.title("Welcome to Stock App! ✨")

# TODO: description of the page
st.subheader("About this project")
st.markdown("Lorem ipsum dolor sit amet, consectetur adipiscing elit. Donec lobortis neque ac mauris commodo, pellentesque volutpat purus varius. Nunc pretium, nisi ac hendrerit condimentum, purus arcu volutpat elit, in varius felis enim eu quam. Interdum et malesuada fames ac ante ipsum primis in faucibus. Suspendisse sit amet vulputate diam, fringilla scelerisque quam. Phasellus non dignissim diam, ut finibus ante. Donec volutpat turpis quis neque varius, ut egestas arcu rhoncus. Duis ac tincidunt nunc. Integer sit amet rutrum ligula. Cras hendrerit lectus augue, sed commodo ex efficitur eget. Phasellus eu quam sit amet massa feugiat hendrerit. Vivamus purus nulla, condimentum ac felis a, mattis pretium nisi. Aliquam pellentesque, diam quis dignissim suscipit, purus felis condimentum lacus, non lacinia sem turpis ac sem. Nullam non mi non dolor congue tempus.")


spark = stockapp_utils.get_hive_connection()

with st.sidebar:
    with st.status("Fetching data...", expanded=True) as status:
        st.write("Connecting to Cassandra...")
        stockapp_utils.cassandra_connection()
        st.write("Getting index data...")
        stockapp_utils.create_hive_tables(spark)
        stocks_df = stockapp_utils.get_index_and_stocks(spark)
        status.update(label="Data fetched", state="complete", expanded=False)


kpis = st.columns(3, gap="small")
kpis[0].metric(label="Number of available indexes: ", value=stocks_df.select('Index').distinct().count())
kpis[1].metric(label="Number of available stocks: ", value=stocks_df.select('Symbol').distinct().count())
kpis[2].metric(label="Number of available sectors: ", value=stocks_df.select('Sector').distinct().count())



# with st.container():
#     kpis = st.columns(3, gap="small")

#     stockapp_utils.create_hive_tables(spark)
#     stocks = stockapp_utils.get_index_and_stocks(spark)

#     with st.spinner():
#         kpis[0].metric(
#             label="Number of available indexes: ", 
#             value=10
#         )
#         kpis[1].write("We have analysed 20 stocks")
#         kpis[2].write("We have analysed 14 industries")



# kpis[0].write(F"")

# st.write(stocks)

# from cassandra.cluster import Cluster, NoHostAvailable, DriverException
# import time, logging


# connection_failed = True

# cassandra_connection = st.error('Cassandra not connected', icon="🚨")
# st.title("Stock app")

# spark = 

# # TODO: add retry mechanism

# spark.sql("CREATE EXTERNAL TABLE IF NOT EXISTS stocks(Symbol CHAR(100), Security CHAR(200), Sector CHAR(200), Index char(200)) STORED AS PARQUET location 'hdfs://namenode:8020/data/stocks';")

# data = spark.sql("SELECT * from stocks;")

# st.write(data)



# while connection_failed:
#     try:
        
        
#         time.sleep(2)
#         # check Cassandra is up and running
#         logging.info("Try to connect Cassandra [host.docker.internal:9042]...")
#         cluster = Cluster(['host.docker.internal'])
#         cluster.connect('stockapp')
#         connection_failed = False
#         logging.info("...Successful")

#         cassandra_connection.empty()
#         cassandra_connection.success("Cassandra connected", icon="✅")

#         spark = SparkSession \
#         .builder \
#         .appName("Python Spark SQL Hive integration example") \
#         .config("hive.metastore.uris", "thrift://host.docker.internals:9083") \
#         .enableHiveSupport() \
#         .getOrCreate()

#         spark.sql("CREATE EXTERNAL TABLE IF NOT EXISTS stocks(Symbol CHAR(100), Security CHAR(200), Sector CHAR(200), Index char(200)) STORED AS PARQUET location '/data/sp5.parquet'")

#         data = spark.sql("SELECT * FROM stocks")

#         st.write(data)

    # except NoHostAvailable:
    #     logging.warning("   ...Cassandra [host.docker.internal:9042] is not available - will try again later")
    #     continue
    # except DriverException:
    #     logging.warning("   ...Cassandra [host.docker.internal:9042] shut down - will try again later")
    #     continue
    # except Exception as err:
    #     raise err