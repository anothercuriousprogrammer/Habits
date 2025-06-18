import mysql.connector
import datetime
import analytics
from habit_class import Habit
import pytest

DB_NAME = "test_habits_database"

# Creation date for all the sample habit objects
CREATION_DATE = datetime.date(2025, 4, 1)

# Sample habit objects
SAMPLE_HABITS = [
    Habit("Study(TEST)", 1, CREATION_DATE),
    Habit("Water the Plants(TEST)", 7, CREATION_DATE),
    Habit("Workout(TEST)", 1, CREATION_DATE),
    Habit("Read(TEST)", 3, CREATION_DATE),
    Habit("Meditate(TEST)", 7, CREATION_DATE),
]

# Sample Checkoff data for habit objects
CHECKOFFS = {
    SAMPLE_HABITS[0].name: [d for d in range(1, 31) if d not in [4, 12, 15, 28]],               # Study
    SAMPLE_HABITS[1].name: [1, 6, 11, 18, 25, 30],                                              # Water the Plants
    SAMPLE_HABITS[2].name: [d for d in range(1, 31) if d not in [2, 7, 12, 19, 23, 24, 25]],    # Workout
    SAMPLE_HABITS[3].name: [1, 5, 6, 7, 9, 12, 14, 16, 17, 19, 20, 22, 23, 25, 30],             # Read
    SAMPLE_HABITS[4].name: [1, 6, 13, 24, 30],                                                  # Meditate
}

# Dates on which to check current streaks, with expected streak counts per habit
EXPECTED_CURRENT_STREAKS = {
    datetime.date(2025, 4, 11): {
        SAMPLE_HABITS[0].name: 7,   # Study
        SAMPLE_HABITS[1].name: 3,   # Water the plants
        SAMPLE_HABITS[2].name: 4,   # Workout
        SAMPLE_HABITS[3].name: 4,   # Read
        SAMPLE_HABITS[4].name: 2,   # Meditate
    },
    datetime.date(2025, 4, 16): {
        SAMPLE_HABITS[0].name: 1,   # Study
        SAMPLE_HABITS[1].name: 3,   # Water the plants
        SAMPLE_HABITS[2].name: 4,   # Workout
        SAMPLE_HABITS[3].name: 7,   # Read
        SAMPLE_HABITS[4].name: 3,   # Meditate
    },
    datetime.date(2025, 4, 26): {
        SAMPLE_HABITS[0].name: 11,  # Study
        SAMPLE_HABITS[1].name: 5,   # Water the plants
        SAMPLE_HABITS[2].name: 1,   # Workout
        SAMPLE_HABITS[3].name: 13,  # Read
        SAMPLE_HABITS[4].name: 1,   # Meditate
    },
}

# Expected longest streak counts for each habit
EXPECTED_LONGEST_STREAKS = {
        SAMPLE_HABITS[0].name: 12,  # Study(TEST)
        SAMPLE_HABITS[1].name: 6,   # Water the Plants(TEST)
        SAMPLE_HABITS[2].name: 6,   # Workout(TEST)
        SAMPLE_HABITS[3].name: 13,   # Read(TEST)
        SAMPLE_HABITS[4].name: 3,   # Meditate(TEST)
    }

@pytest.fixture(scope="module")
def testing_cursor():
    """
    Creates a MySQL connection and cursor for testing.
    Yields the cursor and ensures cleanup afterward.
    """
    connection = mysql.connector.connect(
        host="localhost",
        user="root",
        password="MYpassword"
    )
    cursor = connection.cursor()
    yield cursor, connection

    # Cleanup: drop the test database after tests run
    cursor.execute(f"DROP DATABASE IF EXISTS {DB_NAME}")
    connection.commit()
    cursor.close()
    connection.close()

def test_create_and_check_database(testing_cursor):
    """
    Test the creation and existence check of the database.

    This test verifies that the specified database does not initially exist,
    creates it using the analytics module, commits the change, and then confirms
    that the database now exists.
    """
    cursor, connection = testing_cursor

    # Confirm that the DB doesn't exist
    assert not analytics.check_database_exists(cursor, DB_NAME)

    # Create the DB
    analytics.create_database(cursor, DB_NAME)
    connection.commit()  # commit DB creation

    # Confirm it now exists
    assert analytics.check_database_exists(cursor, DB_NAME)

def test_create_sample_habits(testing_cursor):
    """
    Test that 5 sample habits can be created and are stored in the database.
    """
    cursor, connection = testing_cursor

    cursor.execute(f"USE {DB_NAME}")

    count_created = 0

    for habit in SAMPLE_HABITS:
        analytics.create_habit(cursor, habit)
        count_created += 1

    connection.commit()  # Commit all inserts after creation

    assert count_created == 5, f"Expected to create 5 habits, but created {count_created}"

    print("✅ 5 sample habits were successfully created.")

def test_get_habit_id(testing_cursor):
    """
    Tests the analytics.get_habit_id function to ensure it returns the correct habit ID for given habit names in the test database.

    Asserts:
        - The habit ID for "Read(TEST)" is 4.
        - The habit ID for "Study(TEST)" is 1.
    """
    cursor, connection = testing_cursor
    cursor.execute(f"USE {DB_NAME}")

    habit_name_1 = SAMPLE_HABITS[3].name
    habit_id_1 = analytics.get_habit_id(cursor, habit_name_1)
    assert habit_id_1 == 4, f"Expected habit_id 4 for '{habit_name_1}', got {habit_id_1}"

    habit_name_2 = SAMPLE_HABITS[0].name
    habit_id_2 = analytics.get_habit_id(cursor, habit_name_2)
    assert habit_id_2 == 1, f"Expected habit_id 1 for '{habit_name_2}', got {habit_id_2}"

def test_check_off_and_get_current_streak(testing_cursor):
    """
    Simulates the usage of the application for April 2025, incrementing day by day.
    On each day, if the day is in CHECKOFFS for that habit: Assert the function is not checked off for the new day before this function checks it off, then check it off and assert success.
    On dates in EXPECTED_CURRENT_STREAKS, assert the current streak is calculated correctly.
    """
    cursor, connection = testing_cursor
    cursor.execute(f"USE {DB_NAME}")

    # Map habit names to habit_ids using get_habit_id
    habit_ids = {}
    for habit in SAMPLE_HABITS:
        habit_id = analytics.get_habit_id(cursor, habit.name)
        assert habit_id is not None, f"Habit '{habit.name}' should exist in DB"
        habit_ids[habit.name] = habit_id

    # Number of days to simulate (1 month)
    days_in_month = 30

    # Iterate day by day starting from creation date
    for day_offset in range(days_in_month):
        current_date = CREATION_DATE + datetime.timedelta(days=day_offset)

        for habit_name, habit_id in habit_ids.items():
            # Check if this day (day number) is in the habit's checkoff list
            day_num = current_date.day

            if day_num in CHECKOFFS[habit_name]:
                # Before check off, assert habit not checked off for this day
                assert not analytics.is_habit_checked_off(cursor, habit_id, current_date), (
                    f"Habit '{habit_name}' should NOT be checked off for {current_date} before test"
                )

                # Update streaks (done in start-up of the application) and check off habit
                analytics.update_streaks(cursor, habit_id, current_date)
                analytics.check_off_habit(cursor, habit_id, current_date)

                connection.commit()

                # Assert habit is now checked off for this date
                assert analytics.is_habit_checked_off(cursor, habit_id, current_date), (
                    f"Habit '{habit_name}' was not checked off for {current_date}"
                )

            # If this date is in EXPECTED_CURRENT_STREAKS, assert streak data matches the expected
            if current_date in EXPECTED_CURRENT_STREAKS:
                expected_streak = EXPECTED_CURRENT_STREAKS[current_date].get(habit_name)
                current_streak = analytics.get_current_streak(cursor, habit_id)
                assert current_streak == expected_streak, (
                    f"On {current_date}, habit '{habit_name}' has streak {current_streak}, expected {expected_streak}"
                    )

    print("✅ Incremental day-by-day habit check-offs and streak verifications passed successfully.")

def test_habit_check_offs(testing_cursor):
    """
    Tests the is_habit_checked_off function to verify if specific habits are correctly marked
    as checked off or not on given dates.

    Asserts:
        - Study(TEST) is checked off on April 3, 2025, but not on April 15, 2025.
        - Workout(TEST) is checked off on April 5, 2025, but not on April 19, 2025.
        - Meditate(TEST) is not checked off on April 3, 2025, but is checked off on April 6, 2025.

    """
    cursor, connection = testing_cursor
    cursor.execute(f"USE {DB_NAME}")

    # Get habit IDs
    study_id = analytics.get_habit_id(cursor, SAMPLE_HABITS[0].name)
    workout_id = analytics.get_habit_id(cursor, SAMPLE_HABITS[2].name)
    meditate_id = analytics.get_habit_id(cursor, SAMPLE_HABITS[4].name)

    # Study(TEST)
    assert analytics.is_habit_checked_off(cursor, study_id, datetime.date(2025, 4, 3)) is True
    assert analytics.is_habit_checked_off(cursor, study_id, datetime.date(2025, 4, 15)) is False

    # Workout(TEST)
    assert analytics.is_habit_checked_off(cursor, workout_id, datetime.date(2025, 4, 5)) is True
    assert analytics.is_habit_checked_off(cursor, workout_id, datetime.date(2025, 4, 19)) is False

    # Meditate(TEST)
    assert analytics.is_habit_checked_off(cursor, meditate_id, datetime.date(2025, 4, 3)) is False
    assert analytics.is_habit_checked_off(cursor, meditate_id, datetime.date(2025, 4, 6)) is True

def test_get_habit_by_periodicity(testing_cursor):
    """
    Tests the get_habit_by_periodicity function with various periodicities (1, 7, 30).
    Ensures it returns the correct habit names from the test database.
    """
    cursor, _ = testing_cursor
    cursor.execute(f"USE {DB_NAME}")

    # Periodicity: 1-day habits
    result_1 = analytics.get_habit_by_periodicity(cursor, 1)
    expected_1 = {SAMPLE_HABITS[0].name, SAMPLE_HABITS[2].name}
    assert set(result_1) == expected_1

    # Periodicity: 7-day habits
    result_7 = analytics.get_habit_by_periodicity(cursor, 7)
    expected_7 = {SAMPLE_HABITS[1].name, SAMPLE_HABITS[4].name}
    assert set(result_7) == expected_7

    # Periodicity: 30-day (not in sample)
    result_30 = analytics.get_habit_by_periodicity(cursor, 30)
    assert result_30 == []

def test_get_all_habits(testing_cursor):
    """
    Tests the get_all_habits function to ensure it returns all habit names from the database.
    """
    cursor, _ = testing_cursor
    cursor.execute(f"USE {DB_NAME}")

    habit_names = analytics.get_all_habits(cursor)
    expected_names = [habit.name for habit in SAMPLE_HABITS]

    assert set(habit_names) == set(expected_names)

def test_get_longest_streak(testing_cursor):
    """
    Tests the get_longest_streak function using SAMPLE_HABITS for habit names
    and a predefined mapping for expected longest streaks.
    """
    cursor, _ = testing_cursor
    cursor.execute(f"USE {DB_NAME}")

    for habit in SAMPLE_HABITS:
        habit_id = analytics.get_habit_id(cursor, habit.name)
        assert habit_id is not None, f"Habit ID for '{habit.name}' should exist"

        longest_streak = analytics.get_longest_streak(cursor, habit_id)
        expected = EXPECTED_LONGEST_STREAKS[habit.name]
        assert longest_streak == expected, (
            f"Longest streak for '{habit.name}' was {longest_streak}, expected {expected}"
        )
