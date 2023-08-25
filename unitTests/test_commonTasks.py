import unittest
import sys
from unittest.mock import patch, Mock

sys.path.extend(['/var/www/CatFeeder'])

from commonTasks import *

class TestCommonTasks(unittest.TestCase):

    @patch('commonTasks.sqlite3.connect')
    def test_db_insert_feedtime(self, mock_connect):
        mock_con = Mock()
        mock_cur = Mock()
        mock_con.execute.return_value = mock_cur
        mock_connect.return_value = mock_con

        result = db_insert_feedtime(datetime.datetime.now(), 1)
        self.assertEqual(result, 'ok')

    @patch('commonTasks.sqlite3.connect')
    def test_db_get_last_feedtimes(self, mock_connect):
        mock_con = Mock()
        mock_cur = Mock()
        mock_cur.fetchall.return_value = [('2023-08-25 12:00:00', 'Description')]
        mock_con.execute.return_value = mock_cur
        mock_connect.return_value = mock_con

        result = db_get_last_feedtimes(1)
        self.assertEqual(len(result), 1)

    # Similar tests for other functions...

    @patch('commonTasks.Adafruit_CharLCD')
    def test_print_to_LCDScreen(self, mock_lcd):
        instance = mock_lcd.return_value
        lcd_mock = Mock()
        instance.return_value = lcd_mock

        result = print_to_LCDScreen('Test Message')
        self.assertEqual(result, 'ok')

if __name__ == '__main__':
    unittest.main()
