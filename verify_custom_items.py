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

def restructure_fan_data(raw_fan_data):
    """
    This function takes raw fan data (as received by the summary route)
    and restructures it to ensure custom_optional_items[] is properly handled.
    
    Copy this logic to the routes.py file in the summary route.
    """
    print("Restructuring raw fan data for correct template rendering...")
    
    processed_fans = []
    for fan in raw_fan_data:
        # Skip if not a dictionary
        if not isinstance(fan, dict):
            print(f"Skipping non-dictionary fan data: {type(fan)}")
            continue
        
        # Ensure 'specifications' exists
        if 'specifications' not in fan:
            fan['specifications'] = {}
        
        # Direct copy of custom_optional_items[] to specifications
        if 'custom_optional_items[]' in fan and 'custom_optional_items[]' not in fan['specifications']:
            fan['specifications']['custom_optional_items[]'] = fan['custom_optional_items[]']
            print(f"Copied custom_optional_items[] value to specifications: {fan['custom_optional_items[]']}")
            
            # Also add as regular dictionary entry for backwards compatibility
            if 'custom_optional_items' not in fan['specifications']:
                fan['specifications']['custom_optional_items'] = {}
            
            item_name = fan['custom_optional_items[]']
            item_id = item_name.lower().replace(' ', '_')
            fan['specifications']['custom_optional_items'][item_id] = 0
            print(f"Added to custom_optional_items dictionary with ID: {item_id}")
        
        processed_fans.append(fan)
    
    return processed_fans

def test_with_raw_data():
    # Create fan data directly from the JSON string in user's message
    json_data = '[{"fan_model":"BC-SW","fan_size":"222","class_":"1","arrangement":"4","vendor":"TCF Factory","vendor_rate":"210","moc":"ms","material_name_0":"","material_weight_0":"","material_rate_0":"","material_name_1":"","material_weight_1":"","material_rate_1":"","material_name_2":"","material_weight_2":"","material_rate_2":"","material_name_3":"","material_weight_3":"","material_rate_3":"","material_name_4":"","material_weight_4":"","material_rate_4":"","custom_no_of_isolators":"","custom_shaft_diameter":"","vibration_isolators":"dunlop","bearing_brand":"","motor_brand":"","motor_kw":"","pole":"","efficiency":"","motor_discount":"0","drive_pack":"","drive_pack_kw":"","fabrication_margin":"25","bought_out_margin":"25","flex_connectors":"required","silencer":"not_required","testing_charges":"not_required","freight_charges":"not_required","warranty_charges":"not_required","packing_charges":"not_required","custom_optional_items[]":"AMCA Type C Spark Proof Construction","material":"ms","accessories":{},"bare_fan_weight":165,"accessory_weights":0,"total_weight":165,"fabrication_cost":34650,"fabrication_selling_price":46200,"vibration_isolators_cost":12000,"no_of_isolators":6,"shaft_diameter":null,"drive_pack_cost":0,"bearing_cost":0,"motor_cost":0,"optional_items":{"flex_connectors":5000},"bought_out_cost":22000,"optional_items_cost":10000,"bought_out_selling_price":29333.333333333332,"total_cost":56650,"total_selling_price":75533.33333333333,"total_job_margin":25,"resultsVisible":true}]'
    fan_data = json.loads(json_data)
    
    # Create a properly structured fan data for templating
    structured_fans = []
    for fan in fan_data:
        # Create a fan with proper nested structure
        structured_fan = {
            'specifications': {
                'fan_model': fan.get('fan_model', ''),
                'size': fan.get('fan_size', ''),
                'class': fan.get('class_', ''),
                'arrangement': fan.get('arrangement', ''),
                'vibration_isolators': fan.get('vibration_isolators', ''),
                'bearing_brand': fan.get('bearing_brand', '')
            },
            'motor': {
                'brand': fan.get('motor_brand', ''),
                'kw': fan.get('motor_kw', ''),
                'pole': fan.get('pole', ''),
                'efficiency': fan.get('efficiency', ''),
            },
            'weights': {
                'total_weight': fan.get('total_weight', 0),
                'bare_fan_weight': fan.get('bare_fan_weight', 0),
                'accessory_weight': fan.get('accessory_weights', 0)
            },
            'costs': {
                'total_cost': fan.get('total_cost', 0),
                'fabrication_cost': fan.get('fabrication_cost', 0),
                'bought_out_cost': fan.get('bought_out_cost', 0),
                'vibration_isolators_cost': fan.get('vibration_isolators_cost', 0),
                'motor_cost': fan.get('motor_cost', 0),
                'drive_pack_cost': fan.get('drive_pack_cost', 0),
                'bearing_cost': fan.get('bearing_cost', 0)
            }
        }
        
        # Handle optional items
        if 'optional_items' in fan and isinstance(fan['optional_items'], dict):
            structured_fan['specifications']['optional_items'] = {
                'prices': fan['optional_items']
            }
        
        # Important: Copy the custom_optional_items[] field to specifications
        if 'custom_optional_items[]' in fan:
            # Method 1: Copy to specifications with the [] notation
            structured_fan['specifications']['custom_optional_items[]'] = fan['custom_optional_items[]']
            
            # Method 2: Also add to custom_optional_items dictionary format
            if 'custom_optional_items' not in structured_fan['specifications']:
                structured_fan['specifications']['custom_optional_items'] = {}
            
            # Convert to snake_case ID and store with zero price
            item_id = fan['custom_optional_items[]'].lower().replace(' ', '_')
            structured_fan['specifications']['custom_optional_items'][item_id] = 0
        
        structured_fans.append(structured_fan)
    
    # Print the structured data for debugging
    print("Structured fan data:")
    for i, fan in enumerate(structured_fans):
        print(f"\nFan {i+1}:")
        if 'custom_optional_items[]' in fan['specifications']:
            print(f"custom_optional_items[]: {fan['specifications']['custom_optional_items[]']}")
        if 'custom_optional_items' in fan['specifications']:
            print("custom_optional_items dictionary:")
            for key, value in fan['specifications']['custom_optional_items'].items():
                print(f"  {key}: {value}")
    
    # Create a test request context to build URLs
    with app.test_request_context('/'):
        # Render the template with the structured fan data
        try:
            html = render_template('templates/summary.html', 
                                  fans=structured_fans, 
                                  enquiry_number='TEST123', 
                                  customer_name='Test Customer', 
                                  sales_engineer='Test Engineer',
                                  total_fans=1,
                                  total_weight=165,
                                  total_fabrication_cost=34650,
                                  total_bought_out_cost=22000,
                                  total_cost=56650)
            
            # Check if AMCA Type C Spark Proof Construction appears in the rendered HTML
            if 'AMCA Type C Spark Proof Construction' in html:
                print("\nSUCCESS: AMCA Type C Spark Proof Construction is visible in the summary")
            else:
                print("\nFAILURE: AMCA Type C Spark Proof Construction is NOT visible in the summary")
                # Print relevant sections of the HTML for debugging
                print("\nDebug - Looking for custom optional items section:")
                custom_items_start = html.find('Custom Optional Items')
                if custom_items_start > -1:
                    section_end = html.find('</div>', custom_items_start)
                    print(html[custom_items_start:section_end+6])
                else:
                    print("Could not find 'Custom Optional Items' section in HTML")
                
                # Save the HTML to a file for manual inspection
                with open('debug_summary.html', 'w') as f:
                    f.write(html)
                print("Full HTML saved to debug_summary.html for manual inspection")
                
        except Exception as e:
            print(f"Exception during template rendering: {str(e)}")

if __name__ == "__main__":
    test_with_raw_data() 