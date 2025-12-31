---------------------------------------------------------------------
-- DEVIL RUN: FINAL DATABASE SETUP SCRIPT
-- Database Used: [devil_run_db] (As defined in config.py)
---------------------------------------------------------------------

USE [master];
GO

-- 1. Create Database if it doesn't exist
IF NOT EXISTS (SELECT * FROM sys.databases WHERE name = 'devil_run_db')
BEGIN
    CREATE DATABASE [devil_run_db];
    PRINT '>>> Database [devil_run_db] created successfully.';
END
ELSE
BEGIN
    PRINT '>>> Database [devil_run_db] already exists. Skipping creation.';
END
GO

-- Switch to the database
USE [devil_run_db];
GO

---------------------------------------------------------------------
-- 2. Table: Players
-- Holds login, profile details (name/dob), and total stars.
---------------------------------------------------------------------
IF OBJECT_ID('dbo.Players', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.Players (
        id INT IDENTITY(1,1) PRIMARY KEY, 
        username NVARCHAR(50) NOT NULL UNIQUE,
        password_hash CHAR(64) NOT NULL,
        name NVARCHAR(100) NULL,         -- Stores Full Name (New Update)
        dob NVARCHAR(20) NULL,           -- Stores Date of Birth (New Update)
        total_stars INT NOT NULL DEFAULT 0,
        created_at DATETIME NOT NULL DEFAULT GETDATE()
    );
    PRINT '>>> Table [Players] created.';
END
ELSE
BEGIN
    -- Self-Healing: Add name/dob if they were missing from a previous version
    IF NOT EXISTS(SELECT * FROM sys.columns WHERE Name = N'name' AND Object_ID = Object_ID(N'dbo.Players'))
    BEGIN
        ALTER TABLE dbo.Players ADD name NVARCHAR(100) NULL;
        PRINT '>>> Added missing column [name] to Players.';
    END

    IF NOT EXISTS(SELECT * FROM sys.columns WHERE Name = N'dob' AND Object_ID = Object_ID(N'dbo.Players'))
    BEGIN
        ALTER TABLE dbo.Players ADD dob NVARCHAR(20) NULL;
        PRINT '>>> Added missing column [dob] to Players.';
    END
    
    PRINT '>>> Table [Players] exists and is up to date.';
END
GO

---------------------------------------------------------------------
-- 3. Table: Deaths (Community Troll Feature)
---------------------------------------------------------------------
IF OBJECT_ID('dbo.Deaths', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.Deaths (
        id INT IDENTITY(1,1) PRIMARY KEY,
        level_id INT NOT NULL,
        coord_x INT NOT NULL, 
        coord_y INT NOT NULL,
        created_at DATETIME NOT NULL DEFAULT GETDATE()
    );
    CREATE INDEX IX_Deaths_LevelCoords ON dbo.Deaths (level_id, coord_x, coord_y);
    PRINT '>>> Table [Deaths] created.';
END
ELSE
BEGIN
    PRINT '>>> Table [Deaths] already exists.';
END
GO

---------------------------------------------------------------------
-- 4. Table: Level_Attempts (Progress Tracking)
---------------------------------------------------------------------
IF OBJECT_ID('dbo.Level_Attempts', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.Level_Attempts (
        id INT IDENTITY(1,1) PRIMARY KEY,
        user_id INT NOT NULL, 
        level_id INT NOT NULL,
        attempts INT NOT NULL, 
        stars_earned INT NOT NULL,
        completed_at DATETIME NOT NULL DEFAULT GETDATE()
    );
    PRINT '>>> Table [Level_Attempts] created.';
END
ELSE
BEGIN
    PRINT '>>> Table [Level_Attempts] already exists.';
END
GO

PRINT '-------------------------------------------------------';
PRINT 'DATABASE SETUP COMPLETE. YOU CAN NOW RUN main.py';
PRINT '-------------------------------------------------------';
