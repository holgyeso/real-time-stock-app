import time
import logging
import streamlit as st
from pyspark.sql import SparkSession
from cassandra.cluster import Cluster, NoHostAvailable, DriverException



### DIRECTLY USED ON STREAMLIT PAGES ###

def setup_page():
    """Configure the streamlit app icon & name
    """

    return st.set_page_config(
            page_icon="🪙",
            page_title="Stock App",
            initial_sidebar_state = "expanded",
        )

def sidebar():
    with st.sidebar:
        with st.spinner('Connecting to Cassandra...'):
            cassandra_connection()

def cassandra_connection():
    connected = False

    while not connected:
        
        try:
            # try to connect to Cassandra
            cluster = Cluster(['host.docker.internal'])
            connection = cluster.connect('stockapp')
            connected = True
            
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
        

    return connection


def get_hive_connection():
    return SparkSession \
            .builder \
            .appName("Ex") \
            .config("spark.sql.warehouse.dir", "hdfs://namenode:8020/user/hive/warehouse") \
            .config("hive.metastore.uris", "thrift://host.docker.internal:9083") \
            .enableHiveSupport() \
            .getOrCreate()

def create_hive_tables(sparksession):
    sparksession.sql("CREATE EXTERNAL TABLE IF NOT EXISTS stocks(Symbol CHAR(100), Security CHAR(200), Sector CHAR(200), Index char(200)) STORED AS PARQUET location 'hdfs://namenode:8020/data/stocks';")


def get_index_and_stocks(sparksession):
    data = sparksession.sql("SELECT * from stocks;")
    # st.write(data)
    return data


def side_bar(stock_df):
    with st.sidebar:
        st.text("Choose what you are interested in!")
        sidebar_index_selectbox = st.selectbox(
            label="Choose the index", 
            # options=[row.Index for row in stock_df.select('Index').distinct().collect()],
            options=["NASDAQ", "S&P500"],
            index=None
        )

        sidebar_stock_selectbox = st.selectbox(
            label="Choose the stock",
            options=[row.Symbol + '(' + row.Security + ')' for row in stock_df\
                                                            .filter(stock_df.Index == sidebar_index_selectbox) \
                                                            .select(['Symbol', 'Security']) \
                                                            .distinct() \
                                                            .sort("Symbol", ascending=True) \
                                                            .collect()]
        )
    return (sidebar_index_selectbox, sidebar_stock_selectbox)

