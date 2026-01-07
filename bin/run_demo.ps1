# Copy of root run_demo.ps1 placed into bin for convenience
PowerShell -NoExit -Command "& {cd \"%~dp0..\"; . .\venv\Scripts\Activate.ps1; python -m src.orchestrator_runner }" 
Start-Process powershell -ArgumentList "-NoExit","-Command","cd \"%~dp0..\"; . .\venv\Scripts\Activate.ps1; streamlit run src/app_auto.py --server.port 8501 --server.address 127.0.0.1"
Start-Sleep -Seconds 3
powershell -NoExit -Command "& {cd \"%~dp0..\"; . .\venv\Scripts\Activate.ps1; python test_client_interactive.py }"
