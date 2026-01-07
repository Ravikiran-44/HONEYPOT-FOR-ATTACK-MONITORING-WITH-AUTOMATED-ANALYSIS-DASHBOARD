@echo off
REM Activate venv and run three processes: orchestrator, streamlit, and test client
REM Adjust python path if needed.

setlocal

REM 1) activate venv
call "%~dp0\venv\Scripts\activate.bat"

REM 2) start orchestrator in a new window
start "Orchestrator" cmd /k "cd /d %~dp0 && python -u -m src.orchestrator_runner"

REM 3) start streamlit (host on 127.0.0.1)
start "Streamlit" cmd /k "cd /d %~dp0 && streamlit run streamlit_app.py --server.port 8501 --server.address 127.0.0.1"

REM 4) wait a few seconds then run test client to create a session
timeout /t 3 /nobreak >nul
python -u test_client_interactive.py

echo.
echo Demo started. Open http://localhost:8501
pause
endlocal
