// =====================================================
// GLOBAL VARIABLES
// =====================================================

let map = null;
let routeLine = null;

let sourceMarker = null;
let destinationMarker = null;
let userMarker = null;

let locationWatcher = null;

let lastZone = "Safe";

let riskZoneLayers = [];


// =====================================================
// FIND ROUTE
// =====================================================

async function findRoute() {

    const source =
        document.getElementById("source").value.trim();

    const destination =
        document.getElementById("destination").value.trim();

    const departureTime =
        document.getElementById("departureTime").value;


    if (!source || !destination || !departureTime) {

        document.getElementById("result").innerHTML = `
            <h2>⚠️ Missing Information</h2>
            <p>
                Please enter source, destination
                and departure time.
            </p>
        `;

        return;
    }


    document.getElementById("result").innerHTML = `
        <h2>⏳ Checking Route Safety...</h2>

        <p>
            Finding route, checking weather,
            and predicting risk...
        </p>
    `;


    try {

        console.log("Sending source:", source);
        console.log("Sending destination:", destination);


        const response = await fetch(
            "/predict",
            {
                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify({

                    source: source,

                    destination: destination,

                    source_latitude:
                        document.getElementById("source").dataset.latitude || null,

                    source_longitude:
                        document.getElementById("source").dataset.longitude || null,

                    destination_latitude:
                        document.getElementById("destination").dataset.latitude || null,

                    destination_longitude:
                        document.getElementById("destination").dataset.longitude || null,

                    departure_time: departureTime

                })
            }
        );


        if (!response.ok) {

            throw new Error(
                "Server returned HTTP " +
                response.status
            );

        }


        const data =
            await response.json();


        console.log(
            "Route data:",
            data
        );


        // DRAW MAP

        showMap(data);


        // =================================================
        // DURATION
        // =================================================

        const hours =
            Math.floor(
                data.duration_minutes / 60
            );

        const minutes =
            Math.round(
                data.duration_minutes % 60
            );

        const durationText =
            hours + "h " + minutes + "m";


        // =================================================
        // ROAD COUNTS
        // =================================================

        const majorRoadCount =
            data.major_roads
                ? data.major_roads.length
                : 0;

        const stateRoadCount =
            data.state_roads
                ? data.state_roads.length
                : 0;

        const otherRoadCount =
            data.other_roads
                ? data.other_roads.length
                : 0;


        // =================================================
        // DEFAULT VALUES
        // =================================================

        const roadType =
            data.road_type || "Unknown";

        const goodSurface =
            data.good_surface_percentage ??
            0;

        const asphalt =
            data.asphalt_percentage ??
            0;

        const paved =
            data.paved_percentage ??
            0;

        const concrete =
            data.concrete_percentage ??
            0;

        const lanes =
            data.lanes || 0;


        // =================================================
        // RISK FACTORS
        // =================================================

        let riskFactorsHTML =
            "<li>No risk factors available</li>";


        if (
            data.risk_factors &&
            data.risk_factors.length > 0
        ) {

            riskFactorsHTML =
                data.risk_factors
                    .map(
                        factor =>
                            `<li>${factor}</li>`
                    )
                    .join("");

        }


        // =================================================
        // RESULT
        // =================================================

        document.getElementById(
            "result"
        ).innerHTML = `

            <h2>
                🚦 Route Safety Result
            </h2>


            <h3>
                📍 Route Information
            </h3>


            <p>
                <b>🛣️ Route:</b>
                ${data.source}
                →
                ${data.destination}
            </p>


            <p>
                <b>📏 Distance:</b>
                ${data.distance_km} km
            </p>


            <p>
                <b>⏱️ Duration:</b>
                ${durationText}
            </p>


            <hr>


            <h3>
                🛡️ Safety Analysis
            </h3>


            <p>
                <b>⚠️ Risk Score:</b>
                ${data.risk_score}%
            </p>


            <p>
                <b>🚦 Risk Level:</b>
                ${data.risk_level}
            </p>


            <h3>
                ${data.alert}
            </h3>


            <hr>


            <h3>
                🛡️ Risk Factors
            </h3>


            <ul>
                ${riskFactorsHTML}
            </ul>


            <hr>


            <h3>
                🌦️ Weather & Traffic
            </h3>


            <p>
                <b>🌦️ Weather:</b>
                ${data.route_weather}
            </p>


            <p>
                <b>🌡️ Temperature:</b>
                ${data.average_temperature} °C
            </p>


            <p>
                <b>🚗 Traffic:</b>
                ${data.traffic_density}
            </p>


            <p>
                <b>👁️ Visibility:</b>
                ${data.visibility}
            </p>


            <hr>


            <h3>
                🛣️ Road Quality
            </h3>


            <p>
                <b>🛣️ Road Type:</b>
                ${roadType}
            </p>


            <p>
                <b>🛞 Good Road Surface:</b>
                ${goodSurface}%
            </p>


            <p>
                <b>🛣️ Asphalt:</b>
                ${asphalt}%
            </p>


            <p>
                <b>🛤️ Paved:</b>
                ${paved}%
            </p>


            <p>
                <b>🧱 Concrete:</b>
                ${concrete}%
            </p>


            <p>
                <b>🛣️ Lanes:</b>
                ${lanes}
            </p>


            <hr>


            <h3>
                🛣️ Road Information
            </h3>


            <p>
                <b>🛣️ Major Highways:</b>
                ${majorRoadCount}
            </p>


            <p>
                <b>🛤️ State Roads:</b>
                ${stateRoadCount}
            </p>


            <p>
                <b>🛣️ Other Roads:</b>
                ${otherRoadCount}
            </p>


            <p>
                <b>🔄 Roundabouts:</b>
                ${data.roundabouts}
            </p>


            <p>
                <b>🛣️ Service Roads:</b>
                ${data.service_roads}
            </p>


            <p>
                <b>🌉 Flyovers / Underpasses:</b>
                ${data.flyovers_underpasses}
            </p>


            <hr>


            <h3>
                🕐 Journey Details
            </h3>


            <p>
                <b>Departure Time:</b>
                ${data.departure_time}
            </p>


            <p>
                <b>Peak Hour:</b>
                ${
                    data.is_peak_hour == 1
                    ? "Yes"
                    : "No"
                }
            </p>

        `;

    }


    catch (error) {

        console.error(
            "Route prediction error:",
            error
        );


        document.getElementById(
            "result"
        ).innerHTML = `

            <h2>
                ❌ Route Prediction Failed
            </h2>

            <p>
                ${error.message}
            </p>

            <p>
                Make sure Flask is running.
            </p>

        `;

    }

}


// =====================================================
// SHOW MAP
// =====================================================

function showMap(data) {

    console.log(
        "SOURCE:",
        data.source_coordinates
    );

    console.log(
        "DESTINATION:",
        data.destination_coordinates
    );

    console.log(
        "FIRST ROUTE POINT:",
        data.route_points[0]
    );


    // =================================================
    // CREATE MAP
    // =================================================

    if (map === null) {

        map = L.map("map");

        L.tileLayer(
            "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
            {
                maxZoom: 19,
                attribution:
                    "© OpenStreetMap"
            }
        ).addTo(map);

    }


    // =================================================
    // REMOVE OLD ROUTE
    // =================================================

    if (routeLine !== null) {

        map.removeLayer(routeLine);

        routeLine = null;

    }


    // =================================================
    // REMOVE OLD MARKERS
    // =================================================

    if (sourceMarker !== null) {

        map.removeLayer(sourceMarker);

        sourceMarker = null;

    }


    if (destinationMarker !== null) {

        map.removeLayer(destinationMarker);

        destinationMarker = null;

    }


    // =================================================
    // ROUTE COORDINATES
    // =================================================

    const leafletPoints =
        data.route_points.map(
            point => [

                point[1],

                point[0]

            ]
        );


    console.log(
        "LEAFLET ROUTE POINT:",
        leafletPoints[0]
    );


    // =================================================
    // DRAW ROUTE
    // =================================================

    routeLine =
        L.polyline(

            leafletPoints,

            {
                color: "green",
                weight: 6,
                opacity: 0.9
            }

        ).addTo(map);


    // =================================================
    // SOURCE MARKER
    // =================================================

    const sourceLat =
        data.source_coordinates[1];

    const sourceLon =
        data.source_coordinates[0];


    sourceMarker =
        L.marker(
            [
                sourceLat,
                sourceLon
            ]
        )
        .addTo(map)
        .bindPopup(
            `<b>📍 Source</b><br>${data.source}`
        );


    // =================================================
    // DESTINATION MARKER
    // =================================================

    const destinationLat =
        data.destination_coordinates[1];

    const destinationLon =
        data.destination_coordinates[0];


    destinationMarker =
        L.marker(
            [
                destinationLat,
                destinationLon
            ]
        )
        .addTo(map)
        .bindPopup(
            `<b>🏁 Destination</b><br>${data.destination}`
        );


    console.log(
        "Source marker:",
        sourceLat,
        sourceLon
    );

    console.log(
        "Destination marker:",
        destinationLat,
        destinationLon
    );


    // =================================================
    // FIT ROUTE
    // =================================================

    map.fitBounds(
        routeLine.getBounds(),
        {
            padding: [50, 50]
        }
    );


    // =================================================
    // LOAD RISK ZONES
    // =================================================

    loadRiskZones();


    // =================================================
    // FIX MAP
    // =================================================

    setTimeout(
        function() {

            map.invalidateSize();

        },
        500
    );

}


// =====================================================
// LOAD RISK ZONES
// =====================================================

async function loadRiskZones() {

    try {

        console.log(
            "Loading risk zones..."
        );


        const response =
            await fetch(
                "/risk-zones"
            );


        if (!response.ok) {

            throw new Error(
                "Risk zone request failed: " +
                response.status
            );

        }


        const zones =
            await response.json();


        console.log(
            "Risk zones:",
            zones
        );


        // =================================================
        // REMOVE OLD ZONES
        // =================================================

        riskZoneLayers.forEach(
            layer => {

                map.removeLayer(layer);

            }
        );


        riskZoneLayers = [];


        // =================================================
        // DRAW ZONES
        // =================================================

        zones.forEach(
            function(zone) {

                let circleColor;

                let zoneText;


                if (
                    zone.risk_level === "High"
                ) {

                    circleColor = "red";

                    zoneText =
                        "🚨 High Risk Zone";

                }

                else if (
                    zone.risk_level === "Medium"
                ) {

                    circleColor = "orange";

                    zoneText =
                        "⚠️ Caution Zone";

                }

                else {

                    circleColor = "green";

                    zoneText =
                        "✅ Safe Zone";

                }


                const circle =
                    L.circle(

                        [
                            zone.latitude,
                            zone.longitude
                        ],

                        {

                            radius:
                                zone.radius,

                            color:
                                circleColor,

                            fillColor:
                                circleColor,

                            fillOpacity:
                                0.25,

                            weight: 3

                        }

                    ).addTo(map);


                circle.bindPopup(`

                    <b>${zoneText}</b>

                    <br><br>

                    📍 ${zone.name}

                    <br>

                    ⚠️ Risk Level:
                    ${zone.risk_level}

                    <br>

                📊 Risk Score:
                ${zone.risk_score}%

                <br>

                📏 Radius:
                ${zone.radius} meters

            `);


                riskZoneLayers.push(
                    circle
                );

            }
        );


        console.log(
            "Risk zones displayed:",
            riskZoneLayers.length
        );

    }


    catch (error) {

        console.error(
            "Risk zone loading failed:",
            error
        );

    }

}


// =====================================================
// START SAFETY NAVIGATION
// =====================================================

function startNavigation() {

    if (!navigator.geolocation) {

        alert(
            "❌ Geolocation is not supported."
        );

        return;

    }


    if (map === null) {

        alert(
            "Please find a route first."
        );

        return;

    }


    alert(
        "📍 Safety navigation started."
    );


    locationWatcher =
        navigator.geolocation.watchPosition(

            function(position) {

                const latitude =
                    position.coords.latitude;

                const longitude =
                    position.coords.longitude;


                console.log(
                    "User location:",
                    latitude,
                    longitude
                );


                // =================================================
                // CHECK RISK
                // =================================================

                checkRiskZone(
                    latitude,
                    longitude
                );


                // =================================================
                // USER MARKER
                // =================================================

                if (
                    userMarker !== null
                ) {

                    userMarker.setLatLng(
                        [
                            latitude,
                            longitude
                        ]
                    );

                }

                else {

                    userMarker =
                        L.marker(

                            [
                                latitude,
                                longitude
                            ]

                        )
                        .addTo(map)
                        .bindPopup(
                            "📍 Your Current Location"
                        );

                }


                // =================================================
                // CENTER MAP
                // =================================================

                map.setView(

                    [
                        latitude,
                        longitude
                    ],

                    15

                );

            },


            function(error) {

                console.error(
                    "Geolocation error:",
                    error
                );


                if (
                    error.code === 1
                ) {

                    alert(
                        "❌ Location permission denied."
                    );

                }

                else if (
                    error.code === 2
                ) {

                    alert(
                        "❌ Location unavailable."
                    );

                }

                else if (
                    error.code === 3
                ) {

                    console.log(
                        "Location request timed out. Retrying..."
                    );

                }

            },


            {

                enableHighAccuracy:
                    true,

                maximumAge:
                    5000,

                timeout:
                    15000

            }

        );

}


// =====================================================
// CHECK RISK ZONE
// =====================================================

async function checkRiskZone(
    latitude,
    longitude
) {

    try {

        const response =
            await fetch(

                "/check-risk-zone",

                {

                    method: "POST",

                    headers: {

                        "Content-Type":
                            "application/json"

                    },

                    body:
                        JSON.stringify({

                            latitude:
                                latitude,

                            longitude:
                                longitude

                        })

                }

            );


        if (!response.ok) {

            throw new Error(
                "Risk zone server error"
            );

        }


        const data =
            await response.json();


        console.log(
            "Current risk zone:",
            data.zone
        );


        // =================================================
        // ALERT ONLY WHEN ZONE CHANGES
        // =================================================

        if (
            data.zone !== lastZone
        ) {

            if (
                data.zone === "Danger" ||
                data.zone === "Caution"
            ) {

                alert(
                    data.alert
                );

            }


            lastZone =
                data.zone;

        }

    }


    catch (error) {

        console.error(
            "Risk zone checking failed:",
            error
        );

    }

}
// =====================================================
// LOCATION SUGGESTIONS
// =====================================================

function setupLocationSuggestions(inputId, suggestionsId) {

    const input = document.getElementById(inputId);
    const suggestions = document.getElementById(suggestionsId);

    let timer = null;

    input.addEventListener("input", function () {

        const query = input.value.trim();

        clearTimeout(timer);

        if (query.length < 2) {

            suggestions.innerHTML = "";
            suggestions.style.display = "none";

            return;
        }

        timer = setTimeout(async function () {

            try {

                const response = await fetch(
                    "https://nominatim.openstreetmap.org/search?" +
                    new URLSearchParams({

                        q: query,

                        format: "json",

                        limit: "5",

                        countrycodes: "in",

                        addressdetails: "1",

                        "accept-language": "en"

                    })
                );

                const places = await response.json();

                suggestions.innerHTML = "";

                if (places.length === 0) {

                    suggestions.style.display = "none";

                    return;
                }


                places.forEach(function (place) {

                    const item =
                        document.createElement("div");

                    item.className =
                        "suggestion-item";


                    // Get simple English name
                    let name =
                        getShortLocationName(place);


                    item.textContent =
                        "📍 " + name;


                    item.addEventListener(
                        "click",
                        function () {

                            input.value = name;

                            // Store coordinates so findRoute()
                            // can send them to the backend
                            input.dataset.latitude = place.lat;
                            input.dataset.longitude = place.lon;

                            suggestions.innerHTML = "";

                            suggestions.style.display =
                                "none";

                        }
                    );


                    suggestions.appendChild(item);

                });


                suggestions.style.display = "block";

            }

            catch (error) {

                console.error(
                    "Location suggestion error:",
                    error
                );

                suggestions.style.display = "none";

            }

        }, 400);

    });


    // Hide suggestions when clicking outside

    document.addEventListener(
        "click",
        function (event) {

            if (
                !input.contains(event.target) &&
                !suggestions.contains(event.target)
            ) {

                suggestions.style.display = "none";

            }

        }
    );

}


// =====================================================
// GET SIMPLE ENGLISH LOCATION NAME
// =====================================================

function getShortLocationName(place) {

    const address = place.address || {};


    if (address.city) {

        return address.city;

    }


    if (address.town) {

        return address.town;

    }


    if (address.village) {

        return address.village;

    }


    if (address.municipality) {

        return address.municipality;

    }


    if (address.suburb) {

        return address.suburb;

    }


    if (place.name) {

        return place.name;

    }


    return place.display_name.split(",")[0];

}


// =====================================================
// (Direct-Nominatim suggestions disabled — see note
// below. setupLocationAutocomplete() using our own
// /search-location backend is the active system, since
// it sends a proper User-Agent header that Nominatim's
// usage policy requires and a browser can't set.)
// =====================================================

// setupLocationSuggestions(
//     "source",
//     "sourceSuggestions"
// );


// setupLocationSuggestions(
//     "destination",
//     "destinationSuggestions"
// );

// =====================================================
// LOCATION AUTOCOMPLETE — ACTIVE SYSTEM
// Calls our own Flask backend's /search-location route
// (already India-restricted, already sets lat/lon).
// This backend-based version was firing on the same
// inputs at the same time and racing it, so it's
// disabled by not being called below.
// =====================================================

function setupLocationAutocomplete(
    inputId,
    suggestionsId
) {

    const input =
        document.getElementById(inputId);

    const suggestionsBox =
        document.getElementById(suggestionsId);

    let searchTimeout = null;


    input.addEventListener(
        "input",
        function () {

            const query =
                input.value.trim();


            clearTimeout(searchTimeout);


            if (query.length < 2) {

                suggestionsBox.innerHTML = "";

                suggestionsBox.style.display =
                    "none";

                return;

            }


            // Wait a little before searching
            searchTimeout =
                setTimeout(
                    () => searchLocations(
                        query,
                        input,
                        suggestionsBox
                    ),
                    350
                );

        }
    );


    // Hide suggestions when clicking elsewhere
    document.addEventListener(
        "click",
        function (event) {

            if (
                !input.contains(event.target) &&
                !suggestionsBox.contains(event.target)
            ) {

                suggestionsBox.style.display =
                    "none";

            }

        }
    );

}


// =====================================================
// SEARCH LOCATIONS
// =====================================================

async function searchLocations(
    query,
    input,
    suggestionsBox
) {

    try {

        const response =
            await fetch(
                "/search-location?q=" +
                encodeURIComponent(query)
            );


        if (!response.ok) {

            throw new Error(
                "Location search failed"
            );

        }


        const results =
            await response.json();


        suggestionsBox.innerHTML = "";


        if (
            !results ||
            results.length === 0
        ) {

            suggestionsBox.style.display =
                "none";

            return;

        }


        results.forEach(
            function (place) {

                const item =
                    document.createElement("div");


                item.className =
                    "suggestion-item";


                item.innerHTML = `
                    <div class="suggestion-name">
                        📍 ${place.name}
                    </div>

                    <div class="suggestion-location">
                        ${place.display}
                    </div>
                `;


                item.addEventListener(
                    "click",
                    function () {

                        input.value =
                            place.name;

                        suggestionsBox.style.display =
                            "none";


                        // Store coordinates
                        input.dataset.latitude =
                            place.latitude;

                        input.dataset.longitude =
                            place.longitude;


                        console.log(
                            "Selected location:",
                            place.name,
                            place.latitude,
                            place.longitude
                        );

                    }
                );


                suggestionsBox.appendChild(
                    item
                );

            }
        );


        suggestionsBox.style.display =
            "block";

    }


    catch (error) {

        console.error(
            "Location suggestion error:",
            error
        );

        suggestionsBox.style.display =
            "none";

    }

}


// =====================================================
// START AUTOCOMPLETE (active system)
// =====================================================

setupLocationAutocomplete(
    "source",
    "sourceSuggestions"
);


setupLocationAutocomplete(
    "destination",
    "destinationSuggestions"
);

