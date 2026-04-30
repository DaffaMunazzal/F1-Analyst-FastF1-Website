"""Analytics API routes - telemetry, lap analysis, race replay."""
from flask import Blueprint, jsonify, request
from models.database import db, Driver, Constructor, Race, Session, LapTime, Telemetry, GpsPosition, QualifyingResult, RaceResult
import fastf1
import pandas as pd
import numpy as np
from config import Config

analytics_bp = Blueprint('analytics', __name__, url_prefix='/api/analytics')

fastf1.Cache.enable_cache(Config.FASTF1_CACHE_DIR)

# In-memory cache to prevent concurrent Pandas parsing bottlenecks 
# when multiple endpoints request the same session simultaneously
SESSION_CACHE = {}

def get_loaded_session(season, round_num, session_type, needs_telemetry=False):
    cache_key = f"{season}_{round_num}_{session_type}"
    
    if cache_key in SESSION_CACHE:
        sess = SESSION_CACHE[cache_key]
        if needs_telemetry and not getattr(sess, '_telemetry_loaded', False):
            sess.load()
            sess._telemetry_loaded = True
        return sess
        
    sess = fastf1.get_session(season, round_num, session_type)
    if needs_telemetry:
        sess.load()
        sess._telemetry_loaded = True
    else:
        sess.load(telemetry=False, weather=False)
        sess._telemetry_loaded = False
        
    SESSION_CACHE[cache_key] = sess
    return sess


@analytics_bp.route('/lap-times')
def get_lap_times():
    """Get lap times for a session."""
    season = request.args.get('season', 2025, type=int)
    round_num = request.args.get('round', 1, type=int)
    session_type = request.args.get('session', 'R')
    driver_abbr = request.args.get('driver', None)
    
    race = Race.query.filter_by(season=season, round_number=round_num).first()
    
    # Try fetching from DB first
    laps = []
    if race:
        session = Session.query.filter_by(race_id=race.id, session_type=session_type).first()
        if session:
            query = LapTime.query.filter_by(session_id=session.id)
            if driver_abbr:
                driver = Driver.query.filter_by(abbreviation=driver_abbr, season=season).first()
                if driver: query = query.filter_by(driver_id=driver.id)
            laps = query.order_by(LapTime.lap_number.asc()).all()
    
    drivers_data = {}
    
    if len(laps) > 0:
        # Group by driver from DB
        for lap in laps:
            d = Driver.query.get(lap.driver_id)
            if not d: continue
            abbr = d.abbreviation
            if abbr not in drivers_data:
                drivers_data[abbr] = {
                    'driver': abbr, 'full_name': d.full_name,
                    'team': d.constructor.name if d.constructor else '',
                    'team_color': d.constructor.team_color if d.constructor else '#FFF',
                    'laps': []
                }
            drivers_data[abbr]['laps'].append({
                'lap': lap.lap_number, 'time_ms': lap.lap_time_ms, 'time_str': lap.lap_time_str,
                'compound': lap.compound, 'stint': lap.stint, 'position': lap.position,
            })
    else:
        # Fallback to FastF1 if DB is empty for this round
        try:
            ff1_session = get_loaded_session(season, round_num, session_type, needs_telemetry=False)
            
            drivers_to_fetch = [driver_abbr] if driver_abbr else ff1_session.laps['Driver'].unique()
            
            for abbr in drivers_to_fetch:
                d = Driver.query.filter_by(abbreviation=abbr, season=season).first()
                if not d: continue
                
                driver_laps = ff1_session.laps.pick_drivers(abbr)
                laps_list = []
                for _, lap in driver_laps.iterrows():
                    if pd.notna(lap['LapTime']):
                        ms = int(lap['LapTime'].total_seconds() * 1000)
                        mins = ms // 60000
                        secs = (ms % 60000) / 1000
                        laps_list.append({
                            'lap': int(lap['LapNumber']), 'time_ms': ms, 'time_str': f"{mins}:{secs:06.3f}",
                            'compound': str(lap['Compound']) if pd.notna(lap['Compound']) else "UNKNOWN",
                            'stint': int(lap['Stint']) if pd.notna(lap['Stint']) else 1,
                            'position': int(lap['Position']) if pd.notna(lap['Position']) else 0
                        })
                
                if laps_list:
                    drivers_data[abbr] = {
                        'driver': abbr, 'full_name': d.full_name,
                        'team': d.constructor.name if d.constructor else '',
                        'team_color': d.constructor.team_color if d.constructor else '#FFF',
                        'laps': laps_list
                    }
        except Exception as e:
            return jsonify({'error': str(e)}), 500
            
    return jsonify(list(drivers_data.values()))


@analytics_bp.route('/qualifying')
def get_qualifying():
    """Get qualifying results with Q1/Q2/Q3 times."""
    season = request.args.get('season', 2025, type=int)
    round_num = request.args.get('round', 1, type=int)
    
    try:
        # Fetch directly from FastF1 since qualifying results might not be seeded
        ff1_session = get_loaded_session(season, round_num, 'Q', needs_telemetry=False)
        
        results = ff1_session.results
        data = []
        
        for _, r in results.iterrows():
            d = Driver.query.filter_by(abbreviation=r['Abbreviation'], season=season).first()
            
            q1 = str(r['Q1']).split('0 days ')[-1][:11] if pd.notna(r['Q1']) else None
            q2 = str(r['Q2']).split('0 days ')[-1][:11] if pd.notna(r['Q2']) else None
            q3 = str(r['Q3']).split('0 days ')[-1][:11] if pd.notna(r['Q3']) else None
            
            # Format times removing leading zeros
            if q1 and q1.startswith('00:0'): q1 = q1[4:]
            elif q1 and q1.startswith('00:'): q1 = q1[3:]
            if q2 and q2.startswith('00:0'): q2 = q2[4:]
            elif q2 and q2.startswith('00:'): q2 = q2[3:]
            if q3 and q3.startswith('00:0'): q3 = q3[4:]
            elif q3 and q3.startswith('00:'): q3 = q3[3:]
            
            data.append({
                'position': int(r['Position']) if pd.notna(r['Position']) else '-',
                'driver': r['Abbreviation'],
                'full_name': r['FullName'],
                'team': r['TeamName'],
                'team_color': d.constructor.team_color if d and d.constructor else '#FFF',
                'q1': q1,
                'q2': q2,
                'q3': q3,
            })
        
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@analytics_bp.route('/stints')
def get_stints():
    """Get stint/tyre strategy data."""
    season = request.args.get('season', 2025, type=int)
    round_num = request.args.get('round', 1, type=int)
    
    race = Race.query.filter_by(season=season, round_number=round_num).first()
    laps = []
    if race:
        session = Session.query.filter_by(race_id=race.id, session_type='R').first()
        if session:
            laps = LapTime.query.filter_by(session_id=session.id).order_by(
                LapTime.driver_id.asc(), LapTime.lap_number.asc()
            ).all()
    
    drivers_stints = {}
    
    if len(laps) > 0:
        for lap in laps:
            d = Driver.query.get(lap.driver_id)
            if not d: continue
            abbr = d.abbreviation
            if abbr not in drivers_stints:
                drivers_stints[abbr] = {
                    'driver': abbr, 'team_color': d.constructor.team_color if d.constructor else '#FFF', 'stints': []
                }
            
            stint_num = lap.stint or 1
            compound = lap.compound or 'UNKNOWN'
            
            existing_stint = next((s for s in drivers_stints[abbr]['stints'] if s['stint'] == stint_num), None)
            if existing_stint:
                existing_stint['end_lap'] = lap.lap_number
                existing_stint['laps_count'] += 1
            else:
                drivers_stints[abbr]['stints'].append({
                    'stint': stint_num, 'compound': compound,
                    'start_lap': lap.lap_number, 'end_lap': lap.lap_number, 'laps_count': 1,
                })
    else:
        # Fallback to FastF1
        try:
            ff1_session = get_loaded_session(season, round_num, 'R', needs_telemetry=False)
            
            for abbr in ff1_session.laps['Driver'].unique():
                d = Driver.query.filter_by(abbreviation=abbr, season=season).first()
                if not d: continue
                
                driver_laps = ff1_session.laps.pick_drivers(abbr)
                drivers_stints[abbr] = {
                    'driver': abbr, 'team_color': d.constructor.team_color if d.constructor else '#FFF', 'stints': []
                }
                
                for _, lap in driver_laps.iterrows():
                    stint_num = int(lap['Stint']) if pd.notna(lap['Stint']) else 1
                    compound = str(lap['Compound']) if pd.notna(lap['Compound']) else 'UNKNOWN'
                    lap_num = int(lap['LapNumber'])
                    
                    existing_stint = next((s for s in drivers_stints[abbr]['stints'] if s['stint'] == stint_num), None)
                    if existing_stint:
                        existing_stint['end_lap'] = lap_num
                        existing_stint['laps_count'] += 1
                    else:
                        drivers_stints[abbr]['stints'].append({
                            'stint': stint_num, 'compound': compound,
                            'start_lap': lap_num, 'end_lap': lap_num, 'laps_count': 1,
                        })
        except Exception as e:
            return jsonify({'error': str(e)}), 500
            
    return jsonify(list(drivers_stints.values()))


@analytics_bp.route('/telemetry')
def get_telemetry():
    """Get telemetry data - fetched live from FastF1 if not in DB."""
    season = request.args.get('season', 2025, type=int)
    round_num = request.args.get('round', 1, type=int)
    session_type = request.args.get('session', 'R')
    driver1 = request.args.get('driver1', 'VER')
    driver2 = request.args.get('driver2', 'NOR')
    lap = request.args.get('lap', 'fastest')
    
    try:
        ff1_session = get_loaded_session(season, round_num, session_type, needs_telemetry=True)
        
        result = {}
        for driver_abbr in [driver1, driver2]:
            try:
                driver_laps = ff1_session.laps.pick_drivers(driver_abbr)
                if len(driver_laps) == 0: continue
                
                if lap == 'fastest':
                    target_lap = driver_laps.pick_fastest()
                else:
                    target_lap = driver_laps[driver_laps['LapNumber'] == int(lap)].iloc[0]
                
                if pd.isna(target_lap['LapTime']): continue
                
                tel = target_lap.get_telemetry()
                
                # Downsample for performance but keep high accuracy (~1000 points)
                step = max(1, len(tel) // 1000)
                tel_sampled = tel.iloc[::step]
                
                team_name = ''
                team_color = '#FFFFFF'
                d = Driver.query.filter_by(abbreviation=driver_abbr, season=season).first()
                if d and d.constructor:
                    team_name = d.constructor.name
                    team_color = d.constructor.team_color
                
                result[driver_abbr] = {
                    'driver': driver_abbr,
                    'team': team_name,
                    'team_color': team_color,
                    'lap_number': int(target_lap['LapNumber']),
                    'lap_time': str(target_lap['LapTime']),
                    'data': {
                        'distance': tel_sampled['Distance'].tolist(),
                        'speed': tel_sampled['Speed'].tolist(),
                        'throttle': tel_sampled['Throttle'].tolist(),
                        'brake': tel_sampled['Brake'].astype(int).tolist(),
                        'gear': tel_sampled['nGear'].tolist(),
                        'rpm': tel_sampled['RPM'].tolist(),
                        'drs': tel_sampled['DRS'].tolist(),
                    }
                }
            except Exception as e:
                print(f"Skipping telemetry for {driver_abbr}: {e}")
                continue
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@analytics_bp.route('/position-changes')
def position_changes():
    """Get position changes through the race (for qualifying to race progression chart)."""
    season = request.args.get('season', 2025, type=int)
    round_num = request.args.get('round', 1, type=int)
    
    race = Race.query.filter_by(season=season, round_number=round_num).first()
    if not race:
        return jsonify({'error': 'Race not found'}), 404
    
    session = Session.query.filter_by(race_id=race.id, session_type='R').first()
    if not session:
        return jsonify({'error': 'Session not found'}), 404
    
    laps = LapTime.query.filter_by(session_id=session.id).order_by(
        LapTime.lap_number.asc()
    ).all()
    
    drivers_positions = {}
    max_lap = 0
    
    for lap in laps:
        if lap.position is None:
            continue
        d = Driver.query.get(lap.driver_id)
        if not d:
            continue
        abbr = d.abbreviation
        if abbr not in drivers_positions:
            drivers_positions[abbr] = {
                'driver': abbr,
                'team_color': d.constructor.team_color if d.constructor else '#FFF',
                'positions': {}
            }
        drivers_positions[abbr]['positions'][lap.lap_number] = lap.position
        max_lap = max(max_lap, lap.lap_number)
    
    return jsonify({
        'max_lap': max_lap,
        'drivers': list(drivers_positions.values())
    })


@analytics_bp.route('/gps-data')
def gps_data():
    """Get synchronized GPS positional data for drivers for a specific lap."""
    season = request.args.get('season', 2025, type=int)
    round_num = request.args.get('round', 1, type=int)
    lap_num = request.args.get('lap', 'last')
    
    try:
        ff1_session = get_loaded_session(season, round_num, 'R', needs_telemetry=True)
        
        drivers_gps = {}
        
        if lap_num == 'last':
            # Get the maximum lap number achieved by any driver
            max_lap = ff1_session.laps['LapNumber'].max()
            
            # Find the leader's laps (the one who completed the max lap first)
            leaders_lap = ff1_session.laps[ff1_session.laps['LapNumber'] == max_lap].sort_values('SessionTime').iloc[0]
            end_time = leaders_lap['SessionTime']
            start_time = end_time - leaders_lap['LapTime']
            
            for driver_abbr in ff1_session.laps['Driver'].unique():
                try:
                    # Get full race pos data
                    pos = ff1_session.pos_data[driver_abbr]
                    
                    # Slice pos data to just the leader's last lap time window!
                    # This ensures all drivers are plotted exactly where they were during this real time window
                    pos_sliced = pos[(pos['SessionTime'] >= start_time) & (pos['SessionTime'] <= end_time)]
                    
                    if pos_sliced.empty:
                        continue
                        
                    # Downsample to a manageable frame count (e.g., ~200-300 frames for one lap)
                    step = max(1, len(pos_sliced) // 250)
                    pos_sampled = pos_sliced.iloc[::step]
                    
                    d = Driver.query.filter_by(abbreviation=driver_abbr, season=season).first()
                    team_color = d.constructor.team_color if d and d.constructor else '#FFF'
                    
                    drivers_gps[driver_abbr] = {
                        'driver': driver_abbr,
                        'team_color': team_color,
                        'x': pos_sampled['X'].tolist(),
                        'y': pos_sampled['Y'].tolist(),
                    }
                except Exception:
                    continue
        else:
            # Fallback for individual laps if not 'last'
            for driver_abbr in ff1_session.laps['Driver'].unique():
                driver_laps = ff1_session.laps.pick_drivers(driver_abbr)
                if len(driver_laps) == 0:
                    continue
                
                if lap_num == 'fastest':
                    target_lap = driver_laps.pick_fastest()
                    target_laps = pd.DataFrame([target_lap]) if pd.notna(target_lap['LapTime']) else []
                else:
                    target_laps = driver_laps[driver_laps['LapNumber'] == int(lap_num)]
                
                if len(target_laps) == 0:
                    continue
                
                target_lap = target_laps.iloc[0]
                try:
                    tel = target_lap.get_telemetry()
                    step = max(1, len(tel) // 200)
                    tel_sampled = tel.iloc[::step]
                    
                    d = Driver.query.filter_by(abbreviation=driver_abbr, season=season).first()
                    team_color = d.constructor.team_color if d and d.constructor else '#FFF'
                    
                    drivers_gps[driver_abbr] = {
                        'driver': driver_abbr,
                        'team_color': team_color,
                        'x': tel_sampled['X'].tolist(),
                        'y': tel_sampled['Y'].tolist(),
                    }
                except Exception:
                    continue
                    
        return jsonify(drivers_gps)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@analytics_bp.route('/gps-data-full')
def gps_data_full():
    """Get heavily downsampled full race positional data for all drivers."""
    season = request.args.get('season', 2025, type=int)
    round_num = request.args.get('round', 1, type=int)
    
    try:
        ff1_session = get_loaded_session(season, round_num, 'R', needs_telemetry=True)
        drivers_gps = {}
        
        for driver_abbr in ff1_session.laps['Driver'].unique():
            try:
                # Get full race pos data
                pos = ff1_session.pos_data[driver_abbr]
                
                # Downsample heavily. e.g. 1 sample every 10 frames (~2-3 sec)
                step = max(1, len(pos) // 1000)
                pos_sampled = pos.iloc[::step]
                
                d = Driver.query.filter_by(abbreviation=driver_abbr, season=season).first()
                team_color = d.constructor.team_color if d and d.constructor else '#FFF'
                
                drivers_gps[driver_abbr] = {
                    'driver': driver_abbr,
                    'team_color': team_color,
                    'x': pos_sampled['X'].tolist(),
                    'y': pos_sampled['Y'].tolist()
                }
            except Exception:
                continue
                
        return jsonify(drivers_gps)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@analytics_bp.route('/circuit-map')
def circuit_map():
    """Get circuit outline from fastest lap GPS data, with sectors and DRS."""
    season = request.args.get('season', 2025, type=int)
    round_num = request.args.get('round', 1, type=int)
    
    try:
        ff1_session = get_loaded_session(season, round_num, 'R', needs_telemetry=True)
        fastest = ff1_session.laps.pick_fastest()
        tel = fastest.get_telemetry()
        
        # Sector coordinates
        s1_time = fastest.Sector1SessionTime
        s2_time = fastest.Sector2SessionTime
        
        s1_x, s1_y, s2_x, s2_y = 0, 0, 0, 0
        try:
            if pd.notna(s1_time):
                idx1 = (tel['SessionTime'] - s1_time).abs().idxmin()
                s1_x, s1_y = tel.loc[idx1, 'X'], tel.loc[idx1, 'Y']
            if pd.notna(s2_time):
                idx2 = (tel['SessionTime'] - s2_time).abs().idxmin()
                s2_x, s2_y = tel.loc[idx2, 'X'], tel.loc[idx2, 'Y']
        except Exception:
            pass
            
        # Downsample for track shape
        step = max(1, len(tel) // 300)
        tel_sampled = tel.iloc[::step]
        
        return jsonify({
            'x': tel_sampled['X'].tolist(),
            'y': tel_sampled['Y'].tolist(),
            'drs': tel_sampled['DRS'].tolist(),
            's1_x': s1_x, 's1_y': s1_y,
            's2_x': s2_x, 's2_y': s2_y,
            'circuit_name': ff1_session.event['EventName'],
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@analytics_bp.route('/races')
def get_races():
    """Get list of races for selector."""
    season = request.args.get('season', 2025, type=int)
    
    races = Race.query.filter_by(season=season).order_by(Race.round_number.asc()).all()
    
    return jsonify([{
        'round': r.round_number,
        'name': r.race_name,
        'country': r.country,
        'status': r.status,
    } for r in races])


@analytics_bp.route('/drivers')
def get_drivers():
    """Get list of drivers for selector."""
    season = request.args.get('season', 2025, type=int)
    
    drivers = Driver.query.filter_by(season=season).order_by(Driver.position.asc()).all()
    
    return jsonify([{
        'abbreviation': d.abbreviation,
        'full_name': d.full_name,
        'team': d.constructor.name if d.constructor else '',
        'team_color': d.constructor.team_color if d.constructor else '#FFF',
    } for d in drivers])
