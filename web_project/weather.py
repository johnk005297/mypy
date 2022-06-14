import requests

def city_weather(city_name):
    url = "http://api.worldweatheronline.com/premium/v1/weather.ashx"    
    params = {
        "key": "13af0d7e577b4c65997205618212909",
        "q": city_name,
        "format": "json",
        "num_of_days": 1,
        "lang": "ru"
    }
    try:
        resp = requests.get(url, params=params)
        resp.raise_for_status()
        weather = resp.json()
        if "data" in weather:
            if "current_condition" in weather["data"]:
                try:                    
                    return weather["data"]["current_condition"][0]                    
                except(IndexError, TypeError):
                    return False                
    except(requests.RequestException, ValueError):
        print("Network Error")
        return False
    return False

if __name__ == "__main__":
    print(city_weather("Moscow,Russia"))
    