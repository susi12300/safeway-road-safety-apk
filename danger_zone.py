# =====================================================
# DEMO DANGER ZONE
# =====================================================

DEMO_DANGER_ZONE = {

    "name": " Danger Zone",

    # =================================================
    # CHANGE THESE COORDINATES FOR YOUR DEMO
    # =================================================

    "latitude": 12.952002158008384,
    "longitude": 78.8854667668702,
    # 12.951945 12.951945
    #  12.952002158008384 78.8854667668702


# 12.951945 78.885362
# 12.952145 78.885695

    # 500 metre radius
    "radius": 500,

    "risk_level": "High",

    "zone": "Danger",

    "risk_score": 90
}


# =====================================================
# DYNAMIC ROUTE RISK ZONES
# =====================================================

def calculate_zone_risk(
    base_risk,
    weather,
    traffic_density,
    visibility,
    asphalt_percentage,
    is_peak_hour
):

    risk = base_risk


    # =================================================
    # WEATHER
    # =================================================

    if weather == "rain":

        risk += 0.08

    elif weather == "fog":

        risk += 0.12


    # =================================================
    # TRAFFIC
    # =================================================

    if traffic_density == "high":

        risk += 0.08

    elif traffic_density == "medium":

        risk += 0.04


    # =================================================
    # VISIBILITY
    # =================================================

    if visibility == "low":

        risk += 0.08

    elif visibility == "medium":

        risk += 0.04


    # =================================================
    # ROAD SURFACE
    # =================================================

    if asphalt_percentage < 50:

        risk += 0.08

    elif asphalt_percentage < 75:

        risk += 0.04

    elif asphalt_percentage >= 90:

        risk -= 0.05


    # =================================================
    # PEAK HOUR
    # =================================================

    if is_peak_hour == 1:

        risk += 0.05


    # =================================================
    # KEEP BETWEEN 0 AND 1
    # =================================================

    risk = max(
        0,
        min(risk, 1)
    )


    return risk


# =====================================================
# CREATE RISK ZONES ALONG ROUTE
# =====================================================

def generate_route_risk_zones(
    route_points,
    base_risk,
    weather,
    traffic_density,
    visibility,
    asphalt_percentage,
    is_peak_hour
):

    risk_zones = []


    # =================================================
    # CHECK ROUTE
    # =================================================

    if not route_points:

        return risk_zones


    # =================================================
    # SAMPLE ROUTE POINTS
    # =================================================

    max_zones = 12

    total_points = len(route_points)


    if total_points <= max_zones:

        selected_points = route_points

    else:

        step = total_points // max_zones

        selected_points = route_points[::step]


    # =================================================
    # GENERATE RISK FOR EACH ROUTE SECTION
    # =================================================

    for index, point in enumerate(selected_points):


        longitude = point[0]

        latitude = point[1]


        # =================================================
        # BASE ROUTE RISK
        # =================================================

        zone_risk = calculate_zone_risk(

            base_risk,

            weather,

            traffic_density,

            visibility,

            asphalt_percentage,

            is_peak_hour

        )


        # =================================================
        # SECTION VARIATION
        # =================================================

        variation_pattern = [

            -0.04,
            -0.02,
             0.00,
             0.03,
             0.05,
             0.02,
            -0.02,
             0.04,
             0.00,
            -0.03,
             0.03,
             0.01

        ]


        zone_risk += variation_pattern[
            index % len(variation_pattern)
        ]


        # =================================================
        # KEEP BETWEEN 0 AND 1
        # =================================================

        zone_risk = max(
            0,
            min(zone_risk, 1)
        )


        # =================================================
        # DETERMINE ZONE
        # =================================================

        if zone_risk >= 0.65:

            risk_level = "High"

            zone = "Danger"


        elif zone_risk >= 0.35:

            risk_level = "Medium"

            zone = "Caution"


        else:

            risk_level = "Low"

            zone = "Safe"


        # =================================================
        # ADD ZONE
        # =================================================

        risk_zones.append({

            "name":
                "Route Risk Zone " +
                str(index + 1),

            "latitude":
                latitude,

            "longitude":
                longitude,

            "risk_level":
                risk_level,

            "zone":
                zone,

            "risk_score":
                round(
                    zone_risk * 100,
                    2
                ),

            "radius":
                500

        })


    return risk_zones


# =====================================================
# CALCULATE DISTANCE BETWEEN TWO LOCATIONS
# =====================================================

from math import (
    radians,
    sin,
    cos,
    sqrt,
    atan2
)


def calculate_distance(
    latitude1,
    longitude1,
    latitude2,
    longitude2
):

    earth_radius = 6371000


    lat1 = radians(
        latitude1
    )

    lat2 = radians(
        latitude2
    )


    delta_lat = radians(
        latitude2 - latitude1
    )

    delta_lon = radians(
        longitude2 - longitude1
    )


    a = (

        sin(delta_lat / 2) ** 2

        +

        cos(lat1)
        *
        cos(lat2)
        *
        sin(delta_lon / 2) ** 2

    )


    c = 2 * atan2(

        sqrt(a),

        sqrt(1 - a)

    )


    return earth_radius * c


# =====================================================
# CHECK USER CURRENT LOCATION
# =====================================================

def check_danger_zone(
    latitude,
    longitude,
    risk_zones
):


    # =================================================
    # CHECK DEMO DANGER ZONE FIRST
    # =================================================

    demo_distance = calculate_distance(

        latitude,
        longitude,

        DEMO_DANGER_ZONE["latitude"],
        DEMO_DANGER_ZONE["longitude"]

    )


    # =================================================
    # USER IS INSIDE DEMO DANGER ZONE
    # =================================================

    if demo_distance <= DEMO_DANGER_ZONE["radius"]:

        return {

            "zone":
                "Danger",

            "risk_level":
                "High",

            "zone_name":
                DEMO_DANGER_ZONE["name"],

            "distance":
                round(
                    demo_distance,
                    2
                ),

            "risk_score":
                DEMO_DANGER_ZONE["risk_score"],

            "alert":
                "🚨 DEMO ALERT: You have entered a high-risk zone. Drive carefully."

        }


    # =================================================
    # CHECK DYNAMIC ROUTE RISK ZONES
    # =================================================

    for zone in risk_zones:


        distance = calculate_distance(

            latitude,
            longitude,

            zone["latitude"],
            zone["longitude"]

        )


        # =================================================
        # USER INSIDE THIS ZONE
        # =================================================

        if distance <= zone["radius"]:


            # =================================================
            # HIGH RISK
            # =================================================

            if zone["risk_level"] == "High":

                return {

                    "zone":
                        "Danger",

                    "risk_level":
                        "High",

                    "zone_name":
                        zone["name"],

                    "distance":
                        round(
                            distance,
                            2
                        ),

                    "risk_score":
                        zone["risk_score"],

                    "alert":
                        "🚨 High-risk zone ahead. "
                        "Drive carefully."

                }


            # =================================================
            # MEDIUM RISK
            # =================================================

            elif zone["risk_level"] == "Medium":

                return {

                    "zone":
                        "Caution",

                    "risk_level":
                        "Medium",

                    "zone_name":
                        zone["name"],

                    "distance":
                        round(
                            distance,
                            2
                        ),

                    "risk_score":
                        zone["risk_score"],

                    "alert":
                        "⚠️ Moderate-risk zone. "
                        "Reduce speed."

                }


    # =================================================
    # SAFE ZONE
    # =================================================

    return {

        "zone":
            "Safe",

        "risk_level":
            "Low",

        "zone_name":
            None,

        "distance":
            None,

        "risk_score":
            0,

        "alert":
            "✅ You are currently in a safe zone."

    }