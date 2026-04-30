"""
Seed the f1_analytics database with 2025 season data using FastF1.
Also sets up structures for 2026 live data.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import fastf1
import pandas as pd
import numpy as np
from datetime import datetime
from sqlalchemy import create_engine, text
from config import Config

fastf1.Cache.enable_cache(Config.FASTF1_CACHE_DIR)

engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)

# F1 2025 Team Colors
TEAM_COLORS = {
    'Red Bull Racing': '#3671C6',
    'Ferrari': '#E80020',
    'Mercedes': '#27F4D2',
    'McLaren': '#FF8000',
    'Aston Martin': '#229971',
    'Alpine': '#0093CC',
    'Williams': '#64C4FF',
    'RB': '#6692FF',
    'Kick Sauber': '#52E252',
    'Haas F1 Team': '#B6BABD',
}

# Country flag emojis
COUNTRY_FLAGS = {
    'Dutch': '🇳🇱', 'British': '🇬🇧', 'Monegasque': '🇲🇨',
    'Spanish': '🇪🇸', 'Australian': '🇦🇺', 'Mexican': '🇲🇽',
    'French': '🇫🇷', 'Canadian': '🇨🇦', 'German': '🇩🇪',
    'Thai': '🇹🇭', 'Japanese': '🇯🇵', 'Chinese': '🇨🇳',
    'Finnish': '🇫🇮', 'Danish': '🇩🇰', 'American': '🇺🇸',
    'Italian': '🇮🇹', 'New Zealander': '🇳🇿', 'Argentine': '🇦🇷',
    'Brazilian': '🇧🇷', 'Swiss': '🇨🇭',
}

# GP Country codes for flags
GP_COUNTRIES = {
    'Bahrain': 'BH', 'Saudi Arabia': 'SA', 'Australia': 'AU',
    'Japan': 'JP', 'China': 'CN', 'United States': 'US',
    'Italy': 'IT', 'Monaco': 'MC', 'Canada': 'CA',
    'Spain': 'ES', 'Austria': 'AT', 'United Kingdom': 'GB',
    'Hungary': 'HU', 'Belgium': 'BE', 'Netherlands': 'NL',
    'Singapore': 'SG', 'Azerbaijan': 'AZ', 'Mexico': 'MX',
    'Brazil': 'BR', 'Qatar': 'QA', 'Abu Dhabi': 'AE',
    'Las Vegas': 'US', 'Miami': 'US',
}


def create_tables():
    """Create all tables from schema."""
    schema_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'db', 'schema.sql')
    with open(schema_path, 'r') as f:
        schema = f.read()
    
    with engine.connect() as conn:
        for statement in schema.split(';'):
            stmt = statement.strip()
            if stmt and not stmt.startswith('--'):
                try:
                    conn.execute(text(stmt))
                except Exception as e:
                    print(f"Warning: {e}")
        conn.commit()
    print("Tables created successfully.")


def seed_constructors(year):
    """Load constructor data for a given season."""
    print(f"Seeding constructors for {year}...")
    
    # Get first completed race to extract team data
    schedule = fastf1.get_event_schedule(year)
    
    first_event = None
    for _, event in schedule.iterrows():
        try:
            session = fastf1.get_session(year, event['RoundNumber'], 'R')
            session.load(telemetry=False, weather=False)
            if session.results is not None and len(session.results) > 0:
                first_event = session
                break
        except Exception:
            continue
    
    if first_event is None:
        print(f"No completed races found for {year}")
        return
    
    results = first_event.results
    teams = results[['TeamName']].drop_duplicates()
    
    constructors_data = []
    for _, team in teams.iterrows():
        team_name = team['TeamName']
        color = TEAM_COLORS.get(team_name, '#FFFFFF')
        constructors_data.append({
            'name': team_name,
            'full_name': team_name,
            'nationality': '',
            'team_color': color,
            'logo_url': f'/static/img/teams/{team_name.lower().replace(" ", "_")}.png',
            'season': year,
            'points': 0,
            'position': 0
        })
    
    df = pd.DataFrame(constructors_data)
    with engine.connect() as conn:
        for _, row in df.iterrows():
            try:
                conn.execute(text(
                    "INSERT IGNORE INTO constructors (name, full_name, nationality, team_color, logo_url, season, points, position) "
                    "VALUES (:name, :full_name, :nationality, :team_color, :logo_url, :season, :points, :position)"
                ), dict(row))
            except Exception as e:
                print(f"  Error: {e}")
        conn.commit()
    print(f"  Constructors seeded for {year}")


def seed_drivers(year):
    """Load driver data for a given season."""
    print(f"Seeding drivers for {year}...")
    
    schedule = fastf1.get_event_schedule(year)
    
    session = None
    for _, event in schedule.iterrows():
        try:
            session = fastf1.get_session(year, event['RoundNumber'], 'R')
            session.load(telemetry=False, weather=False)
            if session.results is not None and len(session.results) > 0:
                break
        except Exception:
            continue
    
    if session is None:
        return
    
    results = session.results
    
    with engine.connect() as conn:
        for _, driver in results.iterrows():
            abbr = driver.get('Abbreviation', '')
            team_name = driver.get('TeamName', '')
            
            # Get constructor_id
            result = conn.execute(text(
                "SELECT id FROM constructors WHERE name = :name AND season = :season"
            ), {'name': team_name, 'season': year})
            row = result.fetchone()
            constructor_id = row[0] if row else None
            
            nationality = driver.get('CountryCode', '')
            flag = COUNTRY_FLAGS.get(nationality, '🏁')
            
            first_name = driver.get('FirstName', '')
            last_name = driver.get('LastName', '')
            full_name = f"{first_name} {last_name}"
            driver_number = int(driver.get('DriverNumber', 0)) if pd.notna(driver.get('DriverNumber')) else 0
            
            try:
                conn.execute(text(
                    "INSERT IGNORE INTO drivers (abbreviation, first_name, last_name, full_name, "
                    "driver_number, nationality, photo_url, country_flag, constructor_id, season, "
                    "points, position, wins, podiums) "
                    "VALUES (:abbr, :first_name, :last_name, :full_name, :driver_number, "
                    ":nationality, :photo_url, :country_flag, :constructor_id, :season, "
                    "0, 0, 0, 0)"
                ), {
                    'abbr': abbr, 'first_name': first_name, 'last_name': last_name,
                    'full_name': full_name, 'driver_number': driver_number,
                    'nationality': nationality,
                    'photo_url': f'/static/img/drivers/{abbr.lower()}.png',
                    'country_flag': flag, 'constructor_id': constructor_id,
                    'season': year
                })
            except Exception as e:
                print(f"  Error inserting {abbr}: {e}")
        conn.commit()
    print(f"  Drivers seeded for {year}")


def seed_races(year):
    """Load race schedule for a given season."""
    print(f"Seeding races for {year}...")
    
    schedule = fastf1.get_event_schedule(year)
    
    with engine.connect() as conn:
        for _, event in schedule.iterrows():
            round_num = event.get('RoundNumber', 0)
            if round_num == 0:
                continue
            
            event_name = event.get('EventName', '')
            country = event.get('Country', '')
            country_code = GP_COUNTRIES.get(country, '')
            location = event.get('Location', '')
            
            event_date = event.get('EventDate', None)
            if pd.notna(event_date):
                race_date = pd.Timestamp(event_date).strftime('%Y-%m-%d')
            else:
                race_date = None
            
            status = 'completed'
            if pd.notna(event_date) and pd.Timestamp(event_date) > pd.Timestamp.now():
                status = 'upcoming'
            
            try:
                conn.execute(text(
                    "INSERT IGNORE INTO races (season, round_number, race_name, circuit_name, "
                    "country, country_code, city, race_date, status) "
                    "VALUES (:season, :round, :name, :circuit, :country, :code, :city, :date, :status)"
                ), {
                    'season': year, 'round': int(round_num), 'name': event_name,
                    'circuit': event.get('OfficialEventName', event_name),
                    'country': country, 'code': country_code,
                    'city': location, 'date': race_date, 'status': status
                })
            except Exception as e:
                print(f"  Error: {e}")
        conn.commit()
    print(f"  Races seeded for {year}")


def seed_qualifying_results(year):
    """Load qualifying results into database."""
    print(f"Seeding qualifying results for {year}...")
    
    schedule = fastf1.get_event_schedule(year)
    with engine.connect() as conn:
        for _, event in schedule.iterrows():
            round_num = event.get('RoundNumber', 0)
            if round_num == 0: continue
            
            try:
                session = fastf1.get_session(year, int(round_num), 'Q')
                session.load(telemetry=False, weather=False)
            except Exception:
                continue
                
            if session.results is None or len(session.results) == 0:
                continue
                
            # Get race_id
            result = conn.execute(text("SELECT id FROM races WHERE season = :season AND round_number = :round"), 
                                  {'season': year, 'round': int(round_num)})
            race_row = result.fetchone()
            if not race_row: continue
            race_id = race_row[0]
            
            for _, driver in session.results.iterrows():
                abbr = driver.get('Abbreviation', '')
                d_result = conn.execute(text("SELECT id FROM drivers WHERE abbreviation = :abbr AND season = :season"), 
                                        {'abbr': abbr, 'season': year})
                d_row = d_result.fetchone()
                if not d_row: continue
                driver_id = d_row[0]
                
                pos = int(driver.get('Position', 0)) if pd.notna(driver.get('Position')) else 0
                
                # Format Q times
                q1 = str(driver.get('Q1', '')).split('0 days ')[-1][:11] if pd.notna(driver.get('Q1')) else None
                q2 = str(driver.get('Q2', '')).split('0 days ')[-1][:11] if pd.notna(driver.get('Q2')) else None
                q3 = str(driver.get('Q3', '')).split('0 days ')[-1][:11] if pd.notna(driver.get('Q3')) else None
                
                try:
                    conn.execute(text(
                        "INSERT IGNORE INTO qualifying_results "
                        "(race_id, driver_id, position, q1_time, q2_time, q3_time) "
                        "VALUES (:race_id, :driver_id, :position, :q1, :q2, :q3)"
                    ), {
                        'race_id': race_id, 'driver_id': driver_id, 'position': pos,
                        'q1': q1, 'q2': q2, 'q3': q3
                    })
                except Exception as e:
                    print(f"  Error inserting quali {abbr}: {e}")
        conn.commit()
    print(f"  Qualifying seeded for {year}")


def seed_race_results(year):
    """Load race results and standings."""
    print(f"Seeding race results for {year}...")
    
    schedule = fastf1.get_event_schedule(year)
    
    with engine.connect() as conn:
        for _, event in schedule.iterrows():
            round_num = event.get('RoundNumber', 0)
            if round_num == 0:
                continue
            
            try:
                session = fastf1.get_session(year, int(round_num), 'R')
                session.load(telemetry=False, weather=False)
            except Exception:
                continue
            
            if session.results is None or len(session.results) == 0:
                continue
            
            # Get race_id
            result = conn.execute(text(
                "SELECT id FROM races WHERE season = :season AND round_number = :round"
            ), {'season': year, 'round': int(round_num)})
            race_row = result.fetchone()
            if not race_row:
                continue
            race_id = race_row[0]
            
            for _, driver in session.results.iterrows():
                abbr = driver.get('Abbreviation', '')
                
                # Get driver_id
                d_result = conn.execute(text(
                    "SELECT id FROM drivers WHERE abbreviation = :abbr AND season = :season"
                ), {'abbr': abbr, 'season': year})
                d_row = d_result.fetchone()
                if not d_row:
                    continue
                driver_id = d_row[0]
                
                grid = int(driver.get('GridPosition', 0)) if pd.notna(driver.get('GridPosition')) else 0
                pos = int(driver.get('Position', 0)) if pd.notna(driver.get('Position')) else 0
                pts = float(driver.get('Points', 0)) if pd.notna(driver.get('Points')) else 0
                status = str(driver.get('Status', ''))
                
                try:
                    conn.execute(text(
                        "INSERT IGNORE INTO race_results (race_id, driver_id, grid_position, "
                        "finish_position, points, status) "
                        "VALUES (:race_id, :driver_id, :grid, :pos, :pts, :status)"
                    ), {
                        'race_id': race_id, 'driver_id': driver_id,
                        'grid': grid, 'pos': pos, 'pts': pts, 'status': status
                    })
                except Exception as e:
                    print(f"  Error result {abbr}: {e}")
        conn.commit()
    
    # Update driver standings (sum points)
    conn2 = engine.connect()
    conn2.execute(text("""
        UPDATE drivers d SET 
            points = COALESCE((SELECT SUM(rr.points) FROM race_results rr WHERE rr.driver_id = d.id), 0),
            wins = COALESCE((SELECT COUNT(*) FROM race_results rr WHERE rr.driver_id = d.id AND rr.finish_position = 1), 0),
            podiums = COALESCE((SELECT COUNT(*) FROM race_results rr WHERE rr.driver_id = d.id AND rr.finish_position <= 3), 0)
        WHERE d.season = :season
    """), {'season': year})
    
    # Set driver positions by points
    conn2.execute(text("""
        UPDATE drivers d SET position = (
            SELECT COUNT(*) + 1 FROM drivers d2 
            WHERE d2.season = d.season AND d2.points > d.points
        ) WHERE d.season = :season
    """), {'season': year})
    
    # Update constructor standings
    conn2.execute(text("""
        UPDATE constructors c SET 
            points = COALESCE((
                SELECT SUM(d.points) FROM drivers d WHERE d.constructor_id = c.id
            ), 0)
        WHERE c.season = :season
    """), {'season': year})
    
    conn2.execute(text("""
        UPDATE constructors c SET position = (
            SELECT COUNT(*) + 1 FROM constructors c2 
            WHERE c2.season = c.season AND c2.points > c.points
        ) WHERE c.season = :season
    """), {'season': year})
    
    conn2.commit()
    conn2.close()
    print(f"  Race results and standings seeded for {year}")


def seed_lap_times(year, max_rounds=None):
    """Load lap time data for all sessions."""
    print(f"Seeding lap times for {year}...")
    
    schedule = fastf1.get_event_schedule(year)
    
    with engine.connect() as conn:
        for _, event in schedule.iterrows():
            round_num = event.get('RoundNumber', 0)
            if round_num == 0:
                continue
            if max_rounds and round_num > max_rounds:
                break
            
            race_result = conn.execute(text(
                "SELECT id FROM races WHERE season = :season AND round_number = :round"
            ), {'season': year, 'round': int(round_num)})
            race_row = race_result.fetchone()
            if not race_row:
                continue
            race_id = race_row[0]
            
            for session_type in ['R', 'Q']:
                try:
                    ff1_session = fastf1.get_session(year, int(round_num), session_type)
                    ff1_session.load(telemetry=False, weather=False)
                except Exception:
                    continue
                
                if ff1_session.laps is None or len(ff1_session.laps) == 0:
                    continue
                
                # Create session record
                st = session_type
                try:
                    conn.execute(text(
                        "INSERT IGNORE INTO sessions (race_id, session_type, status) "
                        "VALUES (:race_id, :st, 'completed')"
                    ), {'race_id': race_id, 'st': st})
                    conn.commit()
                except Exception:
                    pass
                
                s_result = conn.execute(text(
                    "SELECT id FROM sessions WHERE race_id = :race_id AND session_type = :st"
                ), {'race_id': race_id, 'st': st})
                s_row = s_result.fetchone()
                if not s_row:
                    continue
                session_id = s_row[0]
                
                laps = ff1_session.laps
                for _, lap in laps.iterrows():
                    abbr = lap.get('Driver', '')
                    d_result = conn.execute(text(
                        "SELECT id FROM drivers WHERE abbreviation = :abbr AND season = :season"
                    ), {'abbr': abbr, 'season': year})
                    d_row = d_result.fetchone()
                    if not d_row:
                        continue
                    driver_id = d_row[0]
                    
                    lap_time = lap.get('LapTime', None)
                    lap_time_ms = None
                    lap_time_str = None
                    if pd.notna(lap_time):
                        try:
                            total_seconds = lap_time.total_seconds()
                            lap_time_ms = int(total_seconds * 1000)
                            mins = int(total_seconds // 60)
                            secs = total_seconds % 60
                            lap_time_str = f"{mins}:{secs:06.3f}"
                        except Exception:
                            pass
                    
                    compound = str(lap.get('Compound', '')) if pd.notna(lap.get('Compound')) else None
                    stint = int(lap.get('Stint', 0)) if pd.notna(lap.get('Stint')) else None
                    lap_num = int(lap.get('LapNumber', 0)) if pd.notna(lap.get('LapNumber')) else 0
                    position = int(lap.get('Position', 0)) if pd.notna(lap.get('Position')) else None
                    
                    try:
                        conn.execute(text(
                            "INSERT INTO lap_times (session_id, driver_id, lap_number, "
                            "lap_time_ms, lap_time_str, compound, stint, position) "
                            "VALUES (:sid, :did, :lap, :ms, :str, :comp, :stint, :pos)"
                        ), {
                            'sid': session_id, 'did': driver_id, 'lap': lap_num,
                            'ms': lap_time_ms, 'str': lap_time_str,
                            'comp': compound, 'stint': stint, 'pos': position
                        })
                    except Exception:
                        pass
                
                conn.commit()
                print(f"  Laps loaded: Round {round_num} - {session_type}")


def seed_all(year=2025, max_rounds=None):
    """Run complete seeding pipeline."""
    print(f"\n{'='*60}")
    print(f"  F1 Analytics Database Seeding - {year} Season")
    print(f"{'='*60}\n")
    
    create_tables()
    seed_constructors(year)
    seed_drivers(year)
    seed_races(year)
    seed_race_results(year)
    seed_lap_times(year, max_rounds=max_rounds)
    
    print(f"\n{'='*60}")
    print(f"  Seeding complete for {year}!")
    print(f"{'='*60}\n")


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Seed F1 Analytics Database')
    parser.add_argument('--year', type=int, default=2025, help='Season year')
    parser.add_argument('--rounds', type=int, default=3, help='Max rounds to load (0 for all)')
    args = parser.parse_args()
    
    rounds_to_load = args.rounds if args.rounds > 0 else None
    seed_all(args.year, max_rounds=rounds_to_load)
