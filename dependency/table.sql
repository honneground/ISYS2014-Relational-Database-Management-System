DROP TABLE IF EXISTS Game;
DROP TABLE IF EXISTS Player;
DROP TABLE IF EXISTS Team;
DROP TABLE IF EXISTS Stadium;

CREATE TABLE Team (
    teamName VARCHAR(58) NOT NULL PRIMARY KEY,
    country VARCHAR(56) UNIQUE
);

CREATE TABLE Player (
    teamName VARCHAR(58) NOT NULL,
    number INT NOT NULL,
    name VARCHAR(50),
    dob DATE,
    position VARCHAR(32),
    FOREIGN KEY (teamName) REFERENCES Team(teamName),
    PRIMARY KEY (teamName, number)
);

CREATE TABLE Stadium (
    name VARCHAR(128) NOT NULL PRIMARY KEY,
    city VARCHAR(64)
);

CREATE TABLE Game (
    time DATETIME NOT NULL,
    locate VARCHAR(128),
    homeTeam VARCHAR(58) NOT NULL,
    homeGoal INT,
    awayTeam VARCHAR(58) NOT NULL,
    awayGoal INT,
    winner VARCHAR(58) AS (
        CASE 
            WHEN homeGoal > awayGoal THEN homeTeam
            WHEN homeGoal < awayGoal THEN awayTeam
            ELSE 'N/A'
        END
    ) STORED,
    FOREIGN KEY (homeTeam) REFERENCES Team(teamName),
    FOREIGN KEY (awayTeam) REFERENCES Team(teamName),
    FOREIGN KEY (locate) REFERENCES Stadium(name) ON DELETE SET NULL,
    PRIMARY KEY (time, homeTeam, awayTeam)
);
