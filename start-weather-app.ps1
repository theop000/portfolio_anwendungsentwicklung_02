# to start the app, download this powershell script and execute it in the appropriate directory
# with the command below:
# "   .\start-weather-app.ps1"
git clone https://github.com/theop000/portfolio_anwendungsentwicklung_02; cd portfolio_anwendungsentwicklung_02; docker build -t weather-app .; docker run -p 8050:8050 weather-app