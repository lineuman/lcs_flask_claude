
source venv/bin/activate

gunicorn  run:app --workers 3 --timeout 120