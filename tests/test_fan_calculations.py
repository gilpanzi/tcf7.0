import unittest
import sqlite3
from calculations import calculate_fan_weight, calculate_fabrication_cost
from database import get_db_connection

class TestFanCalculations(unittest.TestCase):
    def setUp(self):
        self.conn = get_db_connection()
        self.cursor = self.conn.cursor()

    def tearDown(self):
        self.conn.close()

    def test_calculate_fan_weight(self):
        """Test fan weight calculation with and without accessories"""
        # Test basic fan weight without accessories
        fan_data = {
            'Fan Model': 'BC-SW',
            'Fan Size': '300',
            'Class': '2',
            'Arrangement': 4
        }
        selected_accessories = []
        
        bare_weight, isolators, shaft_dia, total_weight, error = calculate_fan_weight(
            self.cursor, fan_data, selected_accessories
        )
        
        self.assertIsNone(error)
        self.assertEqual(bare_weight, 355)  # Known value from database
        self.assertEqual(total_weight, 355)  # Should equal bare weight when no accessories

        # Test with accessories
        selected_accessories = ['Isolation Base Frame', 'Inlet Companion Flange']
        bare_weight, isolators, shaft_dia, total_weight, error = calculate_fan_weight(
            self.cursor, fan_data, selected_accessories
        )
        
        self.assertIsNone(error)
        self.assertEqual(bare_weight, 355)
        self.assertEqual(total_weight, 415)  # 355 + 48 + 12

    def test_invalid_fan_model(self):
        """Test error handling for invalid fan model"""
        fan_data = {
            'Fan Model': 'INVALID',
            'Fan Size': '300',
            'Class': '2',
            'Arrangement': 4
        }
        selected_accessories = []
        
        bare_weight, isolators, shaft_dia, total_weight, error = calculate_fan_weight(
            self.cursor, fan_data, selected_accessories
        )
        
        self.assertIsNotNone(error)
        self.assertEqual(error, "No matching fan model found")

    def test_fabrication_cost(self):
        """Test fabrication cost calculation"""
        fan_data = {
            'vendor': 'TCF Factory',
            'material': 'ms'
        }
        total_weight = 355
        
        cost, error = calculate_fabrication_cost(self.cursor, fan_data, total_weight)
        
        self.assertIsNone(error)
        self.assertEqual(cost, 74550)  # 355 * 210 (MS price for TCF Factory)

if __name__ == '__main__':
    unittest.main() 