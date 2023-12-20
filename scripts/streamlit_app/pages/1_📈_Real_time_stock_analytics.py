import streamlit as st
import stockapp_utils
import time
import pandas as pd
from pyspark.sql import SparkSession


# set the icon and title appearing in browser
stockapp_utils.setup_page()

# TODO: set the title of the page
page_title = st.title("👈 Choose a stock from the sidebar to begin!")

spark_hive = None

with st.sidebar:
    
    with st.status("Fetching data...", expanded=True) as status:
        st.write("Connecting to Cassandra...")
        cassandra_conn = stockapp_utils.cassandra_connection()
        st.write("Getting stock data...")
        spark_hive = stockapp_utils.get_hive_connection()
        stockapp_utils.create_hive_tables(spark_hive)
        stocks_df = stockapp_utils.get_index_and_stocks(spark_hive)
        indexes = [row.Symbol + ' (' + row.Security + ') - ' + row.Index for row in stocks_df\
                                                            .select(['Symbol', 'Security', 'Index']) \
                                                            .distinct() \
                                                            .sort("Symbol", ascending=True) \
                                                            .collect()]
        status.update(label="Data fetched", state="complete", expanded=False)

    sidebar_stock_selectbox = st.selectbox(
            label="Choose the stock",
            options=indexes,
            index=None
        )
    
# st.write(f"Stock chosen: {sidebar_stock_selectbox}")
if sidebar_stock_selectbox:

    stock = sidebar_stock_selectbox.split(" ")[0]
    stock_line = stocks_df.filter(stocks_df.Symbol == stock).collect()[0]
    real_time_charts = st.empty()

    while True:

        with real_time_charts.container():

            page_title.empty()
            page_title.title(f"📈 Real-time trade analytics of :blue[{stock}]")

            st.subheader("About")
            st.text(f"Security: {stock_line.Security}")
            st.text(f"Index: {stock_line.Index}")
            st.text(f"Sector: {stock_line.Sector}")

            trades = cassandra_conn.execute(f"SELECT * FROM stockapp.trades where symbol = '{stock}';")
            trade_list = []
            for row in trades:
                trade_list.append({
                    'ts': row.ts,
                    'price': row.price,
                    'volume': row.volume
                })
            if trade_list != []:
                trades_df = pd.DataFrame(trade_list)
                trades_df['volume'] = trades_df.volume.astype(int)
                trades_df['price'] = trades_df.price.astype(float)

                # st.write(trades_df)

                st.subheader("Last hour at a glance")

                #TODO: calculate
                kpis = st.columns(3)
                kpis[0].metric(
                    label="mean price",
                    value=10
                )
                kpis[1].metric(
                    label="mean volume",
                    value=10
                )
                kpis[2].metric(
                    label="mean volume",
                    value=100
                )

                st.subheader("Analytics")

                st.markdown("Price evolution")
                line_chart = st.line_chart(
                    data=trades_df,
                    x="ts",
                    y="price"
                )
                st.markdown("Volume evolution")
                line_chart = st.line_chart(
                    data=trades_df,
                    x="ts",
                    y="volume"
                )
            else:
                st.write("No trade data")
        time.sleep(5)