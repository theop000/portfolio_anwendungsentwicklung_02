1. Anwendung starten:

docker build -t weather-app . && docker run -p 8050:8050 weather-app

2. Browser öffnen:

http://localhost:8050


Funktionen testen:

pytest test_data.py -v --capture=no
pytest test_main.py -v --capture=no
