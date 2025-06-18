from datetime import date
from mysql.connector.cursor import MySQLCursor

class Habit:
    """
    Represents a habit that a user wants to track.

    Attributes:
        name (str): The name of the habit.
        periodicity (int): The number of days between habit check-ins.
        date_created (datetime.date): The date the habit was created.
    """

    def __init__(self, name: str, periodicity: int, date_created: date):
        """
        Initialize a new Habit object.

        Args:
            name (str): The name of the habit.
            periodicity (int): The number of days between habit repetitions.
            date_created (datetime.date): The date the habit was created.
        """
        self.name = name
        self.periodicity = periodicity
        self.date_created = date_created

    def save_to_db(self, cursor: MySQLCursor):
        """
        Save the habit to the database.

        Args:
            cursor (mysql.connector.cursor.MySQLCursor): The MySQL cursor to execute queries.

        Returns:
            None
        """
        query = """
            INSERT INTO habits (habit_name, periodicity, date_created)
            VALUES (%s, %s, %s)
        """
        params = (self.name, self.periodicity, self.date_created)
        cursor.execute(query, params)
