from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum('user', 'admin'), default='user')
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    last_login = db.Column(db.DateTime, nullable=True)

class Constructor(db.Model):
    __tablename__ = 'constructors'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    full_name = db.Column(db.String(200))
    nationality = db.Column(db.String(50))
    team_color = db.Column(db.String(7))
    logo_url = db.Column(db.String(255))
    season = db.Column(db.Integer, nullable=False)
    points = db.Column(db.Float, default=0)
    position = db.Column(db.Integer, default=0)
    drivers = db.relationship('Driver', backref='constructor', lazy=True)

class Driver(db.Model):
    __tablename__ = 'drivers'
    id = db.Column(db.Integer, primary_key=True)
    abbreviation = db.Column(db.String(3), nullable=False)
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    full_name = db.Column(db.String(100))
    driver_number = db.Column(db.Integer)
    nationality = db.Column(db.String(50))
    date_of_birth = db.Column(db.Date)
    photo_url = db.Column(db.String(255))
    country_flag = db.Column(db.String(10))
    constructor_id = db.Column(db.Integer, db.ForeignKey('constructors.id'))
    season = db.Column(db.Integer, nullable=False)
    points = db.Column(db.Float, default=0)
    position = db.Column(db.Integer, default=0)
    wins = db.Column(db.Integer, default=0)
    podiums = db.Column(db.Integer, default=0)

class Race(db.Model):  
    __tablename__ = 'races'
    id = db.Column(db.Integer, primary_key=True)
    season = db.Column(db.Integer, nullable=False)
    round_number = db.Column(db.Integer, nullable=False)
    race_name = db.Column(db.String(200), nullable=False)
    circuit_name = db.Column(db.String(200))
    country = db.Column(db.String(100))
    country_code = db.Column(db.String(5))
    city = db.Column(db.String(100))
    race_date = db.Column(db.Date)
    status = db.Column(db.Enum('completed', 'upcoming', 'live'), default='upcoming')
    sessions = db.relationship('Session', backref='race', lazy=True)
    results = db.relationship('RaceResult', backref='race', lazy=True)
    qualifying = db.relationship('QualifyingResult', backref='race', lazy=True)

class Session(db.Model):
    __tablename__ = 'sessions'
    id = db.Column(db.Integer, primary_key=True)
    race_id = db.Column(db.Integer, db.ForeignKey('races.id'), nullable=False)
    session_type = db.Column(db.Enum('FP1', 'FP2', 'FP3', 'Q', 'SQ', 'SS', 'R', 'SR'), nullable=False)
    session_date = db.Column(db.DateTime)
    status = db.Column(db.Enum('completed', 'upcoming', 'live'), default='upcoming')
    laps = db.relationship('LapTime', backref='session', lazy=True)

class LapTime(db.Model):
    __tablename__ = 'lap_times'
    id = db.Column(db.BigInteger, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('sessions.id'), nullable=False)
    driver_id = db.Column(db.Integer, db.ForeignKey('drivers.id'), nullable=False)
    lap_number = db.Column(db.Integer, nullable=False)
    lap_time_ms = db.Column(db.Integer)
    lap_time_str = db.Column(db.String(20))
    sector1_ms = db.Column(db.Integer)
    sector2_ms = db.Column(db.Integer)
    sector3_ms = db.Column(db.Integer)
    compound = db.Column(db.String(20))
    tyre_life = db.Column(db.Integer)
    stint = db.Column(db.Integer)
    is_personal_best = db.Column(db.Boolean, default=False)
    position = db.Column(db.Integer)
    gap_to_leader = db.Column(db.String(20))
    driver = db.relationship('Driver', backref='laps')

class RaceResult(db.Model):
    __tablename__ = 'race_results'
    id = db.Column(db.Integer, primary_key=True)
    race_id = db.Column(db.Integer, db.ForeignKey('races.id'), nullable=False)
    driver_id = db.Column(db.Integer, db.ForeignKey('drivers.id'), nullable=False)
    grid_position = db.Column(db.Integer)
    finish_position = db.Column(db.Integer)
    points = db.Column(db.Float, default=0)
    status = db.Column(db.String(50))
    fastest_lap = db.Column(db.Boolean, default=False)
    fastest_lap_time = db.Column(db.String(20))
    gap_to_winner = db.Column(db.String(50))
    driver = db.relationship('Driver', backref='race_results')

class QualifyingResult(db.Model):
    __tablename__ = 'qualifying_results'
    id = db.Column(db.Integer, primary_key=True)
    race_id = db.Column(db.Integer, db.ForeignKey('races.id'), nullable=False)
    driver_id = db.Column(db.Integer, db.ForeignKey('drivers.id'), nullable=False)
    position = db.Column(db.Integer)
    q1_time = db.Column(db.String(20))
    q1_time_ms = db.Column(db.Integer)
    q2_time = db.Column(db.String(20))
    q2_time_ms = db.Column(db.Integer)
    q3_time = db.Column(db.String(20))
    q3_time_ms = db.Column(db.Integer)
    driver = db.relationship('Driver', backref='qualifying_results')

class Telemetry(db.Model):
    __tablename__ = 'telemetry'
    id = db.Column(db.BigInteger, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('sessions.id'), nullable=False)
    driver_id = db.Column(db.Integer, db.ForeignKey('drivers.id'), nullable=False)
    lap_number = db.Column(db.Integer, nullable=False)
    distance = db.Column(db.Float)
    time_offset = db.Column(db.Float)
    speed = db.Column(db.Integer)
    throttle = db.Column(db.Float)
    brake = db.Column(db.Boolean)
    gear = db.Column(db.Integer)
    rpm = db.Column(db.Integer)
    drs = db.Column(db.Integer)
    driver = db.relationship('Driver', backref='telemetry_data')

class GpsPosition(db.Model):
    __tablename__ = 'gps_positions'
    id = db.Column(db.BigInteger, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('sessions.id'), nullable=False)
    driver_id = db.Column(db.Integer, db.ForeignKey('drivers.id'), nullable=False)
    lap_number = db.Column(db.Integer, nullable=False)
    timestamp_ms = db.Column(db.BigInteger)
    x = db.Column(db.Float)
    y = db.Column(db.Float)
    z = db.Column(db.Float)
    driver = db.relationship('Driver', backref='gps_data')

class Circuit(db.Model):
    __tablename__ = 'circuits'
    id = db.Column(db.Integer, primary_key=True)
    circuit_name = db.Column(db.String(200), nullable=False, unique=True)
    country = db.Column(db.String(100))
    circuit_length_km = db.Column(db.Float)
    corners = db.Column(db.Integer)
    drs_zones = db.Column(db.Integer)
    map_svg_data = db.Column(db.Text)
