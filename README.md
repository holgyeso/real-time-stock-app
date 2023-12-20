# Big Data Application - Real-time stock analytics platform

## About the project
The application written in Streamlit aims to provide a Big Data architecture use case that implements the batch and the speed layer. It consists of the following parts:

1. Real-time stock data and analytics 
    * the real-time data source is trading data from [Finnhub](https://finnhub.io/docs/api/websocket-trades)
    * the data is ingested using a web socket 
    * and is processed with PySpark
    * the final sink is a Cassandra table
    * the data in the app is refreshed automatically every 5 seconds

2. Batch & serving layer:
    * each minute, trade data from Cassandra is transferred to Hadoop - TBC the frequency
    * in Hadoop, there is also information about the stocks, namely to which index they belong, the name of the issuer company and the sector in which the company functions. All stocks from the S&P500 and NASDAQ indexes are scraped.
    * on top of the single-node Hadoop, there is also a Hive schema defined for both the trades and the indexes
    * a PySpark logic connects to Hive and displays information in the Streamlit application

3. Forecasting - TBA

## Structure
The dockerized application currently consists of 13 containers:

1. 5 containers (`namenode`, `datanode`, `hive-server`, `hive-metastore`, `hive-metastore-postgresql`) are required for Hadoop & Hive. The setup was cloned from [big-data-europe/docker-hive](https://github.com/big-data-europe/docker-hive) GitHub repository, so for more information, please refer to the README of that project.
   * `namenode` is accessible as `hdfs://namenode:8020/`
   * the stock data is stored in Parquet format in `/data/stocks` folder
   * the trade data copied each minute from the batch layer is stored in Parquet format in `/data/trades` folder - TBA schedule
   * connect to Hive: `beeline -u jdbc:hive2://localhost:10000 -n root`

2. `stock-index-scraper` container: `apache/spark-py:v3.4.0` image with `pandas`, `lxml` and `pyarrow` installed
    
    This container runs the `/pyspark_batch_init.sh`, which executes `/read_stock_indexes.py`. In this file:
    * all stocks belonging to [S&P500](https://en.wikipedia.org/wiki/List_of_S%26P_500_companies) and [NASDAQ](https://en.wikipedia.org/wiki/Nasdaq-100) are scraped from Wikipedia in the following format:
      * `Symbol` - the symbol of the stock
      * `Security` - the trading company
      * `Sector` - the GICS sector to which the stock belongs
      * `Index` - constant to denote S&P500 or NASDAQ index
    * the scraped data is sent in Parquet format to Hadoop's `/data/stocks` folder

    ⚠️ This container is meant to be executed only once, so the expected behavior is that the container exits without any error message.


3. `db-cassandra` container: `cassandra:4.1.3` image - https://hub.docker.com/_/cassandra
    
    Each time the container is started, the following Cassandra objects are created *(in `scripts/make-cassandra-tables.sh` file)*:
    * keyspace `stockapp` with *SimpleStrategy* replication of factor 1
    * table `trades` within `stockapp` keyspace with 4 columns:
        * `ts` TIMESTAMP
        * `symbol` VARCHAR
        * `price` DECIMAL
        * `volume` INT
    * the primary key consists of `(symbol, ts)`, which means that the `symbol` column is the partition row and `ts` the clustering key. *Obs. Filtering only on these 2 columns is possible without ALLOW FILTERING option, which reduces the execution's effectiveness*

4. `viz-grafana` container: `grafana/grafana:10.2.0` image - https://hub.docker.com/r/grafana/grafana

    Grafana ingests data from Cassandra and currently creates 2 time-series visualizations about the evolution of volume and prices of the stock selected at the `Stock Symbol` variable. -> TBD if remains

5. `real-time-trades-processing` container: `apache/spark-py:v3.4.0` image - https://hub.docker.com/r/apache/spark-py

    The processing part is realized by using Apache Pyspark. A Streaming Data Frame is initialized on the `/input` folder and a script processes the JSON output into a tabular format with the following specifications *(processing done in `scripts/real_time_processing.py` file)*:
    * `ts` LongType()
    * `symbol` StringType()
    * `price` DecimalType(10,4)
    * `volume` IntegerType()

    *Obs. Please note that Cassandra automatically makes the conversion between the ts bigint type from PySpark and ts timestamp type in Cassandra.*

    After a JSON file is processed, it will be deleted.

6. `finnhub-download` container: `apache/spark-py:v3.4.0` image with `cassandra-driver`, `asyncore-wsgi`, `websocket-client` and `pyspark` installed

    This part of the Docker image has the responsibility of ingesting data from [Finnhub](https://finnhub.io/docs/api/websocket-trades). The script (`scripts/get_trades_from_finnhub.py`) starts only when Cassandra's `stockapp` keyspace and stock data in Hadoop are available. It connects to the Finnhub web socket and generates from each received message a JSON file into the `/input` folder with the current timestamp to make each file unique. This folder is mirrored also in the PySpark container, this is how the two will communicate.

    ⚠️ Finnhub enables the user to subscribe only to 50 stocks.

    *Obs. While in Java and Scala a custom socket class could have been made to ingest data directly from the web socket, in Python the socket streaming is only advised for testing. Therefore the file ingesting stable option was chosen.*

    The structure of the data received from Finnhub:
        
        { "data": [
            {
                "p": <price_decimal>,
                "s": <symbol_str>,
                "t": <timestamp_bigint>,
                "v": <volume_int>
            },
            ...
        ],
        "type": "trade"}

    *Please note that in a message the number of the dict objects within the "data" key can vary.*

7. `streamlit-app` container: `apache/spark-py:v3.4.0` image with `cassandra-driver`, `pandas`, `streamlit` and `delta-spark==2.1.1` packages

    The Streamlit app is available at `http://localhost:8000/` and currently consists of:
    * *Welcome* page, which shows the About and some metrics on how many stocks are analysed
    * *Real-time trade analytics* where information on the stock along with some real-time (refreshing in every 5 seconds) charts are displayed
    * TBA
 
8. `stream-batch-transfer` container: `apache/spark-py:v3.4.0` image with `cassandra-driver` installed.
   
    This container executes `transfer_real_to_batch.py` which transfers every minute the data from the speed layer (from Cassandra) to the batch layer (in Hadoop) and then truncates the table in Cassandra.


## How to use the application

### Prerequisites

1. You should have Docker installed
2. **Environment variables** - All environment variables should be placed in a `.env` file in the folder where the `docker-compose.yml` was created. It should contain the following variables:
    * FINNHUB_TOKEN - the token that is available in Finnhub's dashboard after an account is created

### Steps of installation and user guide:

1. git clone this repo: `git clone https://github.com/holgyeso/real-time-stock-app.git`
2. enter the downloaded folder: `cd real-time-stock-app`
3. build & start docker container: `docker compose up -d`
    
    * The `cassandra` image takes a while until it is correctly initiated. To assure that this is up and running among the logs the *"Created default superuser role 'cassandra'"* message should appear.

    * The data ingestion from Finnhub starts only after the `stockapp` keyspace in `cassandra` is initiated and stocks exist in Hadoop.

4. navigate to`http://localhost:8000/` to access the data through the app created in Streamlit.

    As soon as the database is available, the data from Finnhub will be pulled, processed and visualized. The charts are automatically refreshed each 5s.

5. Do not forget to stop the containers if not in use anymore.