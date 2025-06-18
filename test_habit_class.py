import pytest
from datetime import date
from habit_class import Habit

def test_habit_initialization():
    name = "Exercise"
    periodicity = 2
    creation_date = date(2025, 6, 1)

    habit = Habit(name, periodicity, creation_date)

    assert habit.name == name
    assert habit.periodicity == periodicity
    assert habit.date_created == creation_date

def test_save_to_db_executes_correct_query(mocker):
    habit = Habit("Read", 3, date(2025, 6, 14))
    mock_cursor = mocker.Mock()

    habit.save_to_db(mock_cursor)

    expected_query = """
            INSERT INTO habits (habit_name, periodicity, date_created)
            VALUES (%s, %s, %s)
        """
    expected_params = ("Read", 3, date(2025, 6, 14))

    mock_cursor.execute.assert_called_once_with(expected_query, expected_params)
