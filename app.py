"""
F1 Analytics - Main Flask Application
"""
from flask import Flask, send_file, jsonify, request
from flask_cors import CORS
from config import Config
import os
import json

def create_app():
    app = Flask(__name__, 
                static_folder='static',
                template_folder='templates')
    
    app.config.from_object(Config)
    CORS(app)
    
    # Try to connect to MySQL, fallback to demo mode
    db_available = False
    try:
        from models.database import db
        db.init_app(app)
        with app.app_context():
            db.create_all()
        db_available = True
        
        # Register real API blueprints
        from routes.api_dashboard import dashboard_bp
        from routes.api_analytics import analytics_bp
        from routes.api_auth import auth_bp
        app.register_blueprint(dashboard_bp)
        app.register_blueprint(analytics_bp)
        app.register_blueprint(auth_bp)
        print("[OK] MySQL connected - Live mode")
    except Exception as e:
        print(f"[WARN] MySQL not available - Demo mode with sample data")
        register_demo_routes(app)
    
    # Serve the SPA
    @app.route('/')
    def index():
        return send_file('templates/index.html')
    
    return app


def register_demo_routes(app):
    """Fallback demo routes with sample data when MySQL is unavailable."""
    
    # Demo F1 2025 data
    DEMO_DRIVERS = [
        {"position":1,"abbreviation":"VER","first_name":"Max","last_name":"Verstappen","full_name":"Max Verstappen","driver_number":1,"nationality":"Dutch","country_flag":"🇳🇱","photo_url":"","team":"Red Bull Racing","team_color":"#3671C6","points":161,"wins":5,"podiums":8},
        {"position":2,"abbreviation":"NOR","first_name":"Lando","last_name":"Norris","full_name":"Lando Norris","driver_number":4,"nationality":"British","country_flag":"🇬🇧","photo_url":"","team":"McLaren","team_color":"#FF8000","points":154,"wins":3,"podiums":7},
        {"position":3,"abbreviation":"LEC","first_name":"Charles","last_name":"Leclerc","full_name":"Charles Leclerc","driver_number":16,"nationality":"Monegasque","country_flag":"🇲🇨","photo_url":"","team":"Ferrari","team_color":"#E80020","points":138,"wins":2,"podiums":6},
        {"position":4,"abbreviation":"PIA","first_name":"Oscar","last_name":"Piastri","full_name":"Oscar Piastri","driver_number":81,"nationality":"Australian","country_flag":"🇦🇺","photo_url":"","team":"McLaren","team_color":"#FF8000","points":126,"wins":2,"podiums":5},
        {"position":5,"abbreviation":"SAI","first_name":"Carlos","last_name":"Sainz","full_name":"Carlos Sainz","driver_number":55,"nationality":"Spanish","country_flag":"🇪🇸","photo_url":"","team":"Williams","team_color":"#64C4FF","points":108,"wins":1,"podiums":4},
        {"position":6,"abbreviation":"HAM","first_name":"Lewis","last_name":"Hamilton","full_name":"Lewis Hamilton","driver_number":44,"nationality":"British","country_flag":"🇬🇧","photo_url":"","team":"Ferrari","team_color":"#E80020","points":96,"wins":1,"podiums":4},
        {"position":7,"abbreviation":"RUS","first_name":"George","last_name":"Russell","full_name":"George Russell","driver_number":63,"nationality":"British","country_flag":"🇬🇧","photo_url":"","team":"Mercedes","team_color":"#27F4D2","points":91,"wins":1,"podiums":3},
        {"position":8,"abbreviation":"ANT","first_name":"Andrea Kimi","last_name":"Antonelli","full_name":"Andrea Kimi Antonelli","driver_number":12,"nationality":"Italian","country_flag":"🇮🇹","photo_url":"","team":"Mercedes","team_color":"#27F4D2","points":78,"wins":0,"podiums":3},
        {"position":9,"abbreviation":"GAS","first_name":"Pierre","last_name":"Gasly","full_name":"Pierre Gasly","driver_number":10,"nationality":"French","country_flag":"🇫🇷","photo_url":"","team":"Alpine","team_color":"#0093CC","points":52,"wins":0,"podiums":1},
        {"position":10,"abbreviation":"ALO","first_name":"Fernando","last_name":"Alonso","full_name":"Fernando Alonso","driver_number":14,"nationality":"Spanish","country_flag":"🇪🇸","photo_url":"","team":"Aston Martin","team_color":"#229971","points":48,"wins":0,"podiums":1},
        {"position":11,"abbreviation":"STR","first_name":"Lance","last_name":"Stroll","full_name":"Lance Stroll","driver_number":18,"nationality":"Canadian","country_flag":"🇨🇦","photo_url":"","team":"Aston Martin","team_color":"#229971","points":28,"wins":0,"podiums":0},
        {"position":12,"abbreviation":"TSU","first_name":"Yuki","last_name":"Tsunoda","full_name":"Yuki Tsunoda","driver_number":22,"nationality":"Japanese","country_flag":"🇯🇵","photo_url":"","team":"RB","team_color":"#6692FF","points":26,"wins":0,"podiums":0},
        {"position":13,"abbreviation":"HUL","first_name":"Nico","last_name":"Hulkenberg","full_name":"Nico Hulkenberg","driver_number":27,"nationality":"German","country_flag":"🇩🇪","photo_url":"","team":"Kick Sauber","team_color":"#52E252","points":18,"wins":0,"podiums":0},
        {"position":14,"abbreviation":"DOO","first_name":"Jack","last_name":"Doohan","full_name":"Jack Doohan","driver_number":7,"nationality":"Australian","country_flag":"🇦🇺","photo_url":"","team":"Alpine","team_color":"#0093CC","points":14,"wins":0,"podiums":0},
        {"position":15,"abbreviation":"LAW","first_name":"Liam","last_name":"Lawson","full_name":"Liam Lawson","driver_number":30,"nationality":"New Zealander","country_flag":"🇳🇿","photo_url":"","team":"RB","team_color":"#6692FF","points":12,"wins":0,"podiums":0},
        {"position":16,"abbreviation":"HAD","first_name":"Isack","last_name":"Hadjar","full_name":"Isack Hadjar","driver_number":6,"nationality":"French","country_flag":"🇫🇷","photo_url":"","team":"RB","team_color":"#6692FF","points":10,"wins":0,"podiums":0},
        {"position":17,"abbreviation":"BOR","first_name":"Gabriel","last_name":"Bortoleto","full_name":"Gabriel Bortoleto","driver_number":5,"nationality":"Brazilian","country_flag":"🇧🇷","photo_url":"","team":"Kick Sauber","team_color":"#52E252","points":6,"wins":0,"podiums":0},
        {"position":18,"abbreviation":"BEA","first_name":"Oliver","last_name":"Bearman","full_name":"Oliver Bearman","driver_number":87,"nationality":"British","country_flag":"🇬🇧","photo_url":"","team":"Haas F1 Team","team_color":"#B6BABD","points":4,"wins":0,"podiums":0},
        {"position":19,"abbreviation":"OCO","first_name":"Esteban","last_name":"Ocon","full_name":"Esteban Ocon","driver_number":31,"nationality":"French","country_flag":"🇫🇷","photo_url":"","team":"Haas F1 Team","team_color":"#B6BABD","points":2,"wins":0,"podiums":0},
        {"position":20,"abbreviation":"ALB","first_name":"Alexander","last_name":"Albon","full_name":"Alexander Albon","driver_number":23,"nationality":"Thai","country_flag":"🇹🇭","photo_url":"","team":"Williams","team_color":"#64C4FF","points":1,"wins":0,"podiums":0},
    ]
    
    DEMO_CONSTRUCTORS = [
        {"position":1,"name":"McLaren","full_name":"McLaren F1 Team","team_color":"#FF8000","points":280,"drivers":[{"abbreviation":"NOR","full_name":"Lando Norris","points":154},{"abbreviation":"PIA","full_name":"Oscar Piastri","points":126}]},
        {"position":2,"name":"Red Bull Racing","full_name":"Oracle Red Bull Racing","team_color":"#3671C6","points":171,"drivers":[{"abbreviation":"VER","full_name":"Max Verstappen","points":161},{"abbreviation":"LAW","full_name":"Liam Lawson","points":10}]},
        {"position":3,"name":"Ferrari","full_name":"Scuderia Ferrari","team_color":"#E80020","points":234,"drivers":[{"abbreviation":"LEC","full_name":"Charles Leclerc","points":138},{"abbreviation":"HAM","full_name":"Lewis Hamilton","points":96}]},
        {"position":4,"name":"Mercedes","full_name":"Mercedes-AMG Petronas","team_color":"#27F4D2","points":169,"drivers":[{"abbreviation":"RUS","full_name":"George Russell","points":91},{"abbreviation":"ANT","full_name":"Kimi Antonelli","points":78}]},
        {"position":5,"name":"Williams","full_name":"Williams Racing","team_color":"#64C4FF","points":109,"drivers":[{"abbreviation":"SAI","full_name":"Carlos Sainz","points":108},{"abbreviation":"ALB","full_name":"Alexander Albon","points":1}]},
        {"position":6,"name":"Aston Martin","full_name":"Aston Martin Aramco","team_color":"#229971","points":76,"drivers":[{"abbreviation":"ALO","full_name":"Fernando Alonso","points":48},{"abbreviation":"STR","full_name":"Lance Stroll","points":28}]},
        {"position":7,"name":"Alpine","full_name":"BWT Alpine F1 Team","team_color":"#0093CC","points":66,"drivers":[{"abbreviation":"GAS","full_name":"Pierre Gasly","points":52},{"abbreviation":"DOO","full_name":"Jack Doohan","points":14}]},
        {"position":8,"name":"RB","full_name":"Visa Cash App RB","team_color":"#6692FF","points":48,"drivers":[{"abbreviation":"TSU","full_name":"Yuki Tsunoda","points":26},{"abbreviation":"HAD","full_name":"Isack Hadjar","points":22}]},
        {"position":9,"name":"Kick Sauber","full_name":"Stake F1 Team Kick Sauber","team_color":"#52E252","points":24,"drivers":[{"abbreviation":"HUL","full_name":"Nico Hulkenberg","points":18},{"abbreviation":"BOR","full_name":"Gabriel Bortoleto","points":6}]},
        {"position":10,"name":"Haas F1 Team","full_name":"MoneyGram Haas F1 Team","team_color":"#B6BABD","points":6,"drivers":[{"abbreviation":"BEA","full_name":"Oliver Bearman","points":4},{"abbreviation":"OCO","full_name":"Esteban Ocon","points":2}]},
    ]
    
    DEMO_RACES = [
        {"round":1,"name":"Australian Grand Prix","country":"Australia","status":"completed"},
        {"round":2,"name":"Chinese Grand Prix","country":"China","status":"completed"},
        {"round":3,"name":"Japanese Grand Prix","country":"Japan","status":"completed"},
        {"round":4,"name":"Bahrain Grand Prix","country":"Bahrain","status":"completed"},
        {"round":5,"name":"Saudi Arabian Grand Prix","country":"Saudi Arabia","status":"completed"},
        {"round":6,"name":"Miami Grand Prix","country":"United States","status":"upcoming"},
        {"round":7,"name":"Emilia Romagna Grand Prix","country":"Italy","status":"upcoming"},
    ]

    DEMO_PERF = {
        "races": [r["name"] for r in DEMO_RACES[:5]],
        "teams": [
            {"name":"McLaren","color":"#FF8000","points":[42,110,168,230,280]},
            {"name":"Ferrari","color":"#E80020","points":[38,88,145,190,234]},
            {"name":"Red Bull Racing","color":"#3671C6","points":[50,90,120,148,171]},
            {"name":"Mercedes","color":"#27F4D2","points":[25,60,100,138,169]},
            {"name":"Williams","color":"#64C4FF","points":[15,35,60,85,109]},
            {"name":"Aston Martin","color":"#229971","points":[10,25,42,60,76]},
            {"name":"Alpine","color":"#0093CC","points":[8,20,35,50,66]},
            {"name":"RB","color":"#6692FF","points":[6,15,28,38,48]},
            {"name":"Kick Sauber","color":"#52E252","points":[2,8,14,18,24]},
            {"name":"Haas F1 Team","color":"#B6BABD","points":[0,0,2,4,6]},
        ]
    }

    @app.route('/api/dashboard/driver-standings')
    def demo_driver_standings():
        return jsonify(DEMO_DRIVERS)

    @app.route('/api/dashboard/constructor-standings')
    def demo_constructor_standings():
        return jsonify(DEMO_CONSTRUCTORS)

    @app.route('/api/dashboard/race-calendar')
    def demo_race_calendar():
        return jsonify(DEMO_RACES)

    @app.route('/api/dashboard/team-performance')
    def demo_team_performance():
        return jsonify(DEMO_PERF)

    @app.route('/api/analytics/races')
    def demo_analytics_races():
        return jsonify(DEMO_RACES)

    @app.route('/api/analytics/drivers')
    def demo_analytics_drivers():
        return jsonify([{"abbreviation":d["abbreviation"],"full_name":d["full_name"],"team":d["team"],"team_color":d["team_color"]} for d in DEMO_DRIVERS])

    @app.route('/api/analytics/lap-times')
    def demo_lap_times():
        import fastf1
        season = request.args.get('season', 2025, type=int)
        round_num = request.args.get('round', 1, type=int)
        d1 = request.args.get('driver1', 'VER')
        d2 = request.args.get('driver2', 'NOR')
        
        try:
            ff1_session = fastf1.get_session(season, round_num, 'R')
            ff1_session.load(telemetry=False, weather=False)
            
            result = []
            for abbr in [d1, d2]:
                d_info = next((x for x in DEMO_DRIVERS if x["abbreviation"]==abbr), DEMO_DRIVERS[0])
                try:
                    driver_laps = ff1_session.laps.pick_drivers(abbr)
                    laps = []
                    for _, lap in driver_laps.iterrows():
                        if pd.notna(lap['LapTime']):
                            ms = int(lap['LapTime'].total_seconds() * 1000)
                            mins = ms // 60000
                            secs = (ms % 60000) / 1000
                            laps.append({
                                "lap": int(lap['LapNumber']),
                                "time_ms": ms,
                                "time_str": f"{mins}:{secs:06.3f}",
                                "compound": str(lap['Compound']) if pd.notna(lap['Compound']) else "UNKNOWN",
                                "stint": int(lap['Stint']) if pd.notna(lap['Stint']) else 1,
                                "position": int(lap['Position']) if pd.notna(lap['Position']) else 0
                            })
                    result.append({"driver":abbr,"full_name":d_info["full_name"],"team":d_info["team"],"team_color":d_info["team_color"],"laps":laps})
                except Exception:
                    pass
            return jsonify(result)
        except Exception as e:
            return jsonify([])

    @app.route('/api/analytics/position-changes')
    def demo_positions():
        import random
        drivers_data = []
        for d in DEMO_DRIVERS:
            positions = {}
            pos = d["position"]
            for lap in range(1, 58):
                pos = max(1, min(20, pos + random.choice([-1,0,0,0,0,1])))
                positions[str(lap)] = pos
            drivers_data.append({"driver":d["abbreviation"],"team_color":d["team_color"],"positions":positions})
        return jsonify({"max_lap":57,"drivers":drivers_data})

    @app.route('/api/analytics/qualifying')
    def demo_qualifying():
        result = []
        for i, d in enumerate(DEMO_DRIVERS):
            base = 78.5 + i * 0.15
            q1 = f"1:{base:.3f}"
            q2 = f"1:{base-0.2:.3f}" if i < 15 else None
            q3 = f"1:{base-0.4:.3f}" if i < 10 else None
            result.append({"position":i+1,"driver":d["abbreviation"],"full_name":d["full_name"],"team":d["team"],"team_color":d["team_color"],"q1":q1,"q2":q2,"q3":q3})
        return jsonify(result)

    @app.route('/api/analytics/stints')
    def demo_stints():
        import random
        result = []
        for d in DEMO_DRIVERS:
            compounds = ["SOFT","MEDIUM","HARD"]
            stints = []
            lap = 1
            for s in range(1, random.randint(2,4)):
                c = compounds[min(s-1, 2)]
                length = random.randint(12, 25)
                stints.append({"stint":s,"compound":c,"start_lap":lap,"end_lap":lap+length-1,"laps_count":length})
                lap += length
            result.append({"driver":d["abbreviation"],"team_color":d["team_color"],"stints":stints})
        return jsonify(result)

    @app.route('/api/analytics/telemetry')
    def demo_telemetry():
        import fastf1
        season = request.args.get('season', 2025, type=int)
        round_num = request.args.get('round', 1, type=int)
        d1 = request.args.get('driver1', 'VER')
        d2 = request.args.get('driver2', 'NOR')
        
        try:
            ff1_session = fastf1.get_session(season, round_num, 'R')
            ff1_session.load()
            
            result = {}
            for abbr in [d1, d2]:
                d_info = next((x for x in DEMO_DRIVERS if x["abbreviation"]==abbr), DEMO_DRIVERS[0])
                try:
                    driver_laps = ff1_session.laps.pick_drivers(abbr)
                    fastest_lap = driver_laps.pick_fastest()
                    tel = fastest_lap.get_telemetry()
                    
                    # Higher accuracy downsampling (keep ~1000 points)
                    step = max(1, len(tel) // 1000)
                    tel_sampled = tel.iloc[::step]
                    
                    result[abbr] = {
                        "driver": abbr,
                        "team": d_info["team"],
                        "team_color": d_info["team_color"],
                        "lap_number": int(fastest_lap['LapNumber']),
                        "data": {
                            "distance": tel_sampled['Distance'].fillna(0).tolist(),
                            "speed": tel_sampled['Speed'].fillna(0).tolist(),
                            "throttle": tel_sampled['Throttle'].fillna(0).tolist(),
                            "brake": [1 if b else 0 for b in tel_sampled['Brake'].fillna(False)],
                            "gear": tel_sampled['nGear'].fillna(0).tolist(),
                            "rpm": tel_sampled['RPM'].fillna(0).tolist(),
                            "drs": tel_sampled['DRS'].fillna(0).tolist()
                        }
                    }
                except Exception as e:
                    print(f"Telemetry err for {abbr}: {e}")
            return jsonify(result)
        except Exception as e:
            return jsonify({"error": str(e)})

    @app.route('/api/analytics/circuit-map')
    def demo_circuit_map():
        import math
        n = 200
        x = [int(3000*math.cos(2*math.pi*i/n) + 1000*math.cos(6*math.pi*i/n)) for i in range(n)]
        y = [int(2000*math.sin(2*math.pi*i/n) + 500*math.sin(4*math.pi*i/n)) for i in range(n)]
        return jsonify({"x":x,"y":y,"circuit_name":"Demo Circuit"})

    @app.route('/api/analytics/gps-data')
    def demo_gps_data():
        import math
        result = {}
        for i, d in enumerate(DEMO_DRIVERS[:10]):
            n = 200
            offset = i * 5
            x = [int(3000*math.cos(2*math.pi*(j+offset)/n) + 1000*math.cos(6*math.pi*(j+offset)/n)) for j in range(n)]
            y = [int(2000*math.sin(2*math.pi*(j+offset)/n) + 500*math.sin(4*math.pi*(j+offset)/n)) for j in range(n)]
            speed = [int(250 + 50*math.sin(j/20)) for j in range(n)]
            result[d["abbreviation"]] = {"driver":d["abbreviation"],"team_color":d["team_color"],"x":x,"y":y,"speed":speed}
        return jsonify(result)

    @app.route('/api/auth/login', methods=['POST'])
    def demo_login():
        data = request.get_json() or {}
        if data.get('username') == 'admin' and data.get('password') == 'admin':
            return jsonify({"success":True,"user":{"id":1,"username":"admin","email":"admin@f1.com","role":"admin"}})
        return jsonify({"error":"Invalid credentials"}), 401

    @app.route('/api/auth/register', methods=['POST'])
    def demo_register():
        return jsonify({"success":True,"message":"Registration successful (demo mode)"})

    @app.route('/api/auth/me')
    def demo_me():
        return jsonify({"authenticated":False}), 401


app = create_app()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)