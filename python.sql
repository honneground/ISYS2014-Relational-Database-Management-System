-- sample database for 2023

DROP DATABASE IF EXISTS wwc2023_demo;
CREATE DATABASE wwc2023_demo;
USE wwc2023_demo;
SOURCE dependency/table.sql;
SOURCE dependency/value_2023.sql;

-- sample database for 2019

DROP DATABASE IF EXISTS wwc2019_demo;
CREATE DATABASE wwc2019_demo;
USE wwc2019_demo;
SOURCE dependency/table.sql;
SOURCE dependency/value_2019.sql;
