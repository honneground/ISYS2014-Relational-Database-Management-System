import mysql.connector
from getpass import getpass
from tabulate import tabulate
import re
import datetime 
import os

def execute_sql_file(cursor, file_path):
    with open(file_path, 'r') as file:
        sql_script = file.read()
    sql_commands = sql_script.split(';')
    try:
        for command in sql_commands:
            if command.strip() != '':
                cursor.execute(command)
                if cursor.description:
                    cursor.fetchall()
        print(f"Successfully executed SQL script from {file_path}")
        return 0
    except mysql.connector.Error as error:
        print(f"Error occurred: {error}")
        return 1

def get_user_credentials():
    username = input("\nMySQL Username (default: 'root'): ")
    if username == "": username = "root"
    password = getpass("MySQL Password: ")
    if password == "": password = os.environ.get("MYSQL_PASSWORD", "")
    if password.lower() == "blank": password = ""
    return username, password

def connect_to_mysql(username, password):
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user=username,
            password=password,
        )
        return conn
    except mysql.connector.Error as error:
        print(error)
        return None

def convert_database_name(db_name):
    parts = db_name.split('_')
    converted_name = ' '.join(part.upper() for part in parts)
    return converted_name

def menu(database, cursor, changes_pending=False):
    hashes = '#' * (len(database) + 10)
    print(f"\n{hashes}")
    print(f"Database: {convert_database_name(database)}")
    print(hashes)
    menu_string = """
    MAIN MENU:
    (Please choose the operation to perform on the current database)

    V > View
    R > Retrieve 
    I > Insert 
    U > Update 
    P > Purge (Delete)

    S > Switch Database
    C > Commit Changes
    D > Discard Changes

    E > Exit
    """
    print(menu_string)

    option = input("Enter your option: ").strip().upper()

    while(True):
        if option == "R":
            advanced_retrieve_data(cursor)
        elif option in {"V", "O"}: #O for Observe
            retrieve_data(cursor)
        elif option == "I":
            insert_data(cursor)
            changes_pending = True
        elif option == "U":
            update_data(cursor)
            changes_pending = True
        elif option == "P":
            delete_data(cursor)
            changes_pending = True
        elif option == "S":
            if changes_pending:
                if input("Are you sure you want to switch database without committing? (y/n): ").lower() == 'y':
                    return 0
                print("Switch cancelled. Please commit or discard your changes before switching database.")
            else:
                return 0
        elif option == "D":
            if changes_pending:
                return 2
            print("\nNo changes have been made since the last commit.")
            input("\nPress 'Enter' to continue...")
        elif option == "C":
            if changes_pending:
                return 1
            print("\nNo changes have been made since the last commit.")
            input("\nPress 'Enter' to continue...")
        elif option in {'E', 'X', 'B'}:
            if changes_pending:
                print("\nWARNING: You have uncommitted changes that will be lost if you exit now.")
                if input("Are you sure you want to exit without committing? (y/n): ").lower() == 'y':
                    break
                print("Exit cancelled. Please commit or discard your changes before exiting.")
            else:
                break

        else:
            print("\nInvalid option, please try again.")
        print(f"\n{hashes}")
        print(f"Database: {convert_database_name(database)}")
        print(hashes)
        print(menu_string)
        option = input("Enter your option: ").strip().upper()

    print("Thank you for using the system. Exiting now...")
    exit()



def advanced_retrieve_data(cursor):
    print("Attempt to load and update the views...")
    if execute_sql_file(cursor, "dependency/views.sql") == 1:
        print("Fail to retrieve the tables, please check the database.")
        return
    data_retrieval_menu_pro = """
    DATA RETRIEVAL MENU:
    (Select data to show)
    1 > Players under a specific age range
    2 > Specific team players
    3 > Specific team's matches
    4 > Specific stadium' matches
    5 > Specific city's matches
    6 > Total number of goals scored by each team
    """
    print(data_retrieval_menu_pro)
    
    option = input("Select an option to retrieve data: ").strip()

    while option.upper() not in {'E', 'X', 'B'}:
        try:
            if option == '1':
                age_lower = int(input("Enter the lower age limit: "))
                age_upper = int(input("Enter the upper age limit: "))

                if age_lower > age_upper:
                    age_lower, age_upper = age_upper, age_lower
                    print("The lower age limit was greater than the upper age limit. Swapping them.")
                    input("Press 'Enter' to continue...")
                current_date = datetime.date.today()
                date_lower = current_date - datetime.timedelta(days=365 * age_upper)
                date_upper = current_date - datetime.timedelta(days=365 * age_lower)
                query = f"SELECT * FROM PlayerView WHERE DOB BETWEEN '{date_lower}' AND '{date_upper} ORDER BY DOB;';"
                print(f"Retrieving players aged between {age_lower} and {age_upper}...")
                
            elif option == '2' or option == '3':
                    cursor.execute("SELECT * FROM Team")
                    teams = cursor.fetchall()
                    for index, team in enumerate(teams):
                        print(f"{index+1}: {team[1]}")
                    team_index = int(input("Enter the index of the team: "))-1
                    selected_team = teams[team_index][1]

                    if option == '2':
                        query = f"SELECT * FROM PlayerView WHERE Team = '{selected_team}';"
                        print(f"Retrieving players from {selected_team}...")
                    elif option == '3':
                        query = f"SELECT * FROM GameView WHERE `Match (Home vs Away)` LIKE '{selected_team} vs %' OR `Match (Home vs Away)` LIKE '% vs {selected_team}';"
                        print(query)
                        print(f"Retrieving matches for {selected_team}...")
                               
            elif option == '4':
                cursor.execute("SELECT * FROM Stadium")
                stadiums = cursor.fetchall()
                for index, stadium in enumerate(stadiums):
                    print(f"{index+1}: {stadium[0]}, City: {stadium[1]}")
                stadium_index = int(input("Enter the index of the stadium you want to delete: "))-1
                selected_stadium = stadiums[stadium_index][0]
                query = f"SELECT * FROM Gameview WHERE Stadium = '{selected_stadium}';"
                print(f"Retrieving matches at {selected_stadium}...")
                
            elif option == '5':
                cursor.execute("SELECT DISTINCT city FROM Stadium")
                cities = cursor.fetchall()
                for index, city in enumerate(cities):
                    print(f"{index+1}: {city[0]}")
                city_index = int(input("Enter the index of the city you want to view matches for: ")) - 1
                selected_city = cities[city_index][0]
                query = f"SELECT * FROM GameView WHERE `Host City` = '{selected_city}';"
                print(f"Retrieving matches in {selected_city}...")
                            
            elif option == '6':
                query = """
                SELECT Team.country as Team, (SUM(homeGoal)+SUM(awayGoal)) as 'Totoal Goals Count', SUM(homeGoal) AS 'Home Goals Count', SUM(awayGoal) AS 'Away Goals Count'
                FROM Game 
                JOIN Team ON Game.homeTeam = Team.teamName OR Game.awayTeam = Team.teamName 
                GROUP BY Team.country
                ORDER BY (SUM(homeGoal)+SUM(awayGoal)) DESC;
                """
                print("Retrieving the total number of goals scored by each team...")
            else:
                print("Invalid option, please try again.")
                option = input("Select an option to retrieve data: ").strip()
                continue

            execute_query(cursor, query)
            input("\nPress 'Enter' to continue...")
            break

        except ValueError as ve:
            print(f"Input Error: {ve}")
        except mysql.connector.Error as error:
            print(f"Database Error: {error}")

    print("Returning to main menu...")

def retrieve_data(cursor):
    print("Attempt to load and update the views...")
    if execute_sql_file(cursor, "dependency/views.sql") == 1:
        print("Fail to retrieve the tables, please check the database.")
        return
    data_retrieval_menu = """
    DATA RETRIEVAL MENU:
    (Select view to observe)
    1 > Top Four
    2 > Stadium
    3 > Team
    4 > Player
    5 > Game 
    6 > Tournament Standings
    B > Back to Main Menu
    """
    print(data_retrieval_menu)
    
    views = {
        "1": "TopFourView",
        "2": "StadiumView",
        "3": "TeamView",
        "4": "PlayerView",
        "5": "GameView",
        "6": "TeamView",
    }

    option = input("Select an option to retrieve data: ").strip()

    while option.upper() not in {'E', 'X', 'B'}:
        if option in views:
            query = "SELECT * FROM " + views[option]
            print(f"Retrieving data from {views[option]}...")
            execute_query(cursor, query)
            input("\nPress 'Enter' to continue...")
            return
        else:
            print("Invalid option, please try again.")

        print(data_retrieval_menu)
        option = input("Select an option to retrieve data: ").strip()

    print("Returning to main menu...")

def print_results(cursor):
    table_array = cursor.fetchall()
    if table_array:
        header = cursor.column_names
        formatted_table = tabulate(table_array, header, tablefmt="psql", colalign=("left",))
        print()
        print(formatted_table)
    else:
        print("No results found.")

def execute_query(cursor, query):
    try:
        cursor.execute(query)
        print_results(cursor)  # Pass the cursor to print_results
    except Exception as e:
        print(f"An error occurred: {e}")

def insert_data(cursor):
    data_inserting_menu = """
    DATA INSERTING MENU:
    (Select table to insert data)
    T > Team
    P > Player
    S > Stadium
    G > Game
    B > Back to Main Menu
    """
    print(data_inserting_menu)

    table_choice = input("Enter choice (T/P/S/G/B): ").strip().upper()

    try:
        if table_choice == 'T':
            cursor.execute("SELECT * FROM Team")
            rows = cursor.fetchall()
            existing_teams, existing_countries = zip(*[(row[0], row[1]) for row in rows])

            teamName = input("Enter team name: ").strip()
            if teamName in existing_teams:
                raise ValueError("Duplicated team name.")
            if teamName == "":
                raise ValueError("Invalid team name.")
            
            country = input("Enter country: ").strip()

            if country in existing_countries:
                raise ValueError("One country is limited to have a single team.")
            if country == "":
                raise ValueError("Invalid team contry.")
            if len(teamName) > 58 or len(country) > 56:
                raise ValueError("Input data length exceeds limit.")
            cursor.execute("INSERT INTO Team (teamName, country) VALUES (%s, %s)", (teamName, country))
            cursor.execute("SELECT * FROM Team WHERE teamName = %s", (teamName,))
            print("New row added:")
            print_results(cursor)
            input("\nPress 'Enter' to continue...")


        elif table_choice == 'P':
            cursor.execute("SELECT * FROM Team")
            teams = cursor.fetchall()
            if not teams:
                print("No teams found. Add a team first.")
                return
            print("Select team:")
            for idx, team in enumerate(teams):
                print(f"{idx + 1}: {team[1]}")
            team_choice = int(input("Enter choice: "))
            if team_choice < 1 or team_choice > len(teams):
                raise ValueError("Invalid team choice.")
            teamName = teams[team_choice - 1][0]
            number = input("Enter player's number (default: 'Next available number'): ")
            if number != "" and (not number.isdigit() or not 1 < int(number) < 99):
                raise ValueError("Invalid player number.")
            cursor.execute("SELECT number FROM Player WHERE teamName = %s", (teamName,))
            used_numbers = [row[0] for row in cursor.fetchall()]
            if number == "":
                number = 1
                while number in used_numbers:
                    number += 1
                number = str(number)
            if int(number) in used_numbers:
                raise ValueError("Player number is already used.")
            name = input("Enter player's name: ")
            if name == "": name = "Unknown"
            dob = input("Enter player's date of birth (YYYY-MM-DD): ")
            if dob == "": dob = "1900-01-01"
            if not re.match(r'\d{4}-\d{2}-\d{2}', dob):
                raise ValueError("Invalid date format.")
            datetime.datetime.strptime(dob, '%Y-%m-%d')
            position = input("Enter player's position: ").strip()
            if position == "": position = "N/A"
            cursor.execute("INSERT INTO Player (teamName, number, name, dob, position) VALUES (%s, %s, %s, %s, %s)", (teamName, int(number), name, dob, position))
            cursor.execute("SELECT * FROM Player WHERE teamName = %s AND number = %s", (teamName, number))
            print("New row added:")
            print_results(cursor)
            input("\nPress 'Enter' to continue...")


        elif table_choice == 'S':
            name = input("Enter stadium name: ").strip()
            if len(name) < 2:
                raise ValueError("The name of the stadium is too brief.")  
            if len(name) > 128:
                raise ValueError("Input data length exceeds limit.")        
            cursor.execute("SELECT name FROM Stadium WHERE name = %s", (name,))
            existing_stadium = cursor.fetchone()
            if existing_stadium:
                raise ValueError("Duplicated stadium name.")
            else:
                city = input("Enter city: ").strip()
                if len(city) < 2:
                    raise ValueError("The location of the stadium is too brief.")
                if len(city) > 64:
                    raise ValueError("Input data length exceeds limit.")   
                cursor.execute("INSERT INTO Stadium (name, city) VALUES (%s, %s)", (name, city))
                cursor.execute("SELECT * FROM Stadium WHERE name = %s", (name,))
                print("New row added:")
                print_results(cursor)
                input("\nPress 'Enter' to continue...")

        elif table_choice == 'G':
            cursor.execute("SELECT * FROM Team")
            teams = cursor.fetchall()
            if not teams:
                print("No teams found. Add a team first.")
                return
            print("\nSelect home team:\n")
            for idx, team in enumerate(teams):
                print(f"{idx + 1}: {team[1]}")
            home_team_choice = int(input("Enter choice: "))
            if home_team_choice < 1 or home_team_choice > len(teams):
                raise ValueError("Invalid home team choice.")
            homeTeam = teams[home_team_choice - 1][0]
            print("\nSelect away team:\n")
            minus = 0
            for idx, team in enumerate(teams):
                if idx == home_team_choice-1:
                    minus = 1
                else:
                    print(f"{idx + 1 - minus}: {team[1]}")
            away_team_choice = int(input("Enter choice: "))
            if away_team_choice >= home_team_choice:
                away_team_choice += 1
            if away_team_choice < 1 or away_team_choice > len(teams) or away_team_choice == home_team_choice:
                raise ValueError("Invalid away team choice.")
            awayTeam = teams[away_team_choice - 1][0]
            cursor.execute("SELECT * FROM Stadium")
            stadiums = cursor.fetchall()
            if not stadiums:
                print("No stadiums found. Add a stadium first.")
                return
            print("Select stadium:")
            for idx, stadium in enumerate(stadiums):
                print(f"{idx + 1}: {stadium[0]} ({stadium[1]})")
            stadium_choice = int(input("Enter choice: "))
            if stadium_choice < 1 or stadium_choice > len(stadiums):
                raise ValueError("Invalid stadium choice.")
            locate = stadiums[stadium_choice - 1][0]

            time = input("Enter game time (YYYY-MM-DD HH:MM:SS): ")
            if time == "": time = "1900-01-01 00:00:00"
            if not re.match(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}', time):
                raise ValueError("Invalid datetime format.")
            datetime.datetime.strptime(time, '%Y-%m-%d %H:%M:%S') 
            homeGoal = input("Enter home team goals: ")
            if homeGoal == "": homeGoal = "0"
            if not homeGoal.isdigit() or int(homeGoal) < 0:
                raise ValueError("Invalid home team goals.")
            awayGoal = input("Enter away team goals: ")
            if awayGoal == "": awayGoal = "0"
    
            if not awayGoal.isdigit() or int(awayGoal) < 0:
                raise ValueError("Invalid away team goals.")
            cursor.execute("INSERT INTO Game (time, locate, homeTeam, homeGoal, awayTeam, awayGoal) VALUES (%s, %s, %s, %s, %s, %s)", (time, locate, homeTeam, int(homeGoal), awayTeam, int(awayGoal)))
            cursor.execute("SELECT * FROM Game WHERE homeTeam = %s AND awayTeam = %s AND time = %s", (homeTeam, awayTeam, time))
            print("New row added:")
            print_results(cursor)
            input("\nPress 'Enter' to continue...")

        else:
            if table_choice in {'E', 'X', 'B'}:
                return
            print("Invalid choice.")

    except ValueError as ve:
        print(f"Input Error: {ve}")
    except mysql.connector.Error as error:
        print(f"Database Error: {error}")

def switch_database():
    while(True):
        print("\nSelect database year or type the name of a custom database:\n")
        print("2023 - FIFA Women's World Cup Australia and New Zealand (default)")
        print("2019 - FIFA Women's World Cup France")
        print("Type the exact name of any other database to use a custom one")
        database_name = input("\nYour choice (2023/2019 or type a custom database name): ")
        
        if database_name.lower() in {"2023", "23", "3", "au", "australia", "new zealand", "australian", "nz", "kiwi", "aotearoa", "maori", "anz", "oceania", ""}: 
            database_name = "wwc2023_demo"
        elif database_name.lower() in {"2019", "19", "9", "fr", "france", "french"}: 
            database_name = "wwc2019_demo"
        try:
            while(True):
                conn = mysql.connector.connect(database=database_name)
                cursor = conn.cursor()
                reslut = menu(database_name, cursor) 
                if reslut > 0:
                    if reslut == 1:
                        conn.commit()
                        print("\nChanges Commited.")
                    if reslut == 2:
                        conn.rollback()
                        print("\nChanges Discarded.")
                    cursor.close()
                    conn.close()
                    input("\nPress 'Enter' to continue...")
                if reslut == 0:
                    break

        except mysql.connector.Error as error:
            print(f"\nError switching to MySQL database: {error}\nPlease try again.")
            input("\nPress 'Enter' to continue...")
    

def main():
    splash  = """
    Please ensure that you have the corresponding database ready in the SQL server.

    Otherwise, to set up, please execute the given SQL file ("python.sql" ) first.\n

    Hint: You can copy the "value_year" file under the dependency and replace the paths with other qualified CSV files, following the format used in "footystats."

    """
    print(splash)
    if input("Press 'Enter' to proceed if you have everything ready. Would you like to continue for sure? (Y/n):").upper() not in {"","Y"}:
        exit()
    print("# Database Credentials Required #")
    print("Note: Press 'Enter' to use default settings.")
    while(True):
        username, password = get_user_credentials()
        conn = connect_to_mysql(username, password)
        if conn:
            print("Connected Successfully")
            switch_database()
        else:
            print("\n### Invalid credentials or server is unavailable, please check and try again.")

def update_data(cursor):

    data_update_menu = """
    DATA UPDATING MENU:
    (Select table to update data)
    T > Team
    P > Player
    S > Stadium
    G > Game
    B > Back to Main Menu
    """
    print(data_update_menu)
    table_choice = input("Enter choice (T/P/S/G/B): ").strip().upper()
    
    try:
            
        if table_choice == 'T':
            cursor.execute("SELECT * FROM Team")
            teams = cursor.fetchall()
            existing_countries = [row[1] for row in teams]
            for index, team in enumerate(teams):
                print(f"{index+1}: {team[0]}")
            team_index = int(input("Enter the index of the team you want to update: "))-1
            selected_team = teams[team_index]

            print(f"Selected team: {selected_team[0]}")
            new_country = input("Enter new country: ")
            # Update the team in the database
            if new_country not in existing_countries:
                cursor.execute("UPDATE Team SET country = %s WHERE teamName = %s",
                            (new_country, selected_team[0]))
                cursor.execute("SELECT * FROM Team WHERE teamName = %s",
                            (selected_team[0],))
                print("The row updated:")
                print_results(cursor)

                input("\nPress 'Enter' to continue...")
            else:
                print("\n Update failed! One country is limited to have a single team.")


        elif table_choice == 'P':

            cursor.execute("SELECT * FROM Team")
            teams = cursor.fetchall()

            for index, team in enumerate(teams):
                print(f"{index+1}: {team[1]}")  

            team_index = int(input("Enter the index of the team whose player you want to update: "))-1
            selected_team = teams[team_index]

            cursor.execute("SELECT * FROM Player WHERE teamName = %s", (selected_team[0],))
            players = cursor.fetchall()

            for player in players:
                print(f"{player[1]}: {player[2]}") 
            number = int(input("Enter the number of the player you want to update: "))

            cursor.execute("SELECT * FROM Player WHERE teamName = %s AND number = %s", (selected_team[0], number))
            player_details = cursor.fetchone()

            new_position = input("Enter new position (Press Enter to skip): ") or player_details[4]
            new_name = input("Enter new name (Press Enter to skip): ") or player_details[2]
            dob_input = input("Enter new date of birth in format YYYY-MM-DD (Press Enter to skip): ")
            if dob_input:
                if not re.match(r'\d{4}-\d{2}-\d{2}', dob_input):
                    print("Invalid date format. The date of brith won't be updated.")
                    new_dob = player_details[3].strftime('%Y-%m-%d') 
                else:
                    datetime.datetime.strptime(dob_input, '%Y-%m-%d')
                    new_dob = dob_input
            else:
                new_dob = player_details[3].strftime('%Y-%m-%d') 

            cursor.execute("UPDATE Player SET name = %s, position = %s, dob = %s WHERE teamName = %s AND number = %s",
                        (new_name, new_position, new_dob, selected_team[0], number))

            cursor.execute("SELECT * FROM Player WHERE teamName = %s AND number = %s",
                        (selected_team[0], number))
            print("The row updated:")
            print_results(cursor)

            input("\nPress 'Enter' to continue...")




        elif table_choice == 'S':
            cursor.execute("SELECT * FROM Stadium")
            stadiums = cursor.fetchall()
            for index, stadium in enumerate(stadiums):
                print(f"{index+1}: {stadium[0]} in {stadium[1]}")
            stadium_index = int(input("Enter the index of the stadium you want to update: "))-1
            selected_stadium = stadiums[stadium_index]
            print(f"Selected stadium: {selected_stadium[0]} in {selected_stadium[1]}")
            input_city = input("Enter new city (Press Enter to skip): ")
            new_city = input_city or selected_stadium[1]
            cursor.execute("UPDATE Stadium SET city = %s WHERE name = %s",
                        (new_city, selected_stadium[0]))
            cursor.execute("SELECT * FROM Stadium WHERE name = %s",
                        (selected_stadium[0],))
            print("The row updated:")
            print_results(cursor)

            input("\nPress 'Enter' to continue...")

            
        elif table_choice == 'G':
            cursor.execute("SELECT * FROM Game")
            games = cursor.fetchall()
            for index, game in enumerate(games):
                print(f"{index+1}: {game[2]} vs {game[4]} at {game[0]}")
            game_index = int(input("Enter the index of the game you want to update: "))-1
            selected_game = games[game_index]
            print(f"Selected game: {selected_game[2]} vs {selected_game[4]} at {selected_game[0]}")

            # Fetch all stadiums from the database
            cursor.execute("SELECT * FROM Stadium")
            stadiums = cursor.fetchall()

            # Display stadiums with an index
            for index, stadium in enumerate(stadiums):
                print(f"{index+1}: {stadium[0]} in {stadium[1]}")

            # Ask the user to select a stadium by index (optional)
            input_venue_index = input("Enter the index of the new venue (Press Enter to skip): ")
            if input_venue_index:
                new_locate = stadiums[int(input_venue_index)-1][0]
            else:
                new_locate = selected_game[1]  # Keep current venue if input is skipped

            # Ask for new scores (optional)
            input_homeGoal = input("Enter new home team goals (Press Enter to skip): ")
            new_homeGoal = int(input_homeGoal) if input_homeGoal else selected_game[3]
            input_awayGoal = input("Enter new away team goals (Press Enter to skip): ")
            new_awayGoal = int(input_awayGoal) if input_awayGoal else selected_game[5]

            # Update the game in the database
            cursor.execute("""
                UPDATE Game SET 
                    locate = %s, 
                    homeGoal = %s, 
                    awayGoal = %s 
                WHERE homeTeam = %s AND awayTeam = %s AND time = %s
                """, (new_locate, new_homeGoal, new_awayGoal, selected_game[2], selected_game[4], selected_game[0]))

            # Fetch and display the updated game
            cursor.execute("SELECT * FROM Game WHERE homeTeam = %s AND awayTeam = %s AND time = %s",
                        (selected_game[2], selected_game[4], selected_game[0]))
            print("The row updated:")
            print_results(cursor)

            input("\nPress 'Enter' to continue...")
        else:
            if table_choice in {'E', 'X', 'B'}:
                return
            print("Invalid choice.")
    
    except ValueError as ve:
        print(f"Input Error: {ve}")
    except mysql.connector.Error as error:
        print(f"Database Error: {error}")

def delete_data(cursor):
    data_delete_menu = """
    DATA DELETION MENU:
    (Select table to delete data from)
    T > Team
    P > Player
    S > Stadium
    G > Game
    B > Back to Main Menu

    Hint: Prior to deleting any row, please ensure that it is not currently utilized as a foreign key by any other entity. Take the necessary steps to either remove or update the references or eliminate the associated entities before proceeding with the removal

    """
    print(data_delete_menu)
    table_choice = input("Enter choice (T/P/S/G/B): ").strip().upper()

    try:

        if table_choice == 'T':
            cursor.execute("SELECT * FROM Team")
            teams = cursor.fetchall()
            for index, team in enumerate(teams):
                print(f"{index+1}: {team[0]}")
            team_index = int(input("Enter the index of the team you want to delete: "))-1
            selected_team = teams[team_index]

            confirm = input(f"Are you sure you want to delete {selected_team[0]}? (y/n): ").lower()
            if confirm == 'y':
                cursor.execute("DELETE FROM Team WHERE teamName = %s", (selected_team[0],))
                print(f"{selected_team[0]} has been deleted.")
            else:
                print("Deletion cancelled.")

            input("\nPress 'Enter' to continue...")

        # Repeat similar structure for Player, Stadium, and Game
        
        elif table_choice == 'P':
            cursor.execute("SELECT * FROM Team")
            teams = cursor.fetchall()

            for index, team in enumerate(teams):
                print(f"{index+1}: {team[1]}")  

            team_index = int(input("Enter the index of the team whose player you want to delete: "))-1
            selected_team = teams[team_index]

            cursor.execute("SELECT * FROM Player WHERE teamName = %s", (selected_team[0],))
            players = cursor.fetchall()

            for player in players:
                print(f"{player[1]}: {player[2]}") 

            player_number = int(input("Enter the number of the player you want to delete: "))

            # Optional: Fetch and display the player's details before deletion
            cursor.execute("SELECT * FROM Player WHERE teamName = %s AND number = %s", (selected_team[0], player_number))
            player_details = cursor.fetchone()
            if player_details:
                print(f"Player to delete: {player_details[2]} (Number: {player_details[1]}, Team: {selected_team[1]})")
                confirm = input("Are you sure you want to delete this player? (y/n): ").lower()
                if confirm == 'y':
                    cursor.execute("DELETE FROM Player WHERE teamName = %s AND number = %s",
                                   (selected_team[0], player_number))
                    print(f"Player {player_details[2]} has been deleted.")
                else:
                    print("Deletion cancelled.")
            else:
                print("Player not found.")

            input("\nPress 'Enter' to continue...")

        elif table_choice == 'S':
            cursor.execute("SELECT * FROM Stadium")
            stadiums = cursor.fetchall()
            for index, stadium in enumerate(stadiums):
                print(f"{index+1}: {stadium[0]}, City: {stadium[1]}")
            stadium_index = int(input("Enter the index of the stadium you want to delete: "))-1
            selected_stadium = stadiums[stadium_index]

            confirm = input(f"\nMarches in {selected_stadium[0]} will be marked as \"N/A\" for their location.\nAre you certain you want to proceed with the deletion process? (y/n): ").lower()
            if confirm == 'y':
                cursor.execute("DELETE FROM Stadium WHERE name = %s", (selected_stadium[0],))
                print(f"{selected_stadium[0]} has been deleted.")
            else:
                print("Deletion cancelled.")

            input("\nPress 'Enter' to continue...")

        elif table_choice == 'G':
            cursor.execute("SELECT * FROM Game")
            games = cursor.fetchall()
            for index, game in enumerate(games):
                print(f"{index+1}: {game[2]} vs {game[4]} at {game[0]}")
            game_index = int(input("Enter the index of the game you want to delete: "))-1
            selected_game = games[game_index]

            confirm = input(f"Are you sure you want to delete the game between {selected_game[2]} and {selected_game[4]}? (y/n): ").lower()
            if confirm == 'y':
                cursor.execute("DELETE FROM Game WHERE homeTeam = %s AND awayTeam = %s AND time = %s", 
                               (selected_game[2], selected_game[4], selected_game[0]))
                print(f"The game between {selected_game[2]} and {selected_game[4]} has been deleted.")
            else:
                print("Deletion cancelled.")

            input("\nPress 'Enter' to continue...")

        else:
            if table_choice == 'B':
                return
            print("Invalid choice.")

    except ValueError as ve:
        print(f"Input Error: {ve}")
    except mysql.connector.Error as error:
        print(f"Database Error: {error}")



if __name__ == "__main__":
    main()

