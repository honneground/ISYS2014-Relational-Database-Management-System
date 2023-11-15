-- Assign an identifier number for players who has a N/A shirt number
SET @NaPlayersIdentifier := 1000; 

-- Temporary tables involve storing rows from a CSV file in their raw text format, with the automatic removal of themselves being implicit after the process.

DROP TEMPORARY TABLE IF EXISTS TempPlayer;
DROP TEMPORARY TABLE IF EXISTS TempGame; 

CREATE TEMPORARY TABLE TempPlayer (
    raw_data TEXT
);
CREATE TEMPORARY TABLE TempGame (
    raw_data TEXT
);


-- Load the teams CSV file and selectively import two columns. A warning might arise due to our intention of excluding any data from the fifth column onwards.
LOAD DATA LOCAL INFILE 'sample_data/2019/international-womens-world-cup-teams-2019-to-2019-stats.csv'
INTO TABLE Team
FIELDS TERMINATED BY ','
LINES TERMINATED BY '\n'
IGNORE 1 LINES
(@dummy, teamName, @dummy, country);


-- Load the player's data
LOAD DATA LOCAL INFILE 'sample_data/2019/international-womens-world-cup-players-2019-to-2019-stats.csv'
INTO TABLE TempPlayer
LINES TERMINATED BY '\n'
IGNORE 1 LINES
(raw_data);


INSERT INTO Player (teamName, number, name, dob, position)
SELECT 
    TRIM(SUBSTRING_INDEX(SUBSTRING_INDEX(raw_data, ',', 8), ',', -1)) AS teamName,
    CASE 
        WHEN TRIM(SUBSTRING_INDEX(SUBSTRING_INDEX(raw_data, ',', -3), ',', 1)) = 'N/A' 
        THEN @NaPlayersIdentifier := @NaPlayersIdentifier + 1
        ELSE TRIM(SUBSTRING_INDEX(SUBSTRING_INDEX(raw_data, ',', -3), ',', 1)) + 0 
    END AS number,
    TRIM(SUBSTRING_INDEX(SUBSTRING_INDEX(raw_data, ',', 1), ',', -1)) AS name,
    STR_TO_DATE(TRIM(SUBSTRING_INDEX(SUBSTRING_INDEX(raw_data, ',', 4), ',', -1)), '%Y/%m/%d') AS dob,
    TRIM(SUBSTRING_INDEX(SUBSTRING_INDEX(raw_data, ',', 7), ',', -1)) AS position
FROM TempPlayer;

-- Load the stadium and games' data
LOAD DATA LOCAL INFILE 'sample_data/2019/international-womens-world-cup-matches-2019-to-2019-stats.csv'
INTO TABLE TempGame
LINES TERMINATED BY '\n'
IGNORE 1 LINES
(raw_data);

INSERT INTO Stadium (name, city)
SELECT DISTINCT
    name, city
FROM (
    SELECT 
        TRIM(SUBSTRING_INDEX(SUBSTRING_INDEX(raw_data, ' (', 1), ',', -1)) AS name,
        TRIM(SUBSTRING_INDEX(SUBSTRING_INDEX(raw_data, '(', -1), ')', 1)) AS city
    FROM TempGame
    WHERE raw_data LIKE '%(%)%'
) AS cleaned_data
WHERE name IS NOT NULL AND name != '';

INSERT INTO Game (time, homeTeam, awayTeam, homeGoal, awayGoal, locate)
SELECT 
    STR_TO_DATE(TRIM(SUBSTRING_INDEX(SUBSTRING_INDEX(raw_data, ',', 2), ',', -1)), '%b %d %Y - %l:%i%p') AS time,
    TRIM(SUBSTRING_INDEX(SUBSTRING_INDEX(raw_data, ',', 5), ',', -1)) AS homeTeam,
    TRIM(SUBSTRING_INDEX(SUBSTRING_INDEX(raw_data, ',', 6), ',', -1)) AS awayTeam,
    CAST(TRIM(SUBSTRING_INDEX(SUBSTRING_INDEX(raw_data, ',', 13), ',', -1)) AS UNSIGNED) AS homeGoal,
    CAST(TRIM(SUBSTRING_INDEX(SUBSTRING_INDEX(raw_data, ',', 14), ',', -1)) AS UNSIGNED) AS awayGoal,
    CASE
        WHEN raw_data LIKE '%(%)%' THEN TRIM(SUBSTRING_INDEX(SUBSTRING_INDEX(raw_data, ' (', 1), ',', -1))
        ELSE NULL
    END AS locate
FROM TempGame;