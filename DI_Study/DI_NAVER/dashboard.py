import streamlit as st
import pandas as pd
import plotly.express as px
from database import get_db
from models import NewsData, TrendData
from sqlalchemy.orm import Session
import datetime

# Page Config
st.set_page_config(page_title="Naver API Dashboard", layout="wide")

st.title("📊 Naver API Pipeline Dashboard")

# Sidebar
st.sidebar.header("Options")
refresh_btn = st.sidebar.button("Refresh Data")

def load_news(db: Session):
    return db.query(NewsData).order_by(NewsData.collected_at.desc()).limit(100).all()

def load_trends(db: Session, keyword=None):
    query = db.query(TrendData)
    if keyword:
        query = query.filter(TrendData.group_name == keyword)
    return query.all()

def run_pipeline_script(keyword):
    import subprocess
    import sys
    # Running main.py as a subprocess to trigger data collection
    try:
        result = subprocess.run([sys.executable, "main.py", keyword], capture_output=True, text=True)
        return result.stdout, result.stderr
    except Exception as e:
        return None, str(e)

# Main UI
tab1, tab2, tab3 = st.tabs(["Search & Collect", "News Data", "Trend Analysis"])

with tab1:
    st.header("Search & Collect Data")
    keyword = st.text_input("Enter Keyword", value="생성형 AI")
    if st.button("Run Pipeline"):
        with st.spinner(f"Running pipeline for '{keyword}'..."):
            # Using the same venv python
            import sys
            import os
            python_path = sys.executable
            # If running from streamlit, sys.executable might be the venv one if launched via `./venv/bin/streamlit run`
            
            # Simple assumption/hack: we are in the root dir
            cmd = f"./venv/bin/python3 main.py \"{keyword}\""
            st.code(cmd, language="bash")
            
            import subprocess
            process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = process.communicate()
            
            if process.returncode == 0:
                st.success("Pipeline executed successfully!")
                st.text_area("Output", stdout.decode())
            else:
                st.error("Pipeline failed!")
                st.text_area("Error", stderr.decode())

with tab2:
    st.header("📰 Collected News")
    db = next(get_db())
    news_items = load_news(db)
    
    if news_items:
        data = [{
            "Title": item.title.replace("<b>", "").replace("</b>", "").replace("&quot;", "\""),
            "Date": item.pub_date,
            "Keyword": item.keyword,
            "Link": item.link
        } for item in news_items]
        
        df_news = pd.DataFrame(data)
        st.dataframe(df_news, use_container_width=True)
    else:
        st.info("No news data found.")

with tab3:
    st.header("📈 Trend Analysis")
    db = next(get_db())
    trends = load_trends(db)
    
    if trends:
        data = [{
            "Date": item.data_date,
            "Ratio": item.ratio,
            "Keyword": item.group_name
        } for item in trends]
        
        df_trend = pd.DataFrame(data)
        
        # Line Chart
        fig = px.line(df_trend, x="Date", y="Ratio", color="Keyword", title="Search Trends over Time")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No trend data found.")
