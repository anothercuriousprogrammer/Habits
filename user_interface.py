import datetime
import mysql.connector
from habit_class import Habit
import analytics

# Global variable for today's date
todays_date = None


def main():
    """
    Main entry point for the Habits application.

    Establishes a connection to the MySQL server, ensures the habits database
    exists (creating it if necessary), and then launches an interactive command-line
    interface for managing habits.

    Raises:
        mysql.connector.Error: If any database query or connection error occurs.
    """

    global todays_date

    print("Welcome to Habits!!!")

    connection = None
    cursor = None
    db_name = "habits_database"

    try:
        connection = mysql.connector.connect(
            host="localhost",
            user="root",
            password="MYpassword"
        )
        cursor = connection.cursor()

        if analytics.check_database_exists(cursor, db_name):
            cursor.execute(f"USE {db_name}")
            print("Database located successfully.")

        else:
            print("Database not found. Creating database...")
            analytics.create_database(cursor, db_name)
            connection.commit()
            cursor.execute(f"USE {db_name}")
            print("Database created successfully.")

        print("Write INFO for information on how to use the application.")

        todays_date = datetime.date.today()

        # Update the streaks table for all habits for today to set the current_streak for all habits
        habit_names = analytics.get_all_habits(cursor)
        for habit_name in habit_names:
            habit_id = analytics.get_habit_id(cursor, habit_name)
            analytics.update_streaks(cursor, habit_id, todays_date)
        connection.commit()

        while True:
            command = input("> ").strip().lower()

            match command:

                case "info":
                    print(f"""
                        Available commands:
                        - CREATE HABIT                     : Create a new habit
                        - CHECK OFF                        : Mark a habit as completed for today
                        - LIST HABITS                      : List all habit names
                        - LIST HABITS BY PERIODICITY       : List habits filtered by periodicity (in days)
                        - LIST HABITS WITH LONGEST STREAK  : List habits and their longest streak
                        - LIST HABITS WITH CURRENT STREAK  : List habits and their current streak
                        - GET LONGEST STREAK               : Get the longest streak for a specific habit
                        - GET CURRENT STREAK               : Get the current streak for a specific habit
                        - INFO                             : Show this information
                        - EXIT                             : Exit the program

                        Today's date: {todays_date}
                    """)

                case "create habit":
                    name = input("Enter habit name: ").strip()

                    while True:
                        try:
                            periodicity = int(
                                input("Enter periodicity in days (e.g. 1 for daily, 7 for weekly): ").strip())
                            break
                        except ValueError:
                            print("Please enter a valid integer for periodicity.")

                    new_habit = Habit(name=name, periodicity=periodicity, date_created=todays_date)
                    analytics.create_habit(cursor, new_habit)
                    connection.commit()

                case "check off":
                    habit_name = input("Enter habit name to check off: ").strip()
                    habit_id = analytics.get_habit_id(cursor, habit_name)

                    if habit_id is None:
                        print(f"Habit '{habit_name.upper()}' does not exist.")
                    else:
                        if analytics.is_habit_checked_off(cursor, habit_id, todays_date):
                            print(f"Habit '{habit_name.upper()}' is already checked off for {todays_date}.")
                        else:
                            analytics.check_off_habit(cursor, habit_id, todays_date)
                            connection.commit()
                            print(f"Habit '{habit_name.upper()}' checked off for {todays_date}.")

                case "list habits":
                    habits = analytics.get_all_habits(cursor)
                    print("All habits:")
                    for habit_name in habits:
                        print(f"- {habit_name.upper()}")

                case "list habits by periodicity":
                    try:
                        period = int(input("Enter periodicity in days to filter habits: ").strip())
                        habit_names = analytics.get_habit_by_periodicity(cursor, period)

                        if habit_names:
                            print(f"Habits with periodicity {period} days:")
                            for name in habit_names:
                                print(f"- {name.upper()}")
                        else:
                            print(f"No habits found with periodicity {period} days.")

                    except ValueError:
                        print("Please enter a valid integer.")

                case "get longest streak":
                    habit_name = input("Enter habit name: ").strip()
                    habit_id = analytics.get_habit_id(cursor, habit_name)

                    if habit_id is None:
                        print(f"Habit '{habit_name.upper()}' does not exist.")
                    else:
                        longest_streak = analytics.get_longest_streak(cursor, habit_id)
                        print(f"The longest streak for habit '{habit_name.upper()}' is: {longest_streak}")

                case "get current streak":
                    habit_name = input("Enter habit name: ").strip()
                    habit_id = analytics.get_habit_id(cursor, habit_name)

                    if habit_id is None:
                        print(f"Habit '{habit_name.upper()}' does not exist.")
                    else:
                        current_streak = analytics.get_current_streak(cursor, habit_id)
                        print(f"The current streak for habit '{habit_name.upper()}' is: {current_streak} on {todays_date}")

                case "list habits with longest streak":
                    habit_names = analytics.get_all_habits(cursor)

                    print("Habits and their longest streaks:")
                    for habit_name in habit_names:
                        habit_id = analytics.get_habit_id(cursor, habit_name)
                        longest_streak = analytics.get_longest_streak(cursor, habit_id)
                        print(f"- {habit_name.upper()}: Longest streak = {longest_streak}")

                case "list habits with current streak":
                    habit_names = analytics.get_all_habits(cursor)
                    print(f"Habits and their current streaks on {todays_date}:")
                    for habit_name in habit_names:
                        habit_id = analytics.get_habit_id(cursor, habit_name)
                        current_streak = analytics.get_current_streak(cursor, habit_id)
                        print(f"- {habit_name.upper()}: Current streak = {current_streak}")

                case "exit":
                    print("Goodbye! See you soon!")
                    break

                case _:
                    print("Invalid command. Write INFO for available commands.")


    except mysql.connector.Error as err:
        print("Database query failed:", err)

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


if __name__ == "__main__":
    main()
