from pyspark.sql.functions import lit
from pyspark import pandas as pd

# get S&P500 stocks from https://en.wikipedia.org/wiki/List_of_S%26P_500_companies
sp_500_df = pd.read_html("https://en.wikipedia.org/wiki/List_of_S%26P_500_companies")[0]

# transform to spark dataframe
sp_500_sparkdf = sp_500_df[["Symbol", "Security", "GICS Sector"]].to_spark()

# rename columns & create a new one for index
sp_500_sparkdf = sp_500_sparkdf.withColumnRenamed("GICS Sector", "Sector") \
                               .withColumn("Index", lit("S&P500"))


# get NASDAQ100 stocks from "https://en.wikipedia.org/wiki/Nasdaq-100"
nasdaq = pd.read_html("https://en.wikipedia.org/wiki/Nasdaq-100")[4]

# transform to spark dataframe
nasdaq_sparkdf = nasdaq[["Ticker", "Company", "GICS Sector"]].to_spark()

# rename columns & create a new one for index
nasdaq_sparkdf = nasdaq_sparkdf.withColumnRenamed("Company", "Security") \
                               .withColumnRenamed("Ticker", "Symbol") \
                               .withColumnRenamed("GICS Sector", "Sector") \
                               .withColumn("Index", lit("NASDAQ"))

# unite S&P500 and NASDAQ dataframes
stocks = sp_500_sparkdf.union(nasdaq_sparkdf)

# export to Hadoop
stocks.write.mode('overwrite').parquet("hdfs://namenode:8020/data/stocks")