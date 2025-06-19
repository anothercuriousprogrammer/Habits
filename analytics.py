import mysql.connector
import datetime
from habit_class import Habit

def create_database(cursor, db_name):
    """
    This function creates a MySQL database named after db_name input and three tables inside that database:

    - `habits`: Stores information about each habit (name, periodicity, creation date).
    - `check_off_dates`: Records the dates when habits are checked off.
    - `streaks`: Tracks current and longest streaks for each habit.

    The function uses a cursor as an input to execute SQL commands. It ensures that
    foreign key constraints are applied with cascading updates and deletions.

    Args:
        cursor (mysql.connector.cursor.MySQLCursor): The MySQL cursor used to execute SQL statements.
        db_name (str): The name of the database that will be created.

    Returns:
        None
    """

    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name}")
    cursor.execute(f"USE {db_name}")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS habits (
            id INT AUTO_INCREMENT PRIMARY KEY,
            habit_name VARCHAR(100) NOT NULL,
            periodicity INT NOT NULL,
            date_created DATE NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS check_off_dates (
            habit_id INT NOT NULL,
            check_off_date DATE NOT NULL,
            FOREIGN KEY (habit_id) REFERENCES habits(id)
                ON DELETE CASCADE
                ON UPDATE CASCADE
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS streaks (
            habit_id INT PRIMARY KEY,
            current_streak INT NOT NULL,
            longest_streak INT NOT NULL,
            FOREIGN KEY (habit_id) REFERENCES habits(id)
                ON DELETE CASCADE
                ON UPDATE CASCADE
        )
    """)

    print(f"Database {db_name} and tables created successfully.")

def check_database_exists(cursor, db_name):
    """
    Check if the database named after db_name input exists in the MySQL server.

    Args:
        cursor (mysql.connector.cursor.MySQLCursor): The MySQL cursor used to execute the query.
        db_name (str): The name of the database to look for.

    Returns:
        bool: True if the database exists, False otherwise.
    """
    try:
        cursor.execute(f"SHOW DATABASES LIKE '{db_name}'")
        result = cursor.fetchone()
        return result is not None
    except mysql.connector.Error as err:
        print("Database query failed:", err)
        return False

def create_habit(cursor, habit: Habit):
    """
    Creates a habit and initializes its streak in the database (no commit inside).

    Args:
        cursor (mysql.connector.cursor.MySQLCursor): Database cursor.
        habit (Habit): The Habit object to be created.

    Returns:
        None
    """
    def initialize_streak_for_habit(cursor, habit_id):
        """
        Inserts an initial streak record for the given habit_id,
        setting current_streak and longest_streak to 0.
        """
        streak_query = """
            INSERT INTO streaks (habit_id, current_streak, longest_streak)
            VALUES (%s, %s, %s)
        """
        cursor.execute(streak_query, (habit_id, 0, 0))

    existing_habit_id = get_habit_id(cursor, habit.name)
    if existing_habit_id is not None:
        print(f"Habit '{habit.name.upper()}' already exists.")
        return

    habit.save_to_db(cursor)

    new_habit_id = get_habit_id(cursor, habit.name)
    initialize_streak_for_habit(cursor, new_habit_id)

    print(f"Habit '{habit.name}' with a periodicity of {habit.periodicity} days was created successfully on {habit.date_created}.")

def get_habit_id(cursor, habit_name: str):
    """
    Retrieve the habit_id for a given habit_name from the habits table.

    Args:
        cursor (mysql.connector.cursor.MySQLCursor): The MySQL cursor used to execute SQL statements.
        habit_name (str): The name of the habit to look up.

    Returns:
        int or None: The habit_id if found, otherwise None.
    """
    query = "SELECT id FROM habits WHERE habit_name = %s"
    cursor.execute(query, (habit_name,))
    result = cursor.fetchone()
    if result:
        return result[0]  # id is the first column in the result tuple
    else:
        return None

def is_habit_checked_off(cursor, habit_id: int, check_date: datetime.date):
    """
    Check if the habit is already checked off on the given date.

    Args:
        cursor (mysql.connector.cursor.MySQLCursor): The DB cursor.
        habit_id (int): The habit's unique ID.
        check_date (datetime.date): The date to check.

    Returns:
        bool: True if the habit is checked off on check_date, False otherwise.
    """
    query = """
    SELECT 1 FROM check_off_dates WHERE habit_id = %s AND check_off_date = %s LIMIT 1
    """
    cursor.execute(query, (habit_id, check_date))
    return cursor.fetchone() is not None

def check_off_habit(cursor, habit_id: int, check_date: datetime.date):
    """
    Insert a check-off record for a habit on a given date and update the streaks table. Increments the current_streak by 1, if the current streak is greater than the longest_streak, changes the longest_streak to the value of the current_streak.

    Args:
        cursor (mysql.connector.cursor.MySQLCursor): The MySQL cursor to execute queries.
        habit_id (int): The unique identifier of the habit.
        check_date (datetime.date): The date to check off the habit.

    Returns:
        None
    """
    # Insert the check-off date into check_off_dates table
    insert_checkoff_query = """
        INSERT INTO check_off_dates (habit_id, check_off_date)
        VALUES (%s, %s)
    """
    cursor.execute(insert_checkoff_query, (habit_id, check_date))

    # Update the streaks table
    cursor.execute("""UPDATE streaks SET current_streak = current_streak + 1 WHERE habit_id = %s""", (habit_id,))
    cursor.execute("""UPDATE streaks SET longest_streak = current_streak WHERE habit_id = %s AND current_streak > longest_streak""", (habit_id,))

def update_streaks(cursor, habit_id: int, todays_date: datetime.date):
    """
    Updates the streaks table for a given habit id and date. Resets the current_streak to 0 if a habit streak is broken on that date; otherwise, leaves it unchanged.

    Args:
        cursor (mysql.connector.cursor.MySQLCursor): The MySQL cursor to execute queries.
        habit_id (int): The unique identifier of the habit in the database.
        todays_date (datetime.date): Today's date when the habit was checked off.

    Returns:
        None
    """

    cursor.execute("SELECT periodicity FROM habits WHERE id = %s", (habit_id,))
    result = cursor.fetchone()
    periodicity = result[0]

    streak_unbroken = False

    # Check if habit was checked off at least once in the last 'periodicity' days (before todays_date)
    for i in range(0, periodicity + 1):
        check_date = todays_date - datetime.timedelta(days=i)
        cursor.execute("""SELECT 1 FROM check_off_dates WHERE habit_id = %s AND check_off_date = %s""", (habit_id, check_date))
        if cursor.fetchone():
            streak_unbroken = True
            break

    if not streak_unbroken:
        # Streak is broken, reset current streak to 0
        cursor.execute("""UPDATE streaks SET current_streak = 0 WHERE habit_id = %s""", (habit_id,))
    # Else: Do nothing if the streak is unbroken

def get_all_habits(cursor):
    """
    Fetch all habit names from the database.

    Args:
        cursor (mysql.connector.cursor.MySQLCursor): The MySQL cursor.

    Returns:
        list of str: List of habit names.
    """
    query = "SELECT habit_name FROM habits"
    cursor.execute(query)
    results = cursor.fetchall()
    return [row[0] for row in results]  # Extract habit names from tuples

def get_longest_streak(cursor, habit_id: int):
    """
    Retrieve the longest streak for a given habit ID.

    Args:
        cursor (mysql.connector.cursor.MySQLCursor): The MySQL cursor to execute queries.
        habit_id (int): The unique identifier of the habit.

    Returns:
        int | None: The longest streak value, or None if not found.
    """
    cursor.execute("SELECT longest_streak FROM streaks WHERE habit_id = %s", (habit_id,))
    result = cursor.fetchone()

    if result:
        return result[0]  # longest_streak is the first column in the result tuple
    else:
        return None

def get_current_streak(cursor, habit_id: int):
    """
    Get the current streak for a habit by habit_id.

    Args:
        cursor (mysql.connector.cursor.MySQLCursor): The MySQL cursor.
        habit_id (int): The id of the habit.

    Returns:
        int: The current streak count (0 if none found).
    """
    query = "SELECT current_streak FROM streaks WHERE habit_id = %s"
    cursor.execute(query, (habit_id,))
    result = cursor.fetchone()
    if result:
        return result[0]
    else:
        return 0

def get_habit_by_periodicity(cursor, period: int):
    """
    Retrieves habits with the specified periodicity.

    Args:
        cursor: Database cursor object.
        period (int): Periodicity in days to filter habits.

    Returns:
        list[str]: List of habit names with the given periodicity.
    """
    query = "SELECT habit_name FROM habits WHERE periodicity = %s"
    cursor.execute(query, (period,))
    habits = cursor.fetchall()

    return [habit[0] for habit in habits]
