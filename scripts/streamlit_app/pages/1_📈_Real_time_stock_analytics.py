import streamlit as st
import stockapp_utils
import time
import pandas as pd
import altair as alt
from pyspark.sql import SparkSession
from datetime import datetime, timedelta


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
            st.text(f"🔐 Security: {stock_line.Security}")
            st.text(f"📊 Index: {stock_line.Index}")
            st.text(f"🏢 Sector: {stock_line.Sector}")

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

                st.subheader("Last minute at a glance")

                current_mean_price = round(trades_df['price'].mean(), 2)
                thirty_seconds_ago = datetime.now() - timedelta(seconds=30)
                mean_price_seconds_ago = round(trades_df[trades_df['ts'] > thirty_seconds_ago]['price'].mean(), 2)
                delta_mean_price = round((current_mean_price - mean_price_seconds_ago), 2)

                #TODO: calculate
                kpis1 = st.columns(3)
                kpis1[0].metric(
                    label="Min price",
                    value=round(trades_df['price'].min(),2)
                )
                kpis1[1].metric(
                    label="Mean price",
                    value=round(trades_df['price'].mean(), 2),
                    delta=f"{delta_mean_price}"
                )
                kpis1[2].metric(
                    label="Max price",
                    value=round(trades_df['price'].max(), 2)
                )

                current_mean_volume = round(trades_df['volume'].mean(), 2)
                mean_volume_seconds_ago = round(trades_df[trades_df['ts'] > thirty_seconds_ago]['volume'].mean(), 2)
                delta_mean_volume = round((current_mean_volume - mean_volume_seconds_ago), 2)
 
                kpis2 = st.columns(3)
                kpis2[0].metric(
                    label="Min volume",
                    value=trades_df['volume'].min()
                )
                kpis2[1].metric(
                    label="Mean volume",
                    value=round(trades_df['volume'].mean(), 2),
                    delta=f"{delta_mean_volume}"
                )
                kpis2[2].metric(
                    label="Max volume",
                    value=trades_df['volume'].max()
                )
                st.subheader(" Analytics")

                # Price chart
                st.markdown("### Real-Time Stock Price Evolution")
               
                min_price = trades_df['price'].min()
                max_price = trades_df['price'].max()

                # Altair chart
                line_chart = alt.Chart(trades_df).mark_line(color='blue').encode(
                    #x='ts',
                    x = alt.X('ts', axis=alt.Axis(title="Time")),
                    y=alt.Y('price', scale=alt.Scale(domain=(min_price, max_price))),
                    tooltip=['ts:T', 'price:Q'],
                ).properties(
                    width=800,
                    height=400,
                )

                st.altair_chart(line_chart, use_container_width=True)

                # Volume chart
                st.markdown("### Trade Volume Evolution")
                
                min_volume = trades_df['volume'].min()
                max_volume = trades_df['volume'].max()

                # Altair chart
                bar_chart = alt.Chart(trades_df).mark_bar(color='blue').encode(
                    x = alt.X('ts', axis=alt.Axis(title="Time")),
                    y=alt.Y('volume', scale=alt.Scale(domain=(min_volume, max_volume))),
                    tooltip=['volume:Q'],
                ).properties(
                    width=800,
                    height=400,
                )

                st.altair_chart(bar_chart, use_container_width=True)
            else:
                st.write("No trade data")
        time.sleep(5)