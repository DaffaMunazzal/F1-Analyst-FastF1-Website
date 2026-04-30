from app import app
from models.database import db, Driver, Constructor
from sqlalchemy import func

with app.app_context():
    # Find duplicate drivers
    # Group by abbreviation, season and keep the one with max points
    subquery = db.session.query(
        Driver.abbreviation, 
        Driver.season, 
        func.max(Driver.points).label('max_points'),
        func.count(Driver.id).label('count')
    ).group_by(Driver.abbreviation, Driver.season).having(func.count(Driver.id) > 1).all()
    
    print(f"Found {len(subquery)} drivers with duplicates")
    
    deleted_count = 0
    for abbr, season, max_points, count in subquery:
        # Get all drivers for this abbreviation and season
        drivers = Driver.query.filter_by(abbreviation=abbr, season=season).all()
        
        # Sort so we keep the one with max points, or highest id if points are same
        drivers.sort(key=lambda d: (d.points, d.id), reverse=True)
        
        # Keep the first one, delete the rest
        keep_driver = drivers[0]
        for driver_to_delete in drivers[1:]:
            db.session.delete(driver_to_delete)
            deleted_count += 1
            print(f"Deleted duplicate {abbr} ({driver_to_delete.id}) with {driver_to_delete.points} points")
            
    db.session.commit()
    print(f"Successfully deleted {deleted_count} duplicate drivers.")
    
    # Do the same for constructors just in case
    subquery_c = db.session.query(
        Constructor.name, 
        Constructor.season, 
        func.count(Constructor.id).label('count')
    ).group_by(Constructor.name, Constructor.season).having(func.count(Constructor.id) > 1).all()
    
    deleted_c_count = 0
    for name, season, count in subquery_c:
        constructors = Constructor.query.filter_by(name=name, season=season).all()
        constructors.sort(key=lambda c: (c.points, c.id), reverse=True)
        for c_to_delete in constructors[1:]:
            db.session.delete(c_to_delete)
            deleted_c_count += 1
            print(f"Deleted duplicate constructor {name}")
            
    db.session.commit()
    print(f"Successfully deleted {deleted_c_count} duplicate constructors.")
    
