# Big Data Application - Real time stock analytics platform

## About the project
The application aims to provide a Big Data architecture use-case that implements batch and the speed layer. It consists of following parts:

1. Stock data and analytics 
    * the real-time datasource is trading data from [Finnhub](https://finnhub.io/docs/api/websocket-trades)
    * the data comming through a socket is processed with PySpark
    * the final sink is a Cassandra table
    * the reporting layer is realized in Grafana - currently it displays 3 chart visualization of the volumes

## Structure
The dockerized application currently consists of 3 images:
1. cassandra:4.1.3 - https://hub.docker.com/_/cassandra
    
    Each time when the container is started, the following cassandra objects are created *(`make-cassandra-tables.sh` file)*:
    * keyspace `stockapp` with *SimpleStrategy* replication of factor 1
    * table `trades` within `stockapp` keyspace with 4 columns:
        * `ts` TIMESTAMP
        * `symbol` VARCHAR
        * `price` DECIMAL
        * `volume` INT
    * the primary key consists from `(symbol, ts)`, this means that the `symbol` column is the partition row and `ts` the clustering key. *Obs. filtering only on these 2 columns is possible without ALLOW FILTERING option, that reduces the execution's efectiveness*

2. grafana/grafana:10.2.0 - https://hub.docker.com/r/grafana/grafana

    Grafana ingests data from Cassandra and currently makes 3 line visualizations for AALP, TSLA and GOOGL stocks

3. apache/spark-py:v3.4.0 - https://hub.docker.com/r/apache/spark-py

    The processing part is realized by using Apache Pyspark. Currently a Streaming Data Frame is initialized on the `/input` folder and a script processes from the JSON output a tabular output with following specifications *(`real_time_processing.py` file)*:
    * `ts` LongType()
    * `symbol` StringType()
    * `price` DecimalType(10,4)
    * `volume` IntegerType()

    *Obs. Please note that cassandra automatically makes the conversion between the ts bigint from PySpark and ts timestamp in Cassandra.*

4. `generate_random_json.ipynb`

    This notebook contains a logic that generates maximum 1000 random JSON files in the `input` folder. Each file will have the input format of JSON files processed within PySpark. This stucture is:

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

# How to use the application

1. git clone this repo: `git clone https://github.com/holgyeso/real-time-stock-app.git`
2. enter the downloaded folder: `cd real-time-stock-app`
3. build & start docker container: `docker compose up -d`
    
    The `cassandra` images takes a while until it will be correctly initiated. To assure that this is up and running among the logs the *"superuser role created"* message should appear.

    In the meanwhile, `pyspark` will exit with failure, because it cannot communicate with `cassandra`. Therefore, after `cassandra` is up and running, you should restart this container.

4. navigate to `localhost:3000`, enter admin username and admin password and open the `Stock - dashboard` Grafana dashboard, that should display 3 empty charts.

5. execute the cells from `generate_random_json.ipynb` that will generate in a loop JSON files into the `input` folder, that is mirrored to `/input` in the PySpark docker container.

6. Switch to Grafana, refresh data and enjoy how data is visualized in real time.

7. Do not forget to stop the while loop in `generate_random_json.ipynb`.