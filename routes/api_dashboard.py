"""Dashboard API routes."""
from flask import Blueprint, jsonify, request
from models.database import db, Driver, Constructor, Race, RaceResult, LapTime, Session
from sqlalchemy import text

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/api/dashboard')


@dashboard_bp.route('/driver-standings')
def driver_standings():
    """Get driver standings for a given season."""
    season = request.args.get('season', 2025, type=int)
    
    drivers = Driver.query.filter_by(season=season).order_by(Driver.position.asc()).all()
    
    data = []
    for d in drivers:
        team_color = '#FFFFFF'
        team_name = ''
        if d.constructor:
            team_color = d.constructor.team_color or '#FFFFFF'
            team_name = d.constructor.name
        
        data.append({
            'position': d.position,
            'abbreviation': d.abbreviation,
            'first_name': d.first_name,
            'last_name': d.last_name,
            'full_name': d.full_name,
            'driver_number': d.driver_number,
            'nationality': d.nationality,
            'country_flag': d.country_flag,
            'photo_url': d.photo_url,
            'team': team_name,
            'team_color': team_color,
            'points': d.points,
            'wins': d.wins,
            'podiums': d.podiums,
        })
    
    return jsonify(data)


@dashboard_bp.route('/constructor-standings')
def constructor_standings():
    """Get constructor standings for a given season."""
    season = request.args.get('season', 2025, type=int)
    
    constructors = Constructor.query.filter_by(season=season).order_by(Constructor.position.asc()).all()
    
    data = []
    for c in constructors:
        # Get drivers for this constructor
        drivers = Driver.query.filter_by(constructor_id=c.id, season=season).all()
        driver_list = [{'abbreviation': d.abbreviation, 'full_name': d.full_name, 'points': d.points} for d in drivers]
        
        data.append({
            'position': c.position,
            'name': c.name,
            'full_name': c.full_name,
            'team_color': c.team_color,
            'logo_url': c.logo_url,
            'points': c.points,
            'drivers': driver_list,
        })
    
    return jsonify(data)


@dashboard_bp.route('/race-calendar')
def race_calendar():
    """Get race calendar."""
    season = request.args.get('season', 2025, type=int)
    
    races = Race.query.filter_by(season=season).order_by(Race.round_number.asc()).all()
    
    data = []
    for r in races:
        data.append({
            'round': r.round_number,
            'name': r.race_name,
            'circuit': r.circuit_name,
            'country': r.country,
            'country_code': r.country_code,
            'city': r.city,
            'date': r.race_date.isoformat() if r.race_date else None,
            'status': r.status,
        })
    
    return jsonify(data)


@dashboard_bp.route('/team-performance')
def team_performance():
    """Get team performance data per race for chart."""
    season = request.args.get('season', 2025, type=int)
    
    constructors = Constructor.query.filter_by(season=season).order_by(Constructor.position.asc()).all()
    races = Race.query.filter_by(season=season).order_by(Race.round_number.asc()).all()
    
    # Build cumulative points per constructor per race
    result_data = {
        'races': [r.race_name for r in races],
        'teams': []
    }
    
    for c in constructors:
        drivers = Driver.query.filter_by(constructor_id=c.id, season=season).all()
        driver_ids = [d.id for d in drivers]
        
        cumulative = 0
        points_per_race = []
        
        for race in races:
            race_points = db.session.query(
                db.func.coalesce(db.func.sum(RaceResult.points), 0)
            ).filter(
                RaceResult.race_id == race.id,
                RaceResult.driver_id.in_(driver_ids)
            ).scalar()
            
            cumulative += float(race_points or 0)
            points_per_race.append(cumulative)
        
        result_data['teams'].append({
            'name': c.name,
            'color': c.team_color,
            'points': points_per_race,
        })
    
    return jsonify(result_data)


@dashboard_bp.route('/recent-results')
def recent_results():
    """Get most recent race results."""
    season = request.args.get('season', 2025, type=int)
    
    latest_race = Race.query.filter_by(season=season, status='completed').order_by(
        Race.round_number.desc()
    ).first()
    
    if not latest_race:
        return jsonify({'race': None, 'results': []})
    
    results = RaceResult.query.filter_by(race_id=latest_race.id).order_by(
        RaceResult.finish_position.asc()
    ).all()
    
    data = []
    for r in results:
        driver = Driver.query.get(r.driver_id)
        team_color = driver.constructor.team_color if driver and driver.constructor else '#FFF'
        data.append({
            'position': r.finish_position,
            'driver': driver.full_name if driver else '',
            'abbreviation': driver.abbreviation if driver else '',
            'team': driver.constructor.name if driver and driver.constructor else '',
            'team_color': team_color,
            'grid': r.grid_position,
            'points': r.points,
            'status': r.status,
            'gap': r.gap_to_winner,
        })
    
    return jsonify({
        'race': {
            'name': latest_race.race_name,
            'round': latest_race.round_number,
            'country': latest_race.country,
            'date': latest_race.race_date.isoformat() if latest_race.race_date else None,
        },
        'results': data
    })
