# Big Data Application - Real time stock analytics platform

## About the project
The application aims to provide a Big Data architecture use-case that implements the batch and the speed layer. It consists of following parts:

1. Real time stock data and analytics 
    * the real-time datasource is trading data from [Finnhub](https://finnhub.io/docs/api/websocket-trades)
    * the data is ingested using a websocket 
    * and is processed with PySpark
    * the final sink is a Cassandra table
    * the reporting layer is realized in Grafana - currently it displays visualization of the volumes

## Structure
The dockerized application currently consists of 4 images:
1. cassandra:4.1.3 - https://hub.docker.com/_/cassandra
    
    Each time when the container is started, the following cassandra objects are created *(in `scripts/make-cassandra-tables.sh` file)*:
    * keyspace `stockapp` with *SimpleStrategy* replication of factor 1
    * table `trades` within `stockapp` keyspace with 4 columns:
        * `ts` TIMESTAMP
        * `symbol` VARCHAR
        * `price` DECIMAL
        * `volume` INT
    * the primary key consists from `(symbol, ts)`, this means that the `symbol` column is the partition row and `ts` the clustering key. *Obs. filtering only on these 2 columns is possible without ALLOW FILTERING option, that reduces the execution's efectiveness*

2. grafana/grafana:10.2.0 - https://hub.docker.com/r/grafana/grafana

    Grafana ingests data from Cassandra and currently creates 2 time series visualizations about the evolution of volume and prices of the stock selected at the `Stock Symbol` variable.

3. apache/spark-py:v3.4.0 - https://hub.docker.com/r/apache/spark-py

    The processing part is realized by using Apache Pyspark. A Streaming Data Frame is initialized on the `/input` folder and a script processes the JSON output into a tabular format with following specifications *(processing done in `scripts/real_time_processing.py` file)*:
    * `ts` LongType()
    * `symbol` StringType()
    * `price` DecimalType(10,4)
    * `volume` IntegerType()

    *Obs. Please note that Cassandra automatically makes the conversion between the ts bigint type from PySpark and ts timestamp type in Cassandra.*

    After a JSON file is processed, it will be deleted.

4. python:3.9.18-alpine3.18 - https://hub.docker.com/_/python

    This part from the Docker image has the responsability of ingesting data from [Finnhub](https://finnhub.io/docs/api/websocket-trades). The script (`scripts/get_trades_from_finnhub.py`) starts only when Cassandra's `stockapp` keyspace is available. I0t connects to the Finnhub websocket and generates from each received message a JSON file into the `/input` folder with the current timestamp to make each file unique. This folder is mirrored also in the PySpark container, this is how the two will communicate.

    *Obs. While in Java and Scala a custom socket class could have been made to ingest data directly from the websocket, in Python the socket streaming is only advised for testing. Therefore the file ingesting stable option was chosen.*

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


## How to use the application

### Prerequisites

1. You should have Docker installed
2. **Environment variables** - All environment variables should be placed in a `.env` file in the folder where the `docker-compose.yml` was created. It should contain following variables:
    * FINNHUB_TOKEN - the token that is available in Finnhub's dashboard after an account is created

### Steps of installation and user guide:

1. git clone this repo: `git clone https://github.com/holgyeso/real-time-stock-app.git`
2. enter the downloaded folder: `cd real-time-stock-app`
3. build & start docker container: `docker compose up -d`
    
    * The `cassandra` image takes a while until it will be correctly initiated. To assure that this is up and running among the logs the *"Created default superuser role 'cassandra'"* message should appear.

    * The data ingestion from Finnhub starts only after the `stockapp` keyspace in `cassandra` is initiated.

4. navigate to http://localhost:3000/dashboards and open the `Stock - dashboard` Grafana dashboard and make sure to select the wanted stock's symbol in the upper ribbon from `Stock Symbol` drop-down.

    As soon as the database is available, the data from Finnhub will be pulled, processed and visualized. The automatic refresh is 5s, so please refresh the Grafana dashboard manually if refresh is needed more often.

7. Do not forget to stop the containers if not in use anymore.