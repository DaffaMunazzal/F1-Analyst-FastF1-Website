import fastf1
import pandas as pd
from sqlalchemy import create_engine

engine = create_engine('mysql+pymysql://root:password@localhost/f1_cache')

def load_race_data(year, gp, session, event, engine):
    session = fastf1.get_session(year, gp, event, session)
    session.load()

    result = session.results[['Abbreviation', 'Position', 'Grid', 'Points', 'TeamName']]

    result.to_sql('drivers', con=engine, if_exists='append', index=False)
    print(f"Inserted race data for {year} {gp} {session} {event}")