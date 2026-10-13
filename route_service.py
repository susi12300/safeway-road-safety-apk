import requests
import os
from dotenv import load_dotenv

load_dotenv()

# ==================================================
# OPENROUTESERVICE API
# ==================================================

API_KEY = os.getenv("ORS_API_KEY")

ORS_BASE_URL = "https://api.heigit.org/openrouteservice"

if not API_KEY:
    raise RuntimeError("ORS_API_KEY is not configured.")


# ==================================================
# GET COORDINATES
# ==================================================
def get_coordinates(place):
    """
    Convert a place name into [longitude, latitude]
    using the current openrouteservice/HeiGIT geocoding API.
    """

    url = "https://api.heigit.org/pelias/v1/search"

    parameters = {
        "text": place,
        "size": 1,
        "boundary.country": "IND"
    }

    headers = {
        "Authorization": API_KEY,
        "User-Agent": "SafeWay-Road-Safety-Project/1.0"
    }

    response = requests.get(
    	url,
    	params=parameters,
    	headers=headers,
    	timeout=(5, 25)
    )

    print("Geocoding status:", response.status_code)
    print("Geocoding response:", response.text[:500])

    if response.status_code != 200:
        raise RuntimeError(
            "Location search service is temporarily unavailable."
        )

    data = response.json()

    features = data.get("features", [])

    if not features:
        return None

    coordinates = features[0].get("geometry", {}).get("coordinates")

    if not coordinates:
        return None

    longitude = float(coordinates[0])
    latitude = float(coordinates[1])

    return [longitude, latitude]

# ==================================================
# GET ROUTE
# ==================================================

def get_route(
    source,
    destination,
    source_coordinates=None,
    destination_coordinates=None
):

    # ==================================================
    # GET SOURCE COORDINATES
    # ==================================================

    if source_coordinates is None:

        source_coordinates = get_coordinates(
            source
        )


    # ==================================================
    # GET DESTINATION COORDINATES
    # ==================================================

    if destination_coordinates is None:

        destination_coordinates = get_coordinates(
            destination
        )


    # ==================================================
    # CHECK COORDINATES
    # ==================================================

    if source_coordinates is None:

        return {
            "error": "Source location not found"
        }

    if destination_coordinates is None:

        return {
            "error": "Destination location not found"
        }


    # ==================================================
    # GET DRIVING ROUTE
    # ==================================================

    url = (
        f"{ORS_BASE_URL}"
        "/v2/directions/driving-car/geojson"
    )

    route_data = {
        "coordinates": [
            source_coordinates,
            destination_coordinates
        ],
        "extra_info": [
            "surface",
            "waytype",
            "waycategory"
        ]
    }

    headers = {
        "Authorization": API_KEY,
        "Content-Type": "application/json",
        "Accept": "application/geo+json"
    }

    response = requests.post(
        url,
        json=route_data,
        headers=headers,
        timeout=30
    )

    print(
        "Directions status:",
        response.status_code
    )

    if response.status_code != 200:

        print(
            "Directions response:",
            response.text[:1000]
        )

        raise RuntimeError(
            "Route service is temporarily unavailable."
        )

    route = response.json()


    # ==================================================
    # CHECK ROUTE RESULT
    # ==================================================

    features = route.get(
        "features",
        []
    )

    if not features:

        raise RuntimeError(
            "No route was found between the selected locations."
        )

    print(
        "Number of routes found:",
        len(features)
    )

    route_info = features[0]

    properties = route_info.get(
        "properties",
        {}
    )

    extras = properties.get(
        "extras",
        {}
    )


    # ==================================================
    # ROAD SURFACE INFORMATION
    # ==================================================

    surface_info = extras.get(
        "surface",
        {}
    )

    surface_summary = surface_info.get(
        "summary",
        []
    )

    asphalt_percentage = 0
    paved_percentage = 0
    concrete_percentage = 0

    for surface in surface_summary:

        value = surface.get(
            "value"
        )

        amount = surface.get(
            "amount",
            0
        )

        if value == 3:

            asphalt_percentage += amount

        elif value == 1:

            paved_percentage += amount

        elif value == 4:

            concrete_percentage += amount


    good_surface_percentage = (
        asphalt_percentage
        + paved_percentage
        + concrete_percentage
    )


    print(
        "\n========== ROAD SURFACE =========="
    )

    print(
        "Asphalt:",
        round(asphalt_percentage, 2),
        "%"
    )

    print(
        "Paved:",
        round(paved_percentage, 2),
        "%"
    )

    print(
        "Concrete:",
        round(concrete_percentage, 2),
        "%"
    )

    print(
        "Good surface:",
        round(good_surface_percentage, 2),
        "%"
    )

    print(
        "=================================="
    )


    # ==================================================
    # GET ROUTE POINTS
    # ==================================================

    geometry = route_info.get(
        "geometry",
        {}
    )

    route_points = geometry.get(
        "coordinates",
        []
    )


    # ==================================================
    # EXTRACT ROAD INFORMATION
    # ==================================================

    major_roads = []

    state_roads = []

    other_roads = []

    roundabouts = 0

    service_roads = 0

    flyovers_underpasses = 0


    segments = properties.get(
        "segments",
        []
    )


    for segment in segments:

        steps = segment.get(
            "steps",
            []
        )

        for step in steps:

            road_name = step.get(
                "name",
                ""
            )

            instruction = step.get(
                "instruction",
                ""
            )


            # ------------------------------------------
            # ROAD NAMES
            # ------------------------------------------

            if road_name and road_name != "-":

                if (
                    "NH" in road_name
                    or "National Highway" in road_name
                ):

                    if road_name not in major_roads:

                        major_roads.append(
                            road_name
                        )

                elif (
                    "SH" in road_name
                    or "State Highway" in road_name
                ):

                    if road_name not in state_roads:

                        state_roads.append(
                            road_name
                        )

                else:

                    if road_name not in other_roads:

                        other_roads.append(
                            road_name
                        )


            # ------------------------------------------
            # ROUNDABOUT
            # ------------------------------------------

            if (
                "roundabout"
                in instruction.lower()
            ):

                roundabouts += 1


            # ------------------------------------------
            # SERVICE ROAD
            # ------------------------------------------

            if (
                "service road"
                in road_name.lower()
            ):

                service_roads += 1


            # ------------------------------------------
            # FLYOVER / UNDERPASS
            # ------------------------------------------

            road_text = (
                road_name
                + " "
                + instruction
            ).lower()

            if (
                "flyover" in road_text
                or "underpass" in road_text
                or "elevated road" in road_text
            ):

                flyovers_underpasses += 1


    # ==================================================
    # ROUTE DISTANCE AND DURATION
    # ==================================================

    summary = properties.get(
        "summary",
        {}
    )

    distance_km = (
        summary.get(
            "distance",
            0
        )
        / 1000
    )

    duration_minutes = (
        summary.get(
            "duration",
            0
        )
        / 60
    )


    # ==================================================
    # PRINT ROAD INFORMATION
    # ==================================================

    print(
        "\n========== ROAD INFORMATION =========="
    )

    print(
        "Major Highways:",
        major_roads
    )

    print(
        "State Highways:",
        state_roads
    )

    print(
        "Other Roads:",
        other_roads
    )

    print(
        "Roundabouts:",
        roundabouts
    )

    print(
        "Service Roads:",
        service_roads
    )

    print(
        "Flyovers / Underpasses:",
        flyovers_underpasses
    )

    print(
        "Distance:",
        round(distance_km, 2),
        "km"
    )

    print(
        "Duration:",
        round(duration_minutes, 2),
        "minutes"
    )

    print(
        "======================================\n"
    )


    # ==================================================
    # RETURN RESULT
    # ==================================================

    return {

        "source":
            source,

        "destination":
            destination,

        "source_coordinates":
            source_coordinates,

        "destination_coordinates":
            destination_coordinates,

        "distance_km":
            round(
                distance_km,
                2
            ),

        "duration_minutes":
            round(
                duration_minutes,
                2
            ),

        "route_points":
            route_points,

        "major_roads":
            major_roads,

        "state_roads":
            state_roads,

        "other_roads":
            other_roads,

        "roundabouts":
            roundabouts,

        "service_roads":
            service_roads,

        "flyovers_underpasses":
            flyovers_underpasses,

        "asphalt_percentage":
            round(
                asphalt_percentage,
                2
            ),

        "paved_percentage":
            round(
                paved_percentage,
                2
            ),

        "concrete_percentage":
            round(
                concrete_percentage,
                2
            ),

        "good_surface_percentage":
            round(
                good_surface_percentage,
                2
            )
    }


# ==================================================
# TEST
# ==================================================

if __name__ == "__main__":

    result = get_route(
        "Vellore",
        "Chennai"
    )

    print(
        "\n========== FINAL RESULT =========="
    )

    print(
        "Distance:",
        result["distance_km"],
        "km"
    )

    print(
        "Duration:",
        result["duration_minutes"],
        "minutes"
    )

    print(
        "Major Roads:",
        result["major_roads"]
    )

    print(
        "State Roads:",
        result["state_roads"]
    )

    print(
        "Roundabouts:",
        result["roundabouts"]
    )

    print(
        "Service Roads:",
        result["service_roads"]
    )

    print(
        "Flyovers / Underpasses:",
        result["flyovers_underpasses"]
    )

    print(
        "================================="
    )