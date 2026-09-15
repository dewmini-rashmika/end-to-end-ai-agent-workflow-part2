@echo off
setlocal

set BACKEND=c:\Users\USER\Desktop\Agentic_ai\projects\end-to-end-ai-agent-workflow-part2\backend
set FRONTEND=c:\Users\USER\Desktop\Agentic_ai\projects\end-to-end-ai-agent-workflow-part2\frontend
set VENV=%BACKEND%\venv\Scripts
set LOGS=%BACKEND%\logs

:: Create logs dir
if not exist "%LOGS%" mkdir "%LOGS%"

echo.
echo =====================================================
echo   TripMate AI - Starting All Services
echo =====================================================
echo.

echo [1/6] Starting MCP Flight Server (port 8001)...
start "MCP-Flight" /MIN cmd /c "cd /d %BACKEND% && %VENV%\python.exe -m app.mcp_servers.flight_mcp > %LOGS%\mcp_flight.log 2>&1"

timeout /t 1 /nobreak > nul

echo [2/6] Starting MCP Hotel Server (port 8002)...
start "MCP-Hotel" /MIN cmd /c "cd /d %BACKEND% && %VENV%\python.exe -m app.mcp_servers.hotel_mcp > %LOGS%\mcp_hotel.log 2>&1"

timeout /t 1 /nobreak > nul

echo [3/6] Starting MCP Weather Server (port 8003)...
start "MCP-Weather" /MIN cmd /c "cd /d %BACKEND% && %VENV%\python.exe -m app.mcp_servers.weather_mcp > %LOGS%\mcp_weather.log 2>&1"

timeout /t 1 /nobreak > nul

echo [4/6] Starting MCP Budget Server (port 8004)...
start "MCP-Budget" /MIN cmd /c "cd /d %BACKEND% && %VENV%\python.exe -m app.mcp_servers.budget_mcp > %LOGS%\mcp_budget.log 2>&1"

timeout /t 2 /nobreak > nul

echo [5/6] Starting FastAPI Backend (port 8000)...
start "TripMate-Backend" cmd /c "cd /d %BACKEND% && %VENV%\uvicorn.exe app.main:app --reload --host 0.0.0.0 --port 8000 --log-level debug"

timeout /t 3 /nobreak > nul

echo [6/6] Starting React Frontend (port 5173)...
start "TripMate-Frontend" cmd /c "cd /d %FRONTEND% && npm run dev"

echo.
echo =====================================================
echo   All services started!
echo.
echo   Frontend:    http://localhost:5173
echo   Backend API: http://localhost:8000
echo   API Docs:    http://localhost:8000/docs
echo   Health:      http://localhost:8000/health
echo.
echo   MCP Servers: 8001 8002 8003 8004
echo =====================================================
echo.
echo Press any key to open the app in your browser...
pause > nul
start http://localhost:5173
