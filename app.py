# app.py
import streamlit as st
import pandas as pd
from utils import *

st.title("SQL Chat Assistant")

user_input = st.text_input("Ask me")

if user_input:
    with st.chat_message("assistant"):
        data, chart = sql_agent(user_input)

        if data:
            st.write("### Table Output")
            st.dataframe(pd.DataFrame(data))
        
        st.write("### Chart Suggestions", chart)
        if chart["chart"] == "bar_chart":
            st.bar_chart(pd.DataFrame(data)[chart["x"]])
            # plot bar chart
            
        elif chart["chart"] == "line_chart":
            # plot bar chart
            st.line_chart(data[chart["x"]], data[chart["y"]])
            
        elif chart["chart"] == "pie_chart":
            # plot bar chart
            st.pie_chart(pd.DataFrame(data)[chart["x"]])
            
        else:
            st.write("No chart suggestion is required")
            
