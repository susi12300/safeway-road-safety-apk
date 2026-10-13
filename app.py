from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
import joblib
import requests

from danger_zone import check_danger_zone, generate_route_risk_zones
from route_service import get_route
from weather_service import get_overall_route_weather


app = Flask(__name__, static_folder="frontend", static_url_path="")
CORS(app)


# =====================================================
# LOAD ML MODEL
# =====================================================

model = joblib.load("road_risk_model.pkl")
current_risk_zones = []

# =====================================================
# HOME
# =====================================================


@app.route("/")
def home():
    return app.send_static_file("index.html")


# =====================================================
# GET ALL RISK ZONES
# =====================================================

@app.route("/risk-zones", methods=["GET"])
def risk_zones():

    return jsonify(
        current_risk_zones
    )

@app.route("/search-location")
def search_location():

    query = request.args.get("q", "").strip()

    if len(query) < 2:
        return jsonify([])

    try:

        url = "https://nominatim.openstreetmap.org/search"

        params = {
            "q": query,
            "format": "json",
            "limit": 8,
            "addressdetails": 1,
            "countrycodes": "in"
        }

        headers = {
            "User-Agent": "SafeWay-Road-Safety-Project/1.0"
        }

        response = requests.get(
            url,
            params=params,
            headers=headers,
            timeout=5
        )

        if response.status_code != 200:
            return jsonify([])

        results = response.json()

        suggestions = []

        for place in results:

            address = place.get("address", {})

            # Try to get a short useful name
            name = (
                address.get("city")
                or address.get("town")
                or address.get("municipality")
                or address.get("village")
                or place.get("display_name", "").split(",")[0]
            )

            state = address.get("state", "")
            country = address.get("country", "")

            suggestions.append({
                "name": name,
                "display": (
                    f"{name}, {state}"
                    if state
                    else name
                ),
                "latitude": float(place["lat"]),
                "longitude": float(place["lon"])
            })

        return jsonify(suggestions)

    except Exception as e:

        print("Location search error:", e)

        return jsonify([])
# =====================================================
# PREDICT ROUTE SAFETY
# =====================================================

@app.route("/predict", methods=["POST"])
def predict():
    try:
        # =================================================
        # GET USER INPUT
        # =================================================

        data = request.get_json()

        source = data.get("source")
        destination = data.get("destination")
        departure_time = data.get("departure_time")

        source_latitude = data.get("source_latitude")
        source_longitude = data.get("source_longitude")

        destination_latitude = data.get("destination_latitude")
        destination_longitude = data.get("destination_longitude")

        source_coordinates = None
        destination_coordinates = None

        if (
            source_latitude is not None
            and source_longitude is not None
        ):
            source_coordinates = [
                float(source_longitude),
                float(source_latitude)
            ]

        if (
            destination_latitude is not None
            and destination_longitude is not None
        ):
            destination_coordinates = [
                float(destination_longitude),
                float(destination_latitude)
            ]

        # =================================================
        # CHECK INPUT
        # =================================================

        if not source or not destination or not departure_time:
            return jsonify({
                "error": "Source, destination and departure time are required"
            }), 400

        # =================================================
        # CONVERT TIME TO HOUR
        # =================================================

        try:
            hour = int(departure_time.split(":")[0])
        except Exception:
            return jsonify({
                "error": "Invalid departure time format"
            }), 400

        # =================================================
        # PEAK HOUR
        # =================================================

        if (7 <= hour <= 10) or (17 <= hour <= 20):
            is_peak_hour = 1
        else:
            is_peak_hour = 0

        # =================================================
        # GET ROUTE
        # =================================================
        route_result = get_route(
            source,
            destination,
            source_coordinates,
            destination_coordinates
        )

        if "error" in route_result:
            return jsonify(route_result), 400

        print("DEBUG 1: Route completed")

        # =================================================
        # GET ROUTE INFORMATION
        # =================================================

        distance_km = route_result["distance_km"]
        duration_minutes = route_result["duration_minutes"]
        route_points = route_result["route_points"]
        source_coordinates = route_result["source_coordinates"]
        destination_coordinates = route_result["destination_coordinates"]

        # =================================================
        # ROAD INFORMATION
        # =================================================

        major_roads = route_result["major_roads"]
        state_roads = route_result["state_roads"]
        other_roads = route_result["other_roads"]
        roundabouts = route_result["roundabouts"]
        service_roads = route_result["service_roads"]
        flyovers_underpasses = route_result["flyovers_underpasses"]
        asphalt_percentage = route_result["asphalt_percentage"]
        paved_percentage = route_result["paved_percentage"]
        concrete_percentage = route_result["concrete_percentage"]
        good_surface_percentage = route_result["good_surface_percentage"]

        # =================================================
        # GET WEATHER
        # =================================================

        weather_result = get_overall_route_weather(route_points)
        print("DEBUG 2: Weather completed")

        weather = weather_result["overall_weather"]
        temperature = weather_result["average_temperature"]
        weather_source = weather_result["weather_source"]


        print("DEBUG 3: Weather value obtained")
        print("Weather source:", weather_source)

        # =================================================
        # ESTIMATE TRAFFIC
        # =================================================

        if is_peak_hour == 1:
            traffic_density = "high"
        elif 11 <= hour <= 16:
            traffic_density = "medium"
        else:
            traffic_density = "low"

        # =================================================
        # ESTIMATE VISIBILITY
        # =================================================

        if weather == "fog":
            visibility = "low"
        elif weather == "rain":
            visibility = "medium"
        else:
            visibility = "high"

        # =================================================
        # DETERMINE ROAD TYPE
        # =================================================

        if len(major_roads) > 0:
            road_type = "highway"
        elif len(state_roads) > 0:
            road_type = "highway"
        elif len(other_roads) > 0:
            road_type = "urban"
        else:
            road_type = "rural"

        # =================================================
        # ESTIMATE LANES
        # =================================================

        if len(major_roads) > 0:
            lanes = 4
        elif len(state_roads) > 0:
            lanes = 2
        else:
            lanes = 2

        # =================================================
        # CREATE ML INPUT
        # =================================================

        route_data = pd.DataFrame([{
            "weather": weather,
            "road_type": road_type,
            "traffic_density": traffic_density,
            "hour": hour,
            "is_peak_hour": is_peak_hour,
            "visibility": visibility,
            "temperature": temperature,
            "weather_source": weather_source,
            "lanes": lanes
            
        }])

        # =================================================
        # ML PREDICTION
        # =================================================

        prediction = model.predict(route_data)[0]

        # =================================================
        # ROUTE FACTOR
        # =================================================

        route_factor = 0.00

        # -------------------------------------------------
        # DISTANCE FACTOR
        # -------------------------------------------------

        if distance_km <= 50:
            route_factor += 0.00
        elif distance_km <= 100:
            route_factor += 0.03
        elif distance_km <= 150:
            route_factor += 0.05
        else:
            route_factor += 0.08

        # -------------------------------------------------
        # WEATHER FACTOR
        # -------------------------------------------------

        if weather == "rain":
            route_factor += 0.05
        elif weather == "fog":
            route_factor += 0.08

        # -------------------------------------------------
        # TRAFFIC FACTOR
        # -------------------------------------------------

        if traffic_density == "high":
            route_factor += 0.05
        elif traffic_density == "medium":
            route_factor += 0.02

        # -------------------------------------------------
        # VISIBILITY FACTOR
        # -------------------------------------------------

        if visibility == "low":
            route_factor += 0.05
        elif visibility == "medium":
            route_factor += 0.02

        # =================================================
        # ROAD QUALITY FACTOR
        # =================================================

        if asphalt_percentage >= 90:
            route_factor -= 0.08
        elif asphalt_percentage >= 75:
            route_factor -= 0.05
        elif asphalt_percentage >= 50:
            route_factor -= 0.02

        # =================================================
        # ROAD TYPE FACTOR
        # =================================================

        if road_type == "highway" and lanes >= 4:
            route_factor -= 0.03
        elif road_type == "highway":
            route_factor -= 0.01

        # =================================================
        # FINAL RISK
        # =================================================

        route_prediction = prediction + route_factor

        # Keep between 0 and 1
        route_prediction = min(max(route_prediction, 0), 1)

        # =================================================
        # RISK PERCENTAGE
        # =================================================

        risk_percentage = round(route_prediction * 100, 2)

        # =====================================================
        # GENERATE DYNAMIC ROUTE RISK ZONES
        # =====================================================

        global current_risk_zones
        current_risk_zones = generate_route_risk_zones(
            route_points,
            route_prediction,
            weather,
            traffic_density,
            visibility,
            asphalt_percentage,
            is_peak_hour
        )

        # =================================================
        # RISK LEVEL
        # =================================================

        if route_prediction < 0.35:
            risk_level = "Low"
        elif route_prediction < 0.65:
            risk_level = "Medium"
        else:
            risk_level = "High"

        # =================================================
        # RISK FACTORS
        # =================================================

        risk_factors = []

        if weather == "rain":
            risk_factors.append("Rainy weather")
        elif weather == "fog":
            risk_factors.append("Foggy weather")

        if traffic_density == "high":
            risk_factors.append("High traffic density")
        elif traffic_density == "medium":
            risk_factors.append("Moderate traffic density")

        if visibility == "low":
            risk_factors.append("Low visibility")
        elif visibility == "medium":
            risk_factors.append("Moderate visibility")

        if distance_km > 150:
            risk_factors.append("Long travel distance")
        elif distance_km > 100:
            risk_factors.append("Long travel distance")

        if asphalt_percentage < 50:
            risk_factors.append("Poor road surface")

        if is_peak_hour == 1:
            risk_factors.append("Peak hour traffic")

        # If no factors
        if len(risk_factors) == 0:
            risk_factors.append("No major risk factors detected")

        # =================================================
        # ALERT
        # =================================================

        if risk_level == "High":
            alert = "🚨 High-risk conditions detected. Drive carefully."
        elif risk_level == "Medium":
            alert = "⚠️ Moderate-risk conditions. Reduce speed if needed."
        else:
            alert = "✅ Low-risk conditions on this route."

        # =================================================
        # SIMPLIFY ROUTE POINTS
        # =================================================

        max_points = 200

        if len(route_points) > max_points:
            step = max(1, len(route_points) // max_points)
            simplified_route_points = route_points[::step]
        else:
            simplified_route_points = route_points

        # =================================================
        # FINAL RESPONSE
        # =================================================

        return jsonify({
            "source": source,
            "destination": destination,
            "departure_time": departure_time,
            "distance_km": distance_km,
            "duration_minutes": duration_minutes,
            "source_coordinates": source_coordinates,
            "destination_coordinates": destination_coordinates,
            "route_points": simplified_route_points,
            "major_roads": major_roads,
            "state_roads": state_roads,
            "other_roads": other_roads,
            "roundabouts": roundabouts,
            "service_roads": service_roads,
            "flyovers_underpasses": flyovers_underpasses,
            "road_type": road_type,
            "lanes": lanes,
            "asphalt_percentage": asphalt_percentage,
            "paved_percentage": paved_percentage,
            "concrete_percentage": concrete_percentage,
            "good_surface_percentage": good_surface_percentage,
            "route_weather": weather,
            "average_temperature": temperature,
            "hour": hour,
            "is_peak_hour": is_peak_hour,
            "traffic_density": traffic_density,
            "visibility": visibility,
            "risk_score": risk_percentage,
            "risk_level": risk_level,
            "risk_factors": risk_factors,
            "alert": alert,
            "risk_zones": current_risk_zones,
            "message": "Route safety analysis completed using live route weather and ML"
        })

    except Exception as e:
        import traceback
        print("Prediction error:", repr(e))
        traceback.print_exc()
        return jsonify({
            "error": "Failed to predict route safety",
            "details": str(e)
        }), 500


# =====================================================
# CHECK CURRENT DANGER ZONE
# =====================================================

@app.route("/check-risk-zone", methods=["POST"])
def check_risk_zone():

    data = request.get_json()

    latitude = data.get("latitude")
    longitude = data.get("longitude")


    # -----------------------------------------------
    # CHECK COORDINATES
    # -----------------------------------------------

    if latitude is None or longitude is None:

        return jsonify({

            "error":
                "Latitude and longitude are required"

        }), 400


    # -----------------------------------------------
    # CHECK DANGER ZONE
    # -----------------------------------------------

    result = check_danger_zone(

        float(latitude),

        float(longitude),
        current_risk_zones

    )


    return jsonify(result)


# =====================================================
# RUN SERVER
# =====================================================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)