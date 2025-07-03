import requests
import unicodedata
import sqlite3
import os
from datetime import datetime, timezone
from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
import re
from math import ceil

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///stations.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

BVG_API_BASE = "https://v6.bvg.transport.rest"

# Database Model for Stations
class Station(db.Model):
    name = db.Column(db.String, primary_key=True)  # Station Name
    id = db.Column(db.String, nullable=False, unique=True)
    normalized_name = db.Column(db.String, nullable=False, unique=True)

    def __init__(self, name, id):
        self.name = name
        self.id = id
        self.normalized_name = normalize_station_name(name)

# Normalize user input for better matching
def normalize_station_name(text):
    """Normalize station names by removing special characters and converting to lowercase"""
    replacements = {"ß": "ss", "ü": "u", "ö": "o", "ä": "a"}
    normalized = text.lower().replace(" ", "").replace("-", "")

    for orig, repl in replacements.items():
        normalized = normalized.replace(orig, repl)

    return normalized

# Populate database with station data
def populate_database():
    """Initialize database with U-Bahn station data"""
    station_data = {
        "Adenauerplatz": "900023302",
        "Afrikanische Straße": "900011102",
        "Alexanderplatz": "900100003",
        "Alt-Mariendorf": "900070301",
        "Alt-Tegel": "900089301",
        "Alt-Tempelhof": "900068202",
        "Altstadt Spandau": "900029301",
        "Amrumer Straße": "900009101",
        "Augsburger Straße": "900023202",
        "Bayerischer Platz": "900055102",
        "Berliner Straße": "900230072",
        "Bernauer Straße": "900089554",
        "Biesdorf-Süd": "900171005",
        "Birkenstraße": "900002201",
        "Bismarckstraße": "900024201",
        "Blaschkoallee": "900080201",
        "Blissestraße": "900041102",
        "Boddinstraße": "900079202",
        "Borsigwerke": "900088202",
        "Breitenbachplatz": "900051202",
        "Brandenburger Tor": "900100025",
        "Britz-Süd": "900080402",
        "Bülowstraße": "900056104",
        "Bundestag": "900003254",
        "Bundesplatz": "900044202",
        "Cottbusser Platz": "900175006",
        "Dahlem-Dorf": "900051303",
        "Deutsche Oper": "900022201",
        "Eberswalder Straße": "900110006",
        "Eisenacher Straße": "900054103",
        "Elsterwerdaer Platz": "900171006",
        "Ernst-Reuter-Platz": "900023101",
        "Fehrbelliner Platz": "900041101",
        "Frankfurter Allee": "900120001",
        "Frankfurter Tor": "900120008",
        "Franz-Neumann-Platz": "900085202",
        "Freie Universität (Thielplatz)": "900051201",
        "Friedrichsfelde": "900171002",
        "Friedrichstraße": "900100001",
        "Friedrich-Wilhelm-Platz": "900061102",
        "Gesundbrunnen": "900007102",
        "Gleisdreieck": "900017103",
        "Gneisenaustraße": "900016101",
        "Görlitzer Bahnhof": "900014101",
        "Grenzallee": "900080202",
        "Güntzelstraße": "900043201",
        "Halemweg": "900018102",
        "Hallesches Tor": "900012103",
        "Hansaplatz": "900003101",
        "Haselhorst": "900034102",
        "Hauptbahnhof": "900003201",
        "Hausvogteiplatz": "900100012",
        "Heidelberger Platz": "900045102",
        "Heinrich-Heine-Straße": "900100008",
        "Hellersdorf": "900175007",
        "Hermannplatz": "900078101",
        "Hönow": "900175010",
        "Hohenzollernplatz": "900043101",
        "Holzhauser Straße": "900097101",
        "Innsbrucker Platz": "900054105",
        "Jakob-Kaiser-Platz": "900018101",
        "Jannowitzbrücke": "900100004",
        "Johannisthaler Chaussee": "900082202",
        "Jungfernheide": "900020201",
        "Kaiserdamm": "900026202",
        "Kaiserin-Augusta-Straße": "900068302",
        "Karl-Bonhoeffer-Nervenklinik": "900096458",
        "Karl-Marx-Straße": "900078103",
        "Kaulsdorf-Nord": "900175004",
        "Kienberg (Gärten der Welt)": "900175005",
        "Kleistpark": "900054102",
        "Klosterstraße": "900100015",
        "Kochstraße": "900012102",
        "Konstanzer Straße": "900041201",
        "Kottbusser Tor": "900013102",
        "Krumme Lanke": "900050201",
        "Kurfürstendamm": "900023203",
        "Kurfürstenstraße": "900005201",
        "Kurt-Schumacher-Platz": "900086102",
        "Leinestraße": "900079201",
        "Leopoldplatz": "900009102",
        "Lichtenberg": "900160004",
        "Lindauer Allee": "900086160",
        "Lipschitzallee": "900082201",
        "Louis-Lewin-Straße": "900175015",
        "Magdalenenstraße": "900160005",
        "Märkisches Museum": "900100014",
        "Mehringdamm": "900017101",
        "Mendelssohn-Bartholdy-Park": "900005252",
        "Mierendorffplatz": "900019204",
        "Möckernbrücke": "900017104",
        "Mohrenstraße": "900100010",
        "Moritzplatz": "900013101",
        "Museumsinsel": "900100537",
        "Naturkundemuseum": "900100009",
        "Nauener Platz": "900009201",
        "Neu-Westend": "900026101",
        "Neukölln": "900078201",
        "Nollendorfplatz": "900056102",
        "Olympia-Stadion": "900025203",
        "Onkel Toms Hütte": "900050282",
        "Oranienburger Tor": "900100019",
        "Oskar-Helene-Heim": "900051301",
        "Osloer Straße": "900009202",
        "Otisstraße": "900350321",
        "Pankow": "900130002",
        "Pankstraße": "900009203",
        "Paracelsus-Bad": "900085104",
        "Paradestraße": "900068101",
        "Parchimer Allee": "900080401",
        "Paulsternstraße": "900034101",
        "Platz der Luftbrücke": "900017102",
        "Podbielskiallee": "900051302",
        "Potsdamer Platz": "900100020",
        "Prinzenstraße": "900013103",
        "Rathaus Neukölln": "900078102",
        "Rathaus Reinickendorf": "900096410",
        "Rathaus Schöneberg": "900054101",
        "Rathaus Spandau": "900029302",
        "Rathaus Steglitz": "900062202",
        "Rehberge": "900011101",
        "Reinickendorfer Straße": "900008102",
        "Residenzstraße": "900085203",
        "Richard-Wagner-Platz": "900022202",
        "Rohrdamm": "900036101",
        "Rosa-Luxemburg-Platz": "900100016",
        "Rosenthaler Platz": "900100023",
        "Rotes Rathaus": "900100045",
        "Rüdesheimer Platz": "900045101",
        "Rudow": "900083201",
        "Ruhleben": "900025202",
        "Samariterstraße": "900120009",
        "Scharnweberstraße": "900087101",
        "Schillingstraße": "900100017",
        "Schlesisches Tor": "900014102",
        "Schloßstraße": "900062203",
        "Schönhauser Allee": "900110001",
        "Schönleinstraße": "900016201",
        "Schwartzkopffstraße": "900100501",
        "Seestraße": "900140021",
        "Senefelderplatz": "900110005",
        "Siemensdamm": "900035101",
        "Sophie-Charlotte-Platz": "900022101",
        "Spichernstraße": "900042101",
        "Stadtmitte": "900100011",
        "Strausberger Platz": "900120006",
        "Südstern": "900016202",
        "Tempelhof": "900068201",
        "Theodor-Heuss-Platz": "900026201",
        "Tierpark": "900161002",
        "Turmstraße": "900003104",
        "Uhlandstraße": "900043172",
        "Ullsteinstraße": "900069271",
        "Unter den Linden": "900100513",
        "Viktoria-Luise-Platz": "900055101",
        "Vinetastraße": "900130011",
        "Voltastraße": "900007103",
        "Walther-Schreiber-Platz": "900061101",
        "Warschauer Straße": "900120004",
        "Weberwiese": "900120025",
        "Wedding": "900009104",
        "Weinmeisterstraße": "900230172",
        "Westhafen": "900001201",
        "Westphalweg": "900070101",
        "Wilmersdorfer Straße": "900024202",
        "Wittenau": "900096101",
        "Wittenbergplatz": "900056101",
        "Wuhletal": "900175001",
        "Wutzkyallee": "900083102",
        "Yorckstraße": "900058103",
        "Zitadelle": "900033101",
        "Zoologischer Garten": "900023201",
        "Zwickauer Damm": "900083101"
    }

    with app.app_context():
        db.create_all()
        for station_name, station_id in station_data.items():
            if not Station.query.filter_by(name=station_name).first():
                db.session.add(Station(station_name, station_id))
        db.session.commit()
        print(f"Database populated with {len(station_data)} stations")

def fetch_live_arrivals(station_id, results=15):
    """Fetch live U-Bahn arrivals for a given station"""
    url = f"{BVG_API_BASE}/stops/{station_id}/arrivals"
    params = {
        "results": results,
        "suburban": False,  # Disable S-Bahn
        "subway": True,     # Enable U-Bahn only
        "tram": False,
        "bus": False,
        "ferry": False,
        "express": False,
        "regional": False,
        "linesOfStops": False,
        "remarks": False,
        "language": "en",
        "pretty": "false"
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        formatted_arrivals = []

        for arr in data.get("arrivals", []):
            # Get line name and direction information
            line_name = arr.get("line", {}).get("name", "?")
            destination = arr.get("direction") or arr.get("provenance", "?")
            arrival_time_str = arr.get("when")

            if arrival_time_str:
                try:
                    arrival_time = datetime.fromisoformat(arrival_time_str).astimezone(timezone.utc)
                    now_time = datetime.now(timezone.utc)
                    seconds_diff = (arrival_time - now_time).total_seconds()
                    minutes = ceil(seconds_diff / 60)
                    
                    # Skip arrivals less than 1 minute away
                    if minutes < 1:
                        continue
                except Exception as e:
                    print(f"Error parsing time: {e}")
                    continue

                # If line name contains multiple U-Bahn lines, split them
                lines = re.split(r'[\s,\/]+', line_name)
                lines = [l for l in lines if l]  # Filter empty elements
                if not lines:
                    lines = [line_name]

                # Add each line as a separate entry
                for l in lines:
                    formatted_arrivals.append(f"🚆 {l} → {destination} ({minutes} min)")

        return formatted_arrivals if formatted_arrivals else ["No U-Bahn arrivals found"]

    except requests.exceptions.RequestException as e:
        print(f"API request failed: {e}")
        return ["Service temporarily unavailable"]
    except Exception as e:
        print(f"Unexpected error: {e}")
        return ["Error fetching arrivals"]

@app.route("/")
def index():
    """Serve the main page"""
    return render_template("index.html")

@app.route("/get_arrivals", methods=["POST"])
def get_arrivals():
    """Get live arrivals for a station"""
    try:
        data = request.get_json()
        if not data or not data.get("station"):
            return jsonify({"error": "Station name is required"}), 400

        user_input = data.get("station")
        normalized_input = normalize_station_name(user_input)

        # Find best match using both normalized and exact names
        station = Station.query.filter(
            (Station.normalized_name.like(f"%{normalized_input}%")) |
            (Station.name.ilike(f"%{user_input}%"))
        ).first()

        if not station:
            return jsonify({"error": "Station not found"}), 404

        arrivals = fetch_live_arrivals(station.id)
        return jsonify(arrivals)

    except Exception as e:
        print(f"Error in get_arrivals: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route("/autocomplete", methods=["GET"])
def autocomplete():
    """Provide station name autocomplete suggestions"""
    try:
        query = request.args.get("query", "").strip()
        if not query or len(query) < 2:
            return jsonify([])

        query_normalized = normalize_station_name(query)
        results = Station.query.filter(
            (Station.normalized_name.like(f"%{query_normalized}%")) |
            (Station.name.ilike(f"%{query}%"))
        ).limit(5).all()

        return jsonify([station.name for station in results])

    except Exception as e:
        print(f"Error in autocomplete: {e}")
        return jsonify([])

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({"error": "Not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return jsonify({"error": "Internal server error"}), 500

if __name__ == "__main__":
    populate_database()
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("DEBUG", "True").lower() == "true"
    app.run(host="0.0.0.0", port=port, debug=debug)