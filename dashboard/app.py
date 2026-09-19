"""Streamlit entry point for the IT Job Skill Analytics dashboard."""

import streamlit as st


st.set_page_config(
    page_title="IT Job Skill Analytics",
    page_icon="📊",
    layout="wide",
)

st.title("IT Job Skill Analytics")
st.caption("Big Data analytics and skill-demand forecasting for the IT job market.")

st.info(
    "Dashboard scaffold initialized. Market Overview, Skill Analytics, "
    "Job Comparison, Skill Trend, and Forecast pages will be added as the "
    "Gold-layer datasets become available."
)
