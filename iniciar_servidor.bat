@echo off
echo Iniciando Servidor Backend MusicPro...
start "Backend FastAPI" cmd /k "cd backend && python -m uvicorn main:app --reload"

echo Iniciando Tunel de Conexion Permanente...
echo Tu servidor estara disponible en todo el mundo a traves de:
echo https://musicapro-fernando.loca.lt
start "Tunel Localtunnel" cmd /k "npx localtunnel --port 8000 --subdomain musicapro-fernando"

echo.
echo Presiona cualquier tecla para salir...
pause >nul
