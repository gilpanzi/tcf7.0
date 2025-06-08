from flask import Flask, render_template
import os
import json
import re
import traceback

app = Flask(__name__, template_folder=os.path.dirname(os.path.abspath(__file__)))

def test_fixed_summary_template():
    """
    Test script to verify our fixed summary_fixed.html template works correctly.
    """
    print("Testing with summary_fixed.html template...")
    
    # Test data with all different formats of custom optional items
    test_cases = [
        {
            "description": "1. Array notation at root level",
            "fan_data": {
                "custom_optional_items[]": "AMCA Type C Spark Proof Construction", 
                "specifications": {}
            }
        },
        {
            "description": "2. Array notation in specifications",
            "fan_data": {
                "specifications": {
                    "custom_optional_items[]": "AMCA Type C Spark Proof Construction"
                }
            }
        },
        {
            "description": "3. Dictionary format at root level",
            "fan_data": {
                "custom_optional_items": {
                    "amca_type_c_spark_proof_construction": 0
                },
                "specifications": {}
            }
        },
        {
            "description": "4. Dictionary format in specifications",
            "fan_data": {
                "specifications": {
                    "custom_optional_items": {
                        "amca_type_c_spark_proof_construction": 0
                    }
                }
            }
        },
        {
            "description": "5. Legacy format (custom_option_items)",
            "fan_data": {
                "specifications": {
                    "custom_option_items": {
                        "amca_type_c_spark_proof_construction": 0
                    }
                }
            }
        },
        {
            "description": "6. Display name format",
            "fan_data": {
                "custom_optional_items_display_name": "AMCA Type C Spark Proof Construction",
                "specifications": {}
            }
        },
        {
            "description": "7. JSON string format",
            "fan_data": {
                "custom_optional_items": json.dumps({
                    "amca_type_c_spark_proof_construction": 0
                }),
                "specifications": {}
            }
        }
    ]
    
    # Add necessary structure to each test case for the main template
    for test in test_cases:
        fan = test["fan_data"]
        # Add minimal required structure
        fan["motor"] = {
            "brand": "Test Motor",
            "kw": "1.5",
            "pole": "4",
            "efficiency": "IE3"
        }
        fan["weights"] = {
            "total_weight": 250,
            "bare_fan_weight": 200,
            "accessory_weight": 50
        }
        fan["costs"] = {
            "total_cost": 50000,
            "fabrication_cost": 30000,
            "bought_out_cost": 20000,
            "motor_cost": 10000,
            "vibration_isolators_cost": 5000,
            "bearing_cost": 2000,
            "drive_pack_cost": 0
        }
                
        # Add minimal specifications
        if "fan_model" not in fan.get("specifications", {}):
            if "specifications" not in fan:
                fan["specifications"] = {}
            fan["specifications"]["fan_model"] = "BC-SW"
            fan["specifications"]["size"] = "222"
            fan["specifications"]["class"] = "1"
            fan["specifications"]["arrangement"] = "4"
            fan["specifications"]["vibration_isolators"] = "dunlop"
            fan["specifications"]["bearing_brand"] = "SKF"
            # Add optional items for standard items section to render
            fan["specifications"]["optional_items"] = {
                "prices": {
                    "flex_connectors": 5000,
                    "silencer": 3000
                }
            }
    
    # Process test data similar to routes.py
    processed_fans = []
    for i, test in enumerate(test_cases):
        fan = test["fan_data"]
        
        # Handle custom_optional_items[] format - Make sure it exists in specifications
        if 'custom_optional_items[]' in fan and not fan['specifications'].get('custom_optional_items[]'):
            print(f"Test {i+1}: Processing custom_optional_items[] at root level")
            fan['specifications']['custom_optional_items[]'] = fan['custom_optional_items[]']
            
            # Also make sure it's in the dictionary format for backward compatibility
            if 'custom_optional_items' not in fan['specifications']:
                fan['specifications']['custom_optional_items'] = {}
            
            # Convert the array notation to a dictionary entry with zero price
            item_name = fan['custom_optional_items[]']
            item_id = item_name.lower().replace(' ', '_')
            fan['specifications']['custom_optional_items'][item_id] = 0
        
        # Copy display_name if it exists
        if 'custom_optional_items_display_name' in fan and 'custom_optional_items_display_name' not in fan['specifications']:
            print(f"Test {i+1}: Processing custom_optional_items_display_name")
            fan['specifications']['custom_optional_items_display_name'] = fan['custom_optional_items_display_name']
        
        # Handle potential string-encoded JSON
        if 'custom_optional_items' in fan and isinstance(fan['custom_optional_items'], str):
            try:
                # Try to parse it as JSON
                print(f"Test {i+1}: Parsing string JSON custom_optional_items")
                parsed_items = json.loads(fan['custom_optional_items'])
                fan['custom_optional_items'] = parsed_items
                fan['specifications']['custom_optional_items'] = parsed_items
            except:
                print(f"Test {i+1}: Failed to parse string custom_optional_items")
        
        # Handle custom optional items for consistency
        if 'specifications' in fan:
            # Ensure both naming formats exist for backward compatibility
            if 'custom_option_items' in fan['specifications'] and 'custom_optional_items' not in fan['specifications']:
                print(f"Test {i+1}: Converting custom_option_items to custom_optional_items")
                fan['specifications']['custom_optional_items'] = fan['specifications']['custom_option_items']
            elif 'custom_optional_items' in fan['specifications'] and 'custom_option_items' not in fan['specifications']:
                print(f"Test {i+1}: Converting custom_optional_items to custom_option_items")
                fan['specifications']['custom_option_items'] = fan['specifications']['custom_optional_items']
        
        # Copy custom_optional_items from root to specifications if needed
        if 'custom_optional_items' in fan and fan['custom_optional_items'] and isinstance(fan['custom_optional_items'], dict):
            if 'custom_optional_items' not in fan['specifications'] or not fan['specifications']['custom_optional_items']:
                print(f"Test {i+1}: Copying custom_optional_items from root to specifications")
                fan['specifications']['custom_optional_items'] = fan['custom_optional_items']
        
        processed_fans.append(fan)
    
    # Debug: Print processed fan data
    print("\nProcessed fan data for summary template:")
    for i, fan in enumerate(processed_fans):
        print(f"\nFan {i+1}:")
        if 'custom_optional_items[]' in fan:
            print(f"Root custom_optional_items[]: {fan['custom_optional_items[]']}")
        if 'custom_optional_items' in fan and isinstance(fan['custom_optional_items'], dict):
            print("Root custom_optional_items:", fan['custom_optional_items'])
        if 'custom_optional_items_display_name' in fan:
            print(f"Root custom_optional_items_display_name: {fan['custom_optional_items_display_name']}")
        
        print("Specifications level:")
        if 'custom_optional_items[]' in fan['specifications']:
            print(f"  custom_optional_items[]: {fan['specifications']['custom_optional_items[]']}")
        if 'custom_optional_items' in fan['specifications'] and isinstance(fan['specifications']['custom_optional_items'], dict):
            print(f"  custom_optional_items: {fan['specifications']['custom_optional_items']}")
        if 'custom_option_items' in fan['specifications'] and isinstance(fan['specifications']['custom_option_items'], dict):
            print(f"  custom_option_items: {fan['specifications']['custom_option_items']}")
        if 'custom_optional_items_display_name' in fan['specifications']:
            print(f"  custom_optional_items_display_name: {fan['specifications']['custom_optional_items_display_name']}")
    
    # Now render the template with our processed fans
    with app.app_context():
        try:
            context = {
                'fans': processed_fans,
                'enquiry_number': 'TEST123',
                'customer_name': 'Test Customer',
                'sales_engineer': 'Test Engineer',
                'total_fans': len(processed_fans),
                'total_weight': 1750,  # 7 fans x 250kg
                'total_fabrication_cost': 210000,  # 7 fans x 30,000
                'total_bought_out_cost': 140000,  # 7 fans x 20,000
                'total_cost': 350000   # 7 fans x 50,000
            }
            
            # Use our fixed template
            print("\nRendering template...")
            html = render_template('templates/summary_fixed.html', **context)
            print("Template rendered successfully.")
            
            # Check for the key phrase
            target_text = "AMCA Type C Spark Proof Construction"
            count = html.lower().count(target_text.lower())
            
            print(f"\nFound {count} occurrences of '{target_text}' in rendered template")
            print(f"Expected at least {len(test_cases)} occurrences")
            
            # Save the output for inspection
            with open('fixed_summary_test_output.html', 'w') as f:
                f.write(html)
            print("Full HTML saved to fixed_summary_test_output.html for inspection")
            
            if count >= len(test_cases):
                print("\n✅ SUCCESS: All formats of custom optional items are displaying correctly!")
                return True
            else:
                print("\n❌ FAILURE: Some formats are not displaying correctly")
                
                # Extract each fan card and check for our text
                fan_cards = re.findall(r'<div class="fan-card".*?</div>\s*</div>', html, re.DOTALL)
                print(f"\nFound {len(fan_cards)} fan cards in the output")
                
                for i, card in enumerate(fan_cards):
                    if target_text.lower() in card.lower():
                        print(f"Fan {i+1}: Custom optional item found in output")
                    else:
                        print(f"Fan {i+1}: Custom optional item NOT found in output")
                
                return False
                
        except Exception as e:
            print(f"Exception rendering template: {str(e)}")
            print("Stack trace:")
            traceback.print_exc()
            return False

if __name__ == "__main__":
    success = test_fixed_summary_template()
    
    if success:
        print("\nFixed summary template works correctly!")
        print("Custom optional items are now displaying properly in all formats.")
        print("\nNext step: Replace the original summary.html with summary_fixed.html")
    else:
        print("\nFurther investigation required to fix the summary template.")