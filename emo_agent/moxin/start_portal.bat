@echo off
cd /d "%~dp0"
echo Starting Tingshan Streamlit portal...
"..\..\.venv\Scripts\python.exe" -m streamlit run Home.py --server.port 8501 --server.address 127.0.0.1
pause
