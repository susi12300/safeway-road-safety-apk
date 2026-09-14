import requests
import time
import os


# =====================================================
# SETTINGS
# =====================================================

WEATHER_URL = "https://api.openweathermap.org/data/2.5/weather"

# Cache weather data for 5 minutes
CACHE_DURATION = 300

_weather_cache = {}


# =====================================================
# GET API KEY
# =====================================================

OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")


# =====================================================
# CONVERT OPENWEATHER CONDITION
# =====================================================

def weather_code_to_text(weather_id):

    if 200 <= weather_id <= 232:
        return "storm"

    elif 300 <= weather_id <= 321:
        return "rain"

    elif 500 <= weather_id <= 531:
        return "rain"

    elif 600 <= weather_id <= 622:
        return "snow"

    elif 701 <= weather_id <= 781:
        return "fog"

    elif 800 <= weather_id <= 804:
        return "clear"

    else:
        return "clear"


# =====================================================
# CACHE KEY
# =====================================================

def create_cache_key(points):

    return tuple(
        (
            round(point[1], 3),
            round(point[0], 3)
        )
        for point in points
    )


# =====================================================
# GET WEATHER FOR ONE LOCATION
# =====================================================

def get_weather(latitude, longitude):

    if not OPENWEATHER_API_KEY:
        raise RuntimeError(
            "OPENWEATHER_API_KEY is not configured."
        )

    parameters = {
        "lat": latitude,
        "lon": longitude,
        "appid": OPENWEATHER_API_KEY,
        "units": "metric"
    }

    headers = {
        "User-Agent": "SafeWay-Road-Safety-Project/1.0"
    }

    response = requests.get(
        WEATHER_URL,
        params=parameters,
        headers=headers,
        timeout=5
    )

    response.raise_for_status()

    data = response.json()

    temperature = data["main"]["temp"]

    weather_id = data["weather"][0]["id"]

    weather = weather_code_to_text(
        weather_id
    )

    return {
        "temperature": temperature,
        "weather": weather
    }


# =====================================================
# GET WEATHER FOR ROUTE
# =====================================================

def get_route_weather(route_points):

    if not route_points:
        return []

    number_of_points = len(route_points)

    # -------------------------------------------------
    # ONLY 3 WEATHER LOCATIONS
    #
    # 1. Source
    # 2. Midpoint
    # 3. Destination
    # -------------------------------------------------

    sample_indexes = [
        0,
        number_of_points // 2,
        number_of_points - 1
    ]

    # Remove duplicates for very short routes
    sample_indexes = list(
        dict.fromkeys(sample_indexes)
    )

    selected_points = [
        route_points[index]
        for index in sample_indexes
    ]

    print(
        f"Weather locations selected: "
        f"{len(selected_points)}"
    )

    # -------------------------------------------------
    # CHECK CACHE
    # -------------------------------------------------

    cache_key = create_cache_key(
        selected_points
    )

    current_time = time.time()

    if cache_key in _weather_cache:

        cached = _weather_cache[cache_key]

        if (
            current_time - cached["time"]
            < CACHE_DURATION
        ):

            print(
                "Using cached weather data."
            )

            return cached["weather"]

    # -------------------------------------------------
    # GET LIVE WEATHER
    # -------------------------------------------------

    weather_results = []

    try:

        for point_number, point in enumerate(
            selected_points,
            start=1
        ):

            longitude = point[0]
            latitude = point[1]

            print(
                f"Weather request "
                f"{point_number}/{len(selected_points)}: "
                f"{latitude}, {longitude}"
            )

            weather_data = get_weather(
                latitude,
                longitude
            )

            weather_results.append({

                "latitude": latitude,

                "longitude": longitude,

                "temperature":
                    weather_data["temperature"],

                "weather":
                    weather_data["weather"],

                "weather_source":
                    "live"
            })

    except Exception as e:

        print(
            "OpenWeather unavailable:",
            repr(e)
        )

        print(
            "Using default weather conditions."
        )

        # -------------------------------------------------
        # DEFAULT WEATHER FALLBACK
        # -------------------------------------------------

        weather_results = []

        for fallback_point in selected_points:

            weather_results.append({

                "latitude":
                    fallback_point[1],

                "longitude":
                    fallback_point[0],

                "temperature":
                    30.0,

                "weather":
                    "clear",

                "weather_source":
                    "default"
            })

    # -------------------------------------------------
    # SAVE RESULT TO CACHE
    # -------------------------------------------------

    _weather_cache[cache_key] = {

        "time": time.time(),

        "weather": weather_results
    }

    # -------------------------------------------------
    # PRINT SOURCE
    # -------------------------------------------------

    if weather_results:

        source = weather_results[0][
            "weather_source"
        ]

        if source == "live":

            print(
                "Weather source: LIVE"
            )

        else:

            print(
                "Weather source: DEFAULT"
            )

    return weather_results


# =====================================================
# GET OVERALL ROUTE WEATHER
# =====================================================

def get_overall_route_weather(route_points):

    weather_results = get_route_weather(
        route_points
    )

    if not weather_results:

        raise RuntimeError(
            "No weather data available."
        )

    # -------------------------------------------------
    # AVERAGE TEMPERATURE
    # -------------------------------------------------

    temperatures = [
        item["temperature"]
        for item in weather_results
    ]

    average_temperature = round(
        sum(temperatures)
        /
        len(temperatures),
        2
    )

    # -------------------------------------------------
    # WEATHER
    # -------------------------------------------------

    weather_list = [
        item["weather"]
        for item in weather_results
    ]

    if "storm" in weather_list:

        overall_weather = "storm"

    elif "rain" in weather_list:

        overall_weather = "rain"

    elif "snow" in weather_list:

        overall_weather = "snow"

    elif "fog" in weather_list:

        overall_weather = "fog"

    else:

        overall_weather = "clear"

    # -------------------------------------------------
    # WEATHER SOURCE
    # -------------------------------------------------

    weather_source = weather_results[0][
        "weather_source"
    ]

    return {

        "overall_weather":
            overall_weather,

        "average_temperature":
            average_temperature,

        "weather_source":
            weather_source
    }