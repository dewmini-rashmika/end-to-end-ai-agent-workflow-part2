@echo off
echo ============================================================
echo  TripMate AI - Full Setup Script
echo ============================================================

set BACKEND=c:\Users\USER\Desktop\Agentic_ai\projects\end-to-end-ai-agent-workflow-part2\backend
set FRONTEND=c:\Users\USER\Desktop\Agentic_ai\projects\end-to-end-ai-agent-workflow-part2\frontend
set PYTHON=C:\Users\USER\AppData\Local\Programs\Python\Python310\python.exe
set VENV=%BACKEND%\venv\Scripts

echo.
echo [1/6] Recreating Python virtual environment...
rmdir /s /q "%BACKEND%\venv" 2>nul
"%PYTHON%" -m venv "%BACKEND%\venv"
if %errorlevel% neq 0 (echo ERROR creating venv & pause & exit /b 1)
echo     DONE - venv created

echo.
echo [2/6] Upgrading pip...
"%VENV%\python.exe" -m pip install --upgrade pip --quiet
echo     DONE

echo.
echo [3/6] Installing core packages (fastapi, sqlalchemy, auth, etc.)...
"%VENV%\pip.exe" install ^
    "fastapi==0.115.5" ^
    "uvicorn[standard]==0.32.1" ^
    "python-multipart==0.0.18" ^
    "sqlalchemy==2.0.36" ^
    "asyncpg==0.30.0" ^
    "alembic==1.14.0" ^
    "python-jose[cryptography]==3.3.0" ^
    "passlib[bcrypt]==1.7.4" ^
    "pydantic==2.10.3" ^
    "pydantic-settings==2.6.1" ^
    "email-validator==2.2.0" ^
    "httpx==0.28.1" ^
    "slowapi==0.1.9" ^
    "redis==5.2.1" ^
    "structlog==24.4.0"
if %errorlevel% neq 0 (echo ERROR installing core packages & pause & exit /b 1)
echo     DONE - core packages installed

echo.
echo [4/6] Installing LiteLLM + OpenAI (large download, be patient)...
"%VENV%\pip.exe" install "litellm==1.55.3" "openai==1.57.2"
if %errorlevel% neq 0 (echo ERROR installing litellm & pause & exit /b 1)
echo     DONE - LiteLLM installed

echo.
echo [5/6] Installing FastMCP + ChromaDB...
"%VENV%\pip.exe" install "fastmcp==2.3.4"
if %errorlevel% neq 0 (echo WARNING: fastmcp install issue, trying alternative version...)
"%VENV%\pip.exe" install fastmcp
"%VENV%\pip.exe" install "chromadb==0.6.3"
if %errorlevel% neq 0 (
    echo WARNING: chromadb 0.6.3 failed, trying latest...
    "%VENV%\pip.exe" install chromadb
)
echo     DONE

echo.
echo [6/6] Verifying key packages...
"%VENV%\python.exe" -c "import fastapi; print('fastapi:', fastapi.__version__)"
"%VENV%\python.exe" -c "import alembic; print('alembic:', alembic.__version__)"
"%VENV%\python.exe" -c "import litellm; print('litellm: OK')"
"%VENV%\python.exe" -c "import sqlalchemy; print('sqlalchemy:', sqlalchemy.__version__)"

echo.
echo ============================================================
echo  Backend dependencies installed!
echo  Next: Install frontend dependencies
echo ============================================================
echo.
echo [Frontend] Installing npm packages...
cd /d "%FRONTEND%"
call npm install
if %errorlevel% neq 0 (echo ERROR in npm install & pause & exit /b 1)
echo     DONE - frontend packages installed

echo.
echo ============================================================
echo  ALL DONE! 
echo.
echo  Now you need to:
echo  1. Edit backend\.env and add your API keys
echo  2. Install + start PostgreSQL, Redis, ChromaDB (or Docker)
echo  3. Run: alembic upgrade head
echo  4. Start services (see README)
echo ============================================================
pause
