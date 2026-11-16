@echo off
cd "C:\Users\Vasu\Documents\VS_CODE\PY_PROJ\Placement_Portal_DBMS"
start streamlit run streamlit_dashboard.py --server.headless true --server.port 8504 --server.baseUrlPath "/" --server.gatherUsageStats false
timeout /t 3 /wait