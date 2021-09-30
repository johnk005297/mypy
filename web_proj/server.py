from flask import Flask, render_template
from weather import city_weather

app = Flask(__name__)

@app.route('/')
def index():
    title = "Weather forecast"
    weather = city_weather("Moscow,Russia")   
    return render_template("index.html", page_title=title, weather_html=weather)
if __name__ == "__main__":
    app.run()

