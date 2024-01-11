import streamlit as st
import pickle

forecast_btn = st.button('Forecast')
predicted_value = None

if forecast_btn:
    # here the trades_df (or whatever the name of the df in the batchlayer page will be) can be used;
    model = pickle.load(open("/model.sav", "rb"))
    predicted_value = model.predict([[10]])[0]

result = st.write(predicted_value) if predicted_value else None

