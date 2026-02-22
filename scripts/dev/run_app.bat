@echo off
echo Activiting virtual environment...
call venv\Scripts\activate

echo Installing dependencies...
pip install -r requirements.txt

echo Starting application...
python app.py
pause
