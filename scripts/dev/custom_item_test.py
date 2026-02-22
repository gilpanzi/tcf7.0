from flask import Flask, render_template, session, request
import os
import re
import json

app = Flask(__name__, template_folder=os.path.abspath('.'))
app.secret_key = 'test_key'
app.config['SERVER_NAME'] = 'localhost:5000'

def print_dict(d, indent=0):
    for key, value in d.items():
        if isinstance(value, dict):
            print(' ' * indent + str(key) + ':')
            print_dict(value, indent + 4)
        else:
            print(' ' * indent + str(key) + ': ' + str(value))

def test_display_custom_optional_items():
    # Create a fan with AMCA Type C Spark Proof Construction
    fan_data = {
        'specifications': {
            'fan_model': 'BC-SW',
            'size': '270',
            'class': '1',
            'arrangement': '4',
            'vibration_isolators': 'dunlop',
            # Test both regular optional items and custom optional items
            'optional_items': {
                'prices': {
                    'flex_connectors': 5000,
                    'silencer': 5000
                }
            },
            # This is where AMCA Type C Spark Proof Construction should be
            'custom_optional_items': {
                'amca_type_c_spark_proof_construction': 5000
            }
        },
        'motor': {
            'brand': '',
            'kw': 0,
            'pole': 0,
            'efficiency': '',
            'discount_rate': 0
        },
        'weights': {
            'total_weight': 300,
            'bare_fan_weight': 255,
            'accessory_weight': 45
        },
        'costs': {
            'total_cost': 94000,
            'fabrication_cost': 63000,
            'bought_out_cost': 31000,
            'motor_cost': 0,
            'vibration_isolators_cost': 16000,
            'bearing_cost': 0,
            'drive_pack_cost': 0,
            'optional_items_cost': 15000,
            'total_selling_price': 140333.33
        }
    }
    
    # Create a test request context to build URLs
    with app.test_request_context('/'):
        # Test dictionary format of custom optional items
        try:
            html = render_template('templates/summary.html', 
                                  fans=[fan_data], 
                                  enquiry_number='TEST123', 
                                  customer_name='Test Customer', 
                                  sales_engineer='Test Engineer',
                                  total_fans=1,
                                  total_weight=300,
                                  total_fabrication_cost=63000,
                                  total_bought_out_cost=31000,
                                  total_cost=94000)
            
            # We need a simple pattern to match because the HTML might have line breaks and whitespace
            pattern = r'amca.*type.*c.*spark.*proof.*construction'
            if re.search(pattern, html.lower()):
                print("SUCCESS: AMCA Type C Spark Proof Construction is visible in the summary")
            else:
                print("FAILURE: AMCA Type C Spark Proof Construction is NOT visible in the summary")
                # Print the custom optional items section
                print("\nDebug - Looking for custom optional items:")
                custom_items_start = html.find('Custom Optional Items')
                if custom_items_start > -1:
                    section_end = html.find('</div>', custom_items_start)
                    print(html[custom_items_start:section_end+6])
                else:
                    print("Could not find 'Custom Optional Items' section in HTML")
        except Exception as e:
            print(f"Exception in first test: {str(e)}")
        
        # Test array notation format
        try:
            # Create with direct key since bracket notation might be special
            fan_data_2 = {
                'specifications': {
                    'fan_model': 'BC-SW',
                    'size': '270',
                    'class': '1',
                    'arrangement': '4',
                    'vibration_isolators': 'dunlop',
                }
            }
            # Add the array notation field separately
            fan_data_2['specifications']['custom_optional_items[]'] = 'AMCA Type C Spark Proof Construction'
            
            fan_data_2.update({
                'motor': {
                    'brand': '',
                    'kw': 0,
                    'pole': 0,
                    'efficiency': '',
                    'discount_rate': 0
                },
                'weights': {
                    'total_weight': 300,
                    'bare_fan_weight': 255,
                    'accessory_weight': 45
                },
                'costs': {
                    'total_cost': 94000,
                    'fabrication_cost': 63000,
                    'bought_out_cost': 31000,
                    'motor_cost': 0,
                    'vibration_isolators_cost': 16000,
                    'bearing_cost': 0,
                    'drive_pack_cost': 0,
                    'optional_items_cost': 15000,
                    'total_selling_price': 140333.33
                }
            })
            
            # Print the fan data structure to verify
            print("\nFan data 2 structure:")
            print_dict(fan_data_2)
            print("\nVerify 'custom_optional_items[]' in specifications:", 'custom_optional_items[]' in fan_data_2['specifications'])
            print("Value of 'custom_optional_items[]':", fan_data_2['specifications'].get('custom_optional_items[]'))
            
            html2 = render_template('templates/summary.html', 
                                  fans=[fan_data_2], 
                                  enquiry_number='TEST123', 
                                  customer_name='Test Customer', 
                                  sales_engineer='Test Engineer',
                                  total_fans=1,
                                  total_weight=300,
                                  total_fabrication_cost=63000,
                                  total_bought_out_cost=31000,
                                  total_cost=94000)
            
            # Check for the item in the HTML output
            if 'AMCA Type C Spark Proof Construction' in html2:
                print("\nSUCCESS: Array notation format works for custom optional items")
            else:
                print("\nFAILURE: Array notation format does NOT work for custom optional items")
                # Print the custom optional items section
                print("\nDebug - Looking for custom optional items in array notation format:")
                custom_items_start = html2.find('Custom Optional Items')
                if custom_items_start > -1:
                    section_end = html2.find('</div>', custom_items_start)
                    print(html2[custom_items_start:section_end+6])
                else:
                    print("Could not find 'Custom Optional Items' section in HTML")
        except Exception as e:
            print(f"Exception in second test: {str(e)}")

if __name__ == "__main__":
    test_display_custom_optional_items() 