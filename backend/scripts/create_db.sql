-- Run this once with an admin MySQL user, e.g.:
--   mysql -u root -p < scripts/create_db.sql
--
-- Creates the database and an app-scoped user matching the default
-- DATABASE_URL in .env.example. Change the password before using this
-- anywhere beyond local development.

CREATE DATABASE IF NOT EXISTS aivoa_complaints
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE USER IF NOT EXISTS 'aivoa_app'@'localhost' IDENTIFIED BY 'aivoa_dev_pw';
GRANT ALL PRIVILEGES ON aivoa_complaints.* TO 'aivoa_app'@'localhost';
FLUSH PRIVILEGES;

-- Tables themselves are created automatically by SQLAlchemy
-- (Base.metadata.create_all) the first time you run the FastAPI app -
-- no migration step is required for this project.
