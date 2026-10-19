@echo off
cd /d "%~dp0"
echo Starting Moxin Streamlit portal...
"D:\anconda\python.exe" -m streamlit run Home.py --server.port 8501 --server.address 127.0.0.1
pause
