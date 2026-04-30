import fastf1
import pandas as pd
from sqlalchemy import create_engine

fastf1.Cache.enable_cache('f1_cache')

engine = create_engine('mysql+pymysql://root:password@localhost/f1_cache1')

def load_lap_data(year, gp):
    session = fastf1.get_session(year, gp, 'R')
    session.load(telemetry=False, weather=False)

    event = session.event
    race_id = int(f"{year}{event['RoundNumber']:02d}")

    race_data = pd.DataFrame({
        'season': [year],
        'gp_name': event['EventName'],
        'round_number': event['RoundNumber']
    })

    try:
        race_data.to_sql('races', con=engine, if_exists='append', index=False)
    except Exception as e:
        print(f"Error inserting race data: {e}")

    print(f"Processing lap data for {year} {gp}")
    laps = session.laps
    laps_df = laps[['Driver', 'LapNumber', 'LapTime', 'compound', 'Stint', 'LapStartTime', 'LapEndTime']].copy()

    def format_lap_time(lap_time):
        if pd.isna(lap_time): return None
        td = lap_time.total_seconds()
        minutes = int(td // 60)
        seconds = td % 60
        return f"{minutes}:{seconds:.3f}"
    
    laps_df['LapTime'] = laps_df['LapTime'].apply(format_lap_time)

    laps_df.rename(columns={
        'Driver': 'driver',
        'LapTime': 'lap_time',
        'LapNumber': 'lap_number',
        'Compound': 'tire_compound',
        'Stint': 'stint',
        'LapStartTime': 'lap_start_time',
        'LapEndTime': 'lap_end_time'
    }, inplace=True)

    try:
        laps_df.to_sql('lap_times', con=engine, if_exists='append', index=False)
        print(f"Inserted lap times for {year} {gp}")
    except Exception as e:
        print(f"Error inserting lap times: {e}")

if __name__ == "__main__":
    load_lap_data(2026, 1)