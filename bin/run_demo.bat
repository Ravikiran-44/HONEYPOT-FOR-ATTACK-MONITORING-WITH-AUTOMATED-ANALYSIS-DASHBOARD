@echo off
REM Copy of top-level run_demo.bat for convenience in bin/
setlocal
call "%~dp0\..\venv\Scripts\activate.bat"
start "Orchestrator" cmd /k "cd /d %~dp0\.. && python -u -m src.orchestrator_runner"
start "Streamlit" cmd /k "cd /d %~dp0\.. && streamlit run src/app_auto.py --server.port 8501 --server.address 127.0.0.1"
timeout /t 3 /nobreak >nul
python -u ..\test_client_interactive.py
echo.
echo Demo started. Open http://localhost:8501
endlocal