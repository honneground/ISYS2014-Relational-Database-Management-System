DROP PROCEDURE IF EXISTS GetPlayersByDob;
DROP PROCEDURE IF EXISTS GetPlayersByAge;
DROP PROCEDURE IF EXISTS GetPlayersByTeam;
DROP PROCEDURE IF EXISTS GetMatchesByTeam;
DROP PROCEDURE IF EXISTS GetMatchesByStadium;
DROP PROCEDURE IF EXISTS GetMatchesByCity;
DROP PROCEDURE IF EXISTS GetTotalGoalsByTeam;

-- Stored Procedure for Players under a Specific DOB Range
DELIMITER //
CREATE PROCEDURE GetPlayersByDob(IN date_lower DATE, IN date_upper DATE)
BEGIN
    SELECT * FROM PlayerView WHERE DOB BETWEEN date_lower AND date_upper
    ORDER BY DOB;
END //
DELIMITER ;

CALL GetPlayersByDob('2000-01-01','2001-01-01');

-- Stored Procedure for Players under a Specific Age Range
DELIMITER //
CREATE PROCEDURE GetPlayersByAge(IN age_lower INT, IN age_upper INT)
BEGIN
    DECLARE date_lower DATE;
    DECLARE date_upper DATE;
    SET date_lower = CURRENT_DATE - INTERVAL age_upper YEAR;
    SET date_upper = CURRENT_DATE - INTERVAL age_lower YEAR;
    SELECT * FROM PlayerView WHERE DOB BETWEEN date_lower AND date_upper;
END //
DELIMITER ;
CALL GetPlayersByAge(0, 18);
-- Stored Procedure for Specific Team Players
DELIMITER //
CREATE PROCEDURE GetPlayersByTeam(IN team_name VARCHAR(255))
BEGIN
    SELECT * FROM PlayerView WHERE Team = team_name;
END //
DELIMITER ;

SET @TeamName = '';

SELECT country INTO @TeamName 
FROM Team 
LIMIT 1;

CALL GetPlayersByTeam(@TeamName);
-- Stored Procedure for Specific Team's Matches
DELIMITER //
CREATE PROCEDURE GetMatchesByTeam(IN team_name VARCHAR(255))
BEGIN
    SELECT * FROM GameView WHERE `Match (Home vs Away)` LIKE CONCAT(team_name, ' vs %') OR `Match (Home vs Away)` LIKE CONCAT('% vs ', team_name);
END //
DELIMITER ;


CALL GetMatchesByTeam(@TeamName);

-- Stored Procedure for Specific Stadium's Matches
DELIMITER //
CREATE PROCEDURE GetMatchesByStadium(IN stadium_name VARCHAR(255))
BEGIN
    SELECT * FROM GameView WHERE Stadium = stadium_name;
END //
DELIMITER ;


SET @StadiumName = '';

SELECT name INTO @StadiumName 
FROM Stadium 
LIMIT 1;
CALL GetMatchesByStadium(@StadiumName);

-- Stored Procedure for Specific City's Matches

DELIMITER //
CREATE PROCEDURE GetMatchesByCity(IN city_name VARCHAR(255))
BEGIN
    SELECT * FROM GameView WHERE `Host City` = city_name;
END //
DELIMITER ;

SET @CityName = '';

SELECT city INTO @CityName 
FROM Stadium 
LIMIT 1;
CALL GetMatchesByCity(@CityName);

-- Stored Procedure for Total Number of Goals Scored by Each Team

DELIMITER //
CREATE PROCEDURE GetTotalGoalsByTeam()
BEGIN
    SELECT Team.country as Team, (SUM(homeGoal)+SUM(awayGoal)) as 'Total Goals Count', SUM(homeGoal) AS 'Home Goals Count', SUM(awayGoal) AS 'Away Goals Count'
    FROM Game 
    JOIN Team ON Game.homeTeam = Team.teamName OR Game.awayTeam = Team.teamName 
    GROUP BY Team.country
    ORDER BY (SUM(homeGoal)+SUM(awayGoal)) DESC;
END //
DELIMITER ;
CALL GetTotalGoalsByTeam();
-- Trigger

ALTER TABLE Team ADD COLUMN games_played INT DEFAULT 0;

DELIMITER //
CREATE TRIGGER after_game_insert
AFTER INSERT ON Game
FOR EACH ROW
BEGIN
    UPDATE Team SET games_played = games_played + 1 WHERE teamName = NEW.homeTeam;
    UPDATE Team SET games_played = games_played + 1 WHERE teamName = NEW.awayTeam;
END; //
DELIMITER ;

DELIMITER //
CREATE TRIGGER after_game_delete
AFTER DELETE ON Game
FOR EACH ROW
BEGIN
    UPDATE Team SET games_played = games_played - 1 WHERE teamName = OLD.homeTeam;
    UPDATE Team SET games_played = games_played - 1 WHERE teamName = OLD.awayTeam;
END; //
DELIMITER ;
DELIMITER //
CREATE TRIGGER after_game_update
AFTER UPDATE ON Game
FOR EACH ROW
BEGIN
    IF OLD.homeTeam != NEW.homeTeam THEN
        UPDATE Team SET games_played = games_played - 1 WHERE teamName = OLD.homeTeam;
        UPDATE Team SET games_played = games_played + 1 WHERE teamName = NEW.homeTeam;
    END IF;
    IF OLD.awayTeam != NEW.awayTeam THEN
        UPDATE Team SET games_played = games_played - 1 WHERE teamName = OLD.awayTeam;
        UPDATE Team SET games_played = games_played + 1 WHERE teamName = NEW.awayTeam;
    END IF;
END; //
DELIMITER ;

SET @TeamName1 = NULL;
SET @TeamName2 = NULL;
SET @TeamName3 = NULL;
SELECT teamName INTO @TeamName1 FROM Team LIMIT 1;
SELECT teamName INTO @TeamName2 FROM Team LIMIT 1 OFFSET 1;
SELECT teamName INTO @TeamName3 FROM Team LIMIT 1 OFFSET 2;
-- Display our lucky countries for demo
SELECT @TeamName1, @TeamName2, @TeamName3;
-- The Game for the First Two Teams
INSERT INTO Game (time, locate, homeTeam, awayTeam, homeGoal, awayGoal) VALUES ('1900-01-01 01:00:00', @StadiumName, @TeamName1, @TeamName2, 2, 1);
SELECT * FROM Game WHERE homeTeam = @TeamName1 AND awayTeam = @TeamName2 AND time = '1900-01-01 01:00:00';
SELECT teamName, games_played FROM Team WHERE teamName IN (@TeamName1, @TeamName2, @TeamName3);
-- Update the Game to the Last Two Teams
UPDATE Game SET homeTeam = @TeamName3 WHERE homeTeam = @TeamName1 AND awayTeam = @TeamName2 AND time = '1900-01-01 01:00:00';
SELECT * FROM Game WHERE homeTeam = @TeamName3 AND awayTeam = @TeamName2 AND time = '1900-01-01 01:00:00';
SELECT teamName, games_played FROM Team WHERE teamName IN (@TeamName1, @TeamName2, @TeamName3);
-- Remove the game
DELETE FROM Game WHERE homeTeam = @TeamName3 AND awayTeam = @TeamName2 AND time = '1900-01-01 01:00:00';
SELECT * FROM Game WHERE homeTeam = @TeamName3 AND awayTeam = @TeamName2 AND time = '1900-01-01 01:00:00';
SELECT teamName, games_played FROM Team WHERE teamName IN (@TeamName1, @TeamName2, @TeamName3);

DROP TRIGGER IF EXISTS after_game_insert;
DROP TRIGGER IF EXISTS after_game_delete;
DROP TRIGGER IF EXISTS after_game_update;

ALTER TABLE Team DROP COLUMN games_played;