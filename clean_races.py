from app import app
from models.database import db, Race
from sqlalchemy import func

with app.app_context():
    print("Finding duplicate races...")
    
    # Find duplicate races (same season and round_number)
    subquery_r = db.session.query(
        Race.season, 
        Race.round_number, 
        func.count(Race.id).label('count')
    ).group_by(Race.season, Race.round_number).having(func.count(Race.id) > 1).all()
    
    deleted_r_count = 0
    for season, round_num, count in subquery_r:
        races = Race.query.filter_by(season=season, round_number=round_num).all()
        # Sort by id so we keep the first one
        races.sort(key=lambda r: r.id)
        
        # Keep the first one, delete the rest
        for r_to_delete in races[1:]:
            db.session.delete(r_to_delete)
            deleted_r_count += 1
            print(f"Deleted duplicate race {r_to_delete.race_name} (Round {round_num})")
            
    db.session.commit()
    print(f"Successfully deleted {deleted_r_count} duplicate races.")
    
    # Let's apply the unique constraints to the tables if they don't exist
    try:
        db.session.execute(db.text("ALTER TABLE drivers ADD UNIQUE KEY uk_driver_season (abbreviation, season);"))
        print("Added unique constraint to drivers")
    except Exception as e:
        print(f"Driver constraint already exists or error: {e}")
        
    try:
        db.session.execute(db.text("ALTER TABLE constructors ADD UNIQUE KEY uk_constructor_season (name, season);"))
        print("Added unique constraint to constructors")
    except Exception as e:
        print(f"Constructor constraint already exists or error: {e}")
        
    try:
        db.session.execute(db.text("ALTER TABLE races ADD UNIQUE KEY uk_race (season, round_number);"))
        print("Added unique constraint to races")
    except Exception as e:
        print(f"Race constraint already exists or error: {e}")
        
    db.session.commit()
