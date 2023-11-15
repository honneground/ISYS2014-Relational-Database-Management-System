-- Show players under a specific bod range
SELECT * FROM Player WHERE dob BETWEEN '2000-01-01' AND '2010-01-01';
-- Show specific team players
SELECT * FROM Player WHERE teamName = 'Australia W';
-- Show specific team's matches
SELECT * FROM Game WHERE homeTeam = 'Australia W' OR awayTeam = 'Australia W';
-- Show specific stadium' matches
SELECT * FROM Game WHERE locate = 'Stadium Australia';
-- Show specific city's matches
SELECT * FROM Game WHERE locate IN (SELECT name FROM Stadium WHERE city = "Sydney");
-- Find the total number of goals scored by each team

SELECT teamName, SUM(goals) AS total_goals
FROM (
    SELECT homeTeam AS teamName, homeGoal AS goals
    FROM Game
    UNION ALL
    SELECT awayTeam AS teamName, awayGoal AS goals
    FROM Game
) AS GoalsTable
GROUP BY teamName
ORDER BY total_goals DESC;
-- List top4 teams
CREATE OR REPLACE VIEW TopFourView AS
WITH RankedGames AS (
    SELECT *,
           ROW_NUMBER() OVER (ORDER BY time DESC) AS game_rank
    FROM Game
),
LatestGame AS (
    SELECT 
        winner AS ChampionTeam,
        CASE 
            WHEN winner = homeTeam THEN awayTeam
            WHEN winner = awayTeam THEN homeTeam
            ELSE NULL
        END AS RunnerUpTeam
    FROM RankedGames
    WHERE game_rank = 1
),
SecondLatestGame AS (
    SELECT 
        winner AS ThirdPlaceTeam,
        CASE 
            WHEN winner = homeTeam THEN awayTeam
            WHEN winner = awayTeam THEN homeTeam
            ELSE NULL
        END AS FourthPlaceTeam
    FROM RankedGames
    WHERE game_rank = 2
),
CountryMapping AS (
    SELECT
        lg.ChampionTeam,
        (SELECT country FROM Team WHERE teamName = lg.ChampionTeam) AS ChampionCountry,
        lg.RunnerUpTeam,
        (SELECT country FROM Team WHERE teamName = lg.RunnerUpTeam) AS RunnerUpCountry,
        slg.ThirdPlaceTeam,
        (SELECT country FROM Team WHERE teamName = slg.ThirdPlaceTeam) AS ThirdPlaceCountry,
        slg.FourthPlaceTeam,
        (SELECT country FROM Team WHERE teamName = slg.FourthPlaceTeam) AS FourthPlaceCountry
    FROM LatestGame lg
    CROSS JOIN SecondLatestGame slg
)
SELECT 
    ChampionCountry AS Champion,
    RunnerUpCountry AS RunnerUp,
    ThirdPlaceCountry AS ThirdPlace,
    FourthPlaceCountry AS FourthPlace
FROM CountryMapping;


SELECT * FROM TopFourView;

-- View that displaying comprehensive information about all the Stadiums

CREATE OR REPLACE VIEW StadiumView AS
SELECT
    name AS Name,
    city AS City
FROM
    Stadium;

SELECT * FROM StadiumView;

-- -- View that displaying information about all the teams

CREATE OR REPLACE VIEW TeamViewBase AS
SELECT 
    Team.country AS Team,
    COUNT(CASE WHEN G.winner = Team.teamName THEN 1 END) AS Wins,
    COUNT(CASE WHEN G.winner = 'N/A' AND (G.homeTeam = Team.teamName OR G.awayTeam = Team.teamName) THEN 1 END) AS Draws,
    COUNT(CASE WHEN G.winner != Team.teamName AND G.winner != 'N/A' AND (G.homeTeam = Team.teamName OR G.awayTeam = Team.teamName) THEN 1 END) AS Losses
FROM 
    Team
LEFT JOIN Game G ON G.homeTeam = Team.teamName OR G.awayTeam = Team.teamName
GROUP BY 
    Team.country
ORDER BY 
    Wins DESC, Draws DESC, Losses;

SELECT * FROM TeamViewBase;

-- View that displaying comprehensive information about all the teams

CREATE OR REPLACE VIEW TeamView AS
SELECT
    CASE 
        WHEN TR.Team = TResults.Champion THEN CONCAT(TR.Team, ' (Champion)')
        WHEN TR.Team = TResults.RunnerUp THEN CONCAT(TR.Team, ' (Runners-up)')
        WHEN TR.Team = TResults.ThirdPlace THEN CONCAT(TR.Team, ' (Third place)')
        WHEN TR.Team = TResults.FourthPlace THEN CONCAT(TR.Team, ' (Fourth place)')
        ELSE TR.Team
    END AS Team,
    TR.Wins,
    TR.Draws,
    TR.Losses
FROM
    TeamViewBase TR
LEFT JOIN TopFourView TResults ON TR.Team = TResults.Champion
                                    OR TR.Team = TResults.RunnerUp
                                    OR TR.Team = TResults.ThirdPlace
                                    OR TR.Team = TResults.FourthPlace;
SELECT * FROM TeamView;


-- View that displaying comprehensive information about all the players

CREATE OR REPLACE VIEW PlayerView AS
SELECT 
    p.name AS Name,
    CASE
        WHEN p.number >= 1000 THEN 'N/A'
        ELSE CONVERT(p.number, CHAR)
    END AS Number,
    t.country AS Team,
    p.position AS Position,
    p.dob AS 'DOB'

FROM Player p
JOIN Team t ON p.teamName = t.teamName

ORDER BY Team, p.number, Name;

SELECT * FROM PlayerView;

-- View that displaying comprehensive information about all the games

CREATE OR REPLACE VIEW GameView AS
SELECT
    CONCAT(T1.country, ' vs ', T2.country) AS 'Match (Home vs Away)',
    CONCAT(G.homeGoal, ':', G.awayGoal) AS 'Score',
    CASE
        WHEN G.winner = 'N/A' THEN 'N/A (Draw)'
        ELSE (SELECT country FROM Team WHERE teamName = G.winner)
    END AS 'Winner',
    DATE_FORMAT(G.time, '%Y-%m-%d %H:%i') AS 'Time (24-hour)',
    COALESCE(G.locate, 'N/A') AS 'Stadium',
    COALESCE(S.city, 'N/A') AS 'Host City'
FROM
    Game G
INNER JOIN
    Team T1 ON G.homeTeam = T1.teamName
INNER JOIN
    Team T2 ON G.awayTeam = T2.teamName
LEFT JOIN
    Stadium S ON G.locate = S.name
ORDER BY
    G.time; 

SELECT * FROM GameView;