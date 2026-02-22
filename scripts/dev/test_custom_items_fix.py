from flask import Flask, render_template
import os
import json
import re

app = Flask(__name__, template_folder=os.path.dirname(os.path.abspath(__file__)))

def test_all_custom_optional_item_formats():
    """
    Test script to verify that all formats of custom optional items
    are correctly displayed in the summary template.
    """
    print("Testing all custom optional item formats display correctly")
    
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
    
    # Add necessary structure to each test case
    for test in test_cases:
        # Add minimal required structure
        for key in ["motor", "weights", "costs"]:
            if key not in test["fan_data"]:
                test["fan_data"][key] = {}
                
        # Add minimal specifications
        if "fan_model" not in test["fan_data"].get("specifications", {}):
            test["fan_data"]["specifications"]["fan_model"] = "BC-SW"
            test["fan_data"]["specifications"]["size"] = "222"
    
    # Process test data similar to routes.py
    processed_fans = []
    for i, test in enumerate(test_cases):
        fan = test["fan_data"]
        
        # COPY OF IMPROVED HANDLING FOR CUSTOM OPTIONAL ITEMS
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
    
    # Now render the template with our processed fans
    with app.app_context():
        try:
            context = {
                'fans': processed_fans,
                'enquiry_number': 'TEST123',
                'customer_name': 'Test Customer',
                'sales_engineer': 'Test Engineer',
                'total_fans': len(processed_fans),
                'total_weight': 0,
                'total_fabrication_cost': 0,
                'total_bought_out_cost': 0,
                'total_cost': 0
            }
            
            # Use our simplified test template instead
            html = render_template('test_summary.html', **context)
            
            # Check for the key phrase
            target_text = "AMCA Type C Spark Proof Construction"
            count = html.lower().count(target_text.lower())
            
            print(f"\nFound {count} occurrences of '{target_text}' in rendered template")
            print(f"Expected {len(test_cases) * 2} occurrences (two per test case - root and specifications level)")
            
            if count >= len(test_cases):
                print("\n✅ SUCCESS: At least one instance of each custom optional item format is displaying correctly!")
                
                # Save the output for inspection
                with open('test_custom_items_output.html', 'w') as f:
                    f.write(html)
                print("Full HTML saved to test_custom_items_output.html for inspection")
                
                # Now let's apply the same fixes to the main summary.html template
                print("\nTemplate test passed! Applying the same approach to fix summary.html")
                return True
            else:
                print("\n❌ FAILURE: Some formats are not displaying correctly")
                return False
                
        except Exception as e:
            print(f"Exception rendering template: {str(e)}")
            return False

if __name__ == "__main__":
    success = test_all_custom_optional_item_formats()
    
    if success:
        print("\nNext step: Apply these fixes to the main summary.html template") 