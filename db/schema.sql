-- F1 Analytics Database Schema
-- Database: f1_analytics

CREATE DATABASE IF NOT EXISTS f1_analytics CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE f1_analytics;

-- Users table for authentication
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('user', 'admin') DEFAULT 'user',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP NULL
);

-- Constructors/Teams
CREATE TABLE IF NOT EXISTS constructors (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    full_name VARCHAR(200),
    nationality VARCHAR(50),
    team_color VARCHAR(7),
    logo_url VARCHAR(255),
    season INT NOT NULL,
    points DECIMAL(6,1) DEFAULT 0,
    position INT DEFAULT 0,
    UNIQUE KEY uk_constructor_season (name, season)
);

-- Drivers
CREATE TABLE IF NOT EXISTS drivers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    abbreviation VARCHAR(3) NOT NULL,
    first_name VARCHAR(50),
    last_name VARCHAR(50),
    full_name VARCHAR(100),
    driver_number INT,
    nationality VARCHAR(50),
    date_of_birth DATE,
    photo_url VARCHAR(255),
    country_flag VARCHAR(10),
    constructor_id INT,
    season INT NOT NULL,
    points DECIMAL(6,1) DEFAULT 0,
    position INT DEFAULT 0,
    wins INT DEFAULT 0,
    podiums INT DEFAULT 0,
    FOREIGN KEY (constructor_id) REFERENCES constructors(id) ON DELETE SET NULL,
    UNIQUE KEY uk_driver_season (abbreviation, season)
);

-- Races / Events
CREATE TABLE IF NOT EXISTS races (
    id INT AUTO_INCREMENT PRIMARY KEY,
    season INT NOT NULL,
    round_number INT NOT NULL,
    race_name VARCHAR(200) NOT NULL,
    circuit_name VARCHAR(200),
    country VARCHAR(100),
    country_code VARCHAR(5),
    city VARCHAR(100),
    race_date DATE,
    status ENUM('completed', 'upcoming', 'live') DEFAULT 'upcoming',
    UNIQUE KEY uk_race (season, round_number)
);

-- Sessions (Practice, Qualifying, Race)
CREATE TABLE IF NOT EXISTS sessions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    race_id INT NOT NULL,
    session_type ENUM('FP1', 'FP2', 'FP3', 'Q', 'SQ', 'SS', 'R', 'SR') NOT NULL,
    session_date DATETIME,
    status ENUM('completed', 'upcoming', 'live') DEFAULT 'upcoming',
    FOREIGN KEY (race_id) REFERENCES races(id) ON DELETE CASCADE,
    UNIQUE KEY uk_session (race_id, session_type)
);

-- Lap times
CREATE TABLE IF NOT EXISTS lap_times (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    session_id INT NOT NULL,
    driver_id INT NOT NULL,
    lap_number INT NOT NULL,
    lap_time_ms INT,
    lap_time_str VARCHAR(20),
    sector1_ms INT,
    sector2_ms INT,
    sector3_ms INT,
    compound VARCHAR(20),
    tyre_life INT,
    stint INT,
    is_personal_best BOOLEAN DEFAULT FALSE,
    position INT,
    gap_to_leader VARCHAR(20),
    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE,
    FOREIGN KEY (driver_id) REFERENCES drivers(id) ON DELETE CASCADE,
    INDEX idx_lap_session_driver (session_id, driver_id)
);

-- Race results
CREATE TABLE IF NOT EXISTS race_results (
    id INT AUTO_INCREMENT PRIMARY KEY,
    race_id INT NOT NULL,
    driver_id INT NOT NULL,
    grid_position INT,
    finish_position INT,
    points DECIMAL(4,1) DEFAULT 0,
    status VARCHAR(50),
    fastest_lap BOOLEAN DEFAULT FALSE,
    fastest_lap_time VARCHAR(20),
    gap_to_winner VARCHAR(50),
    FOREIGN KEY (race_id) REFERENCES races(id) ON DELETE CASCADE,
    FOREIGN KEY (driver_id) REFERENCES drivers(id) ON DELETE CASCADE,
    UNIQUE KEY uk_result (race_id, driver_id)
);

-- Qualifying results
CREATE TABLE IF NOT EXISTS qualifying_results (
    id INT AUTO_INCREMENT PRIMARY KEY,
    race_id INT NOT NULL,
    driver_id INT NOT NULL,
    position INT,
    q1_time VARCHAR(20),
    q1_time_ms INT,
    q2_time VARCHAR(20),
    q2_time_ms INT,
    q3_time VARCHAR(20),
    q3_time_ms INT,
    FOREIGN KEY (race_id) REFERENCES races(id) ON DELETE CASCADE,
    FOREIGN KEY (driver_id) REFERENCES drivers(id) ON DELETE CASCADE,
    UNIQUE KEY uk_quali (race_id, driver_id)
);

-- Telemetry / Car sensor data
CREATE TABLE IF NOT EXISTS telemetry (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    session_id INT NOT NULL,
    driver_id INT NOT NULL,
    lap_number INT NOT NULL,
    distance FLOAT,
    time_offset FLOAT,
    speed INT,
    throttle FLOAT,
    brake BOOLEAN,
    gear INT,
    rpm INT,
    drs INT,
    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE,
    FOREIGN KEY (driver_id) REFERENCES drivers(id) ON DELETE CASCADE,
    INDEX idx_telemetry_session (session_id, driver_id, lap_number)
);

-- GPS position data
CREATE TABLE IF NOT EXISTS gps_positions (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    session_id INT NOT NULL,
    driver_id INT NOT NULL,
    lap_number INT NOT NULL,
    timestamp_ms BIGINT,
    x FLOAT,
    y FLOAT,
    z FLOAT,
    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE,
    FOREIGN KEY (driver_id) REFERENCES drivers(id) ON DELETE CASCADE,
    INDEX idx_gps_session (session_id, driver_id, lap_number)
);

-- Circuit layouts (for map rendering)
CREATE TABLE IF NOT EXISTS circuits (
    id INT AUTO_INCREMENT PRIMARY KEY,
    circuit_name VARCHAR(200) NOT NULL,
    country VARCHAR(100),
    circuit_length_km FLOAT,
    corners INT,
    drs_zones INT,
    map_svg_data LONGTEXT,
    UNIQUE KEY uk_circuit (circuit_name)
);

-- Insert default admin user (password: admin123 - hashed with werkzeug)
INSERT IGNORE INTO users (username, email, password_hash, role) VALUES 
('admin', 'admin@f1analytics.com', 'pbkdf2:sha256:600000$salt$hash', 'admin');
