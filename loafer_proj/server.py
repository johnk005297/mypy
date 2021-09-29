from flask import Flask
from weather import city_weather

app = Flask(__name__)

@app.route('/')
def index():
    weather = city_weather("Moscow,Russia")    
    if weather:
        return f"Weather in Moscow: {weather['temp_C']}, feels like {weather['FeelsLikeC']}"
    else:
        return "Service error"

if __name__ == "__main__":
    app.run()

