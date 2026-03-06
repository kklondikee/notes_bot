import httpx
from open_meteo import OpenMeteo
from open_meteo.models import DailyParameters, HourlyParameters

async def get_weather(city: str):
    """
    Получает погоду и часовой пояс для указанного города.
    Возвращает (weather_data, timezone, geo_options) или (None, None, None) при ошибке.
    Если geo_options не пуст, значит город неоднозначен и нужно выбирать.
    """
    try:
        async with httpx.AsyncClient() as client:
            geo_response = await client.get(
                "https://nominatim.openstreetmap.org/search",
                params={
                    "q": city,
                    "format": "json",
                    "limit": 5,
                },
                headers={"User-Agent": "NotesBot/1.0"}
            )
            geo_data = geo_response.json()
            if not geo_data:
                return None, None, None

        if len(geo_data) > 1:
            geo_options = []
            for idx, place in enumerate(geo_data):
                display_name = place.get("display_name", city)
                short_name = display_name[:50] + "..." if len(display_name) > 50 else display_name
                geo_options.append({
                    "id": idx,
                    "lat": float(place["lat"]),
                    "lon": float(place["lon"]),
                    "name": short_name,
                    "full_name": display_name,
                })
            return None, None, geo_options

        # Единственный вариант
        lat = float(geo_data[0]["lat"])
        lon = float(geo_data[0]["lon"])
        display_name = geo_data[0]["display_name"].split(",")[0]

        # Получаем погоду через Open-Meteo
        async with OpenMeteo() as open_meteo:
            forecast = await open_meteo.forecast(
                latitude=lat,
                longitude=lon,
                current_weather=True,
                daily=[
                    DailyParameters.SUNRISE,
                    DailyParameters.SUNSET,
                    DailyParameters.TEMPERATURE_2M_MAX,
                    DailyParameters.TEMPERATURE_2M_MIN,
                    DailyParameters.PRECIPITATION_SUM,
                    DailyParameters.WIND_SPEED_10M_MAX,
                ],
                hourly=[
                    HourlyParameters.TEMPERATURE_2M,
                    HourlyParameters.RELATIVE_HUMIDITY_2M,
                    HourlyParameters.WIND_SPEED_10M,
                    HourlyParameters.PRECIPITATION,
                ],
                timezone="auto"
            )

        current = forecast.current_weather
        if not current:
            return None, None, None

        timezone = forecast.timezone
        daily = forecast.daily
        hourly = forecast.hourly

        weather_code = current.weathercode
        icon = get_weather_icon(weather_code)
        temp = current.temperature
        wind_speed = current.windspeed

        max_temp = round(daily.temperature_2m_max[0]) if daily.temperature_2m_max else None
        min_temp = round(daily.temperature_2m_min[0]) if daily.temperature_2m_min else None
        precipitation = daily.precipitation_sum[0] if daily.precipitation_sum else 0
        sunrise = daily.sunrise[0].strftime("%H:%M") if daily.sunrise else None
        sunset = daily.sunset[0].strftime("%H:%M") if daily.sunset else None

        humidity = None
        if hourly and hasattr(hourly, 'relative_humidity_2m') and hourly.relative_humidity_2m:
            humidity = hourly.relative_humidity_2m[0]

        weather_data = {
            "city": display_name,
            "icon": icon,
            "temperature": round(temp),
            "humidity": humidity,
            "wind_speed": round(wind_speed),
            "description": get_weather_description(weather_code),
            "max_temp": max_temp,
            "min_temp": min_temp,
            "precipitation": precipitation,
            "sunrise": sunrise,
            "sunset": sunset,
            "clothing_advice": get_clothing_advice(temp, weather_code),
        }
        return weather_data, timezone, None

    except Exception as e:
        print(f"Ошибка при получении погоды: {e}")
        import traceback
        traceback.print_exc()
        return None, None, None

async def get_weather_by_coords(lat: float, lon: float, city_name: str = None):
    """Получает погоду по координатам. city_name используется для отображения."""
    try:
        async with OpenMeteo() as open_meteo:
            forecast = await open_meteo.forecast(
                latitude=lat,
                longitude=lon,
                current_weather=True,
                daily=[
                    DailyParameters.SUNRISE,
                    DailyParameters.SUNSET,
                    DailyParameters.TEMPERATURE_2M_MAX,
                    DailyParameters.TEMPERATURE_2M_MIN,
                    DailyParameters.PRECIPITATION_SUM,
                    DailyParameters.WIND_SPEED_10M_MAX,
                ],
                hourly=[
                    HourlyParameters.TEMPERATURE_2M,
                    HourlyParameters.RELATIVE_HUMIDITY_2M,
                    HourlyParameters.WIND_SPEED_10M,
                    HourlyParameters.PRECIPITATION,
                ],
                timezone="auto"
            )

        current = forecast.current_weather
        if not current:
            return None, None

        timezone = forecast.timezone
        daily = forecast.daily
        hourly = forecast.hourly

        weather_code = current.weathercode
        icon = get_weather_icon(weather_code)
        temp = current.temperature
        wind_speed = current.windspeed

        max_temp = round(daily.temperature_2m_max[0]) if daily.temperature_2m_max else None
        min_temp = round(daily.temperature_2m_min[0]) if daily.temperature_2m_min else None
        precipitation = daily.precipitation_sum[0] if daily.precipitation_sum else 0
        sunrise = daily.sunrise[0].strftime("%H:%M") if daily.sunrise else None
        sunset = daily.sunset[0].strftime("%H:%M") if daily.sunset else None

        humidity = None
        if hourly and hasattr(hourly, 'relative_humidity_2m') and hourly.relative_humidity_2m:
            humidity = hourly.relative_humidity_2m[0]

        weather_data = {
            "city": city_name or "Неизвестно",
            "icon": icon,
            "temperature": round(temp),
            "humidity": humidity,
            "wind_speed": round(wind_speed),
            "description": get_weather_description(weather_code),
            "max_temp": max_temp,
            "min_temp": min_temp,
            "precipitation": precipitation,
            "sunrise": sunrise,
            "sunset": sunset,
            "clothing_advice": get_clothing_advice(temp, weather_code),
        }
        return weather_data, timezone

    except Exception as e:
        print(f"Ошибка при получении погоды по координатам: {e}")
        return None, None

# --- Вспомогательные функции ---

def get_weather_icon(code: int) -> str:
    if code == 0:
        return "☀️"
    elif code == 1:
        return "🌤"
    elif code == 2:
        return "⛅"
    elif code == 3:
        return "☁️"
    elif 45 <= code <= 48:
        return "🌫"
    elif 51 <= code <= 55:
        return "🌧"
    elif 56 <= code <= 57:
        return "🌨"
    elif 61 <= code <= 65:
        return "🌧"
    elif 66 <= code <= 67:
        return "🌨"
    elif 71 <= code <= 77:
        return "❄️"
    elif 80 <= code <= 82:
        return "🌧"
    elif 85 <= code <= 86:
        return "❄️"
    elif code == 95:
        return "⛈"
    elif code >= 96:
        return "⛈"
    return "☀️"

def get_weather_description(code: int) -> str:
    descriptions = {
        0: "Ясно",
        1: "Преимущественно ясно",
        2: "Переменная облачность",
        3: "Пасмурно",
        45: "Туман",
        48: "Изморозь",
        51: "Легкая морось",
        53: "Морось",
        55: "Сильная морось",
        56: "Легкая ледяная морось",
        57: "Ледяная морось",
        61: "Небольшой дождь",
        63: "Дождь",
        65: "Сильный дождь",
        66: "Легкий ледяной дождь",
        67: "Ледяной дождь",
        71: "Небольшой снег",
        73: "Снег",
        75: "Сильный снег",
        77: "Снежная крупа",
        80: "Ливень",
        81: "Сильный ливень",
        82: "Шквал",
        85: "Снегопад",
        86: "Сильный снегопад",
        95: "Гроза",
        96: "Гроза с градом",
        99: "Сильная гроза с градом",
    }
    return descriptions.get(code, "Неизвестно")

def get_clothing_advice(temp: float, code: int) -> str:
    if temp < -20:
        base = "🥶 Очень холодно! Одевайтесь максимально тепло: пуховик, шапка, шарф, варежки."
    elif temp < -10:
        base = "❄️ Холодно. Нужна зимняя куртка, шапка и перчатки."
    elif temp < 0:
        base = "🌨 Прохладно. Куртка, свитер, шапка не помешает."
    elif temp < 10:
        base = "🍂 Свежо. Ветровка или лёгкая куртка, свитер."
    elif temp < 18:
        base = "🍃 Прохладно. Кофта или лёгкая куртка."
    elif temp < 25:
        base = "🌤 Тепло. Футболка, джинсы, лёгкая обувь."
    elif temp < 30:
        base = "☀️ Жарко. Лёгкая одежда, головной убор, вода."
    else:
        base = "🔥 Очень жарко! Лёгкая одежда, избегайте солнца."

    if code in [61, 63, 65, 80, 81, 82]:
        base += " Не забудьте зонт! ☔"
    elif code in [71, 73, 75, 85, 86]:
        base += " Идёт снег — одевайтесь теплее и будьте осторожны на дорогах. ❄️"
    elif code in [95, 96, 99]:
        base += " Гроза! Лучше остаться дома. ⛈"

    return base