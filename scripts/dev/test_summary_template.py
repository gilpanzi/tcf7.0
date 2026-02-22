from flask import Flask, render_template
import os

app = Flask(__name__, template_folder=os.path.dirname(os.path.abspath(__file__)))

# Different test cases for fan data with custom optional items
test_cases = [
    # Test case 1: Regular format with zero price
    {
        'specifications': {
            'fan_model': 'BC-SW',
            'size': '222',
            'class': '1',
            'arrangement': '4',
            'vibration_isolators': 'not_required',
            'custom_optional_items': {
                'amca_type_c_spark_proof_construction': 0
            }
        },
        'motor': {},
        'costs': {},
        'weights': {}
    },
    
    # Test case 2: Using array notation format
    {
        'specifications': {
            'fan_model': 'BC-SW',
            'size': '222', 
            'class': '1',
            'arrangement': '4',
            'vibration_isolators': 'not_required',
            'custom_optional_items[]': 'AMCA Type C Spark Proof Construction'
        },
        'motor': {},
        'costs': {},
        'weights': {}
    },
    
    # Test case 3: Direct on fan object rather than specifications
    {
        'specifications': {
            'fan_model': 'BC-SW',
            'size': '222',
            'class': '1',
            'arrangement': '4',
            'vibration_isolators': 'not_required'
        },
        'custom_optional_items[]': 'AMCA Type C Spark Proof Construction',
        'motor': {},
        'costs': {},
        'weights': {}
    },
    
    # Test case 4: Using display_name
    {
        'specifications': {
            'fan_model': 'BC-SW',
            'size': '222',
            'class': '1',
            'arrangement': '4',
            'vibration_isolators': 'not_required'
        },
        'custom_optional_items_display_name': 'AMCA Type C Spark Proof Construction',
        'motor': {},
        'costs': {},
        'weights': {}
    }
]

def test_template():
    # Minimal project data for rendering
    project_data = {
        'enquiry_number': 'TEST123',
        'customer_name': 'Test Customer',
        'sales_engineer': 'Test Engineer',
        'total_fans': len(test_cases),
        'total_weight': 0,
        'total_fabrication_cost': 0,
        'total_bought_out_cost': 0,
        'total_cost': 0,
    }
    
    # Render template with our test data
    with app.app_context():
        try:
            html = render_template('templates/summary.html', fans=test_cases, **project_data)
            
            # Check if our custom optional item text appears in the rendered HTML
            item_text = 'AMCA Type C Spark Proof Construction'
            if item_text.lower() in html.lower():
                print(f"✅ SUCCESS: '{item_text}' appears in the rendered template")
                
                # Count occurrences (should appear for each test case)
                count = html.lower().count(item_text.lower())
                print(f"Found {count} occurrences out of {len(test_cases)} test cases")
                
                if count == len(test_cases):
                    print("✅ All test cases successfully displayed the custom optional item")
                else:
                    print(f"❌ Only {count} out of {len(test_cases)} test cases displayed the item")
            else:
                print(f"❌ ERROR: '{item_text}' does not appear in the rendered template")
        except Exception as e:
            print(f"Error rendering template: {e}")
            print("\nInstead, let's try to manually verify our changes:")
            
            # Verify our summary.html changes for displaying custom optional items
            with open('templates/summary.html', 'r') as f:
                content = f.read()
                
            # Check if we removed price filtering for custom optional items
            if "{% for item_id, price in fan.specifications.custom_optional_items.items() %}" in content and "{% if price and price|float > 0 %}" not in content:
                print("✅ Price filtering has been removed from custom optional items")
            else:
                print("❌ Price filtering is still present for custom optional items")
                
            # Check if we're handling the array notation format
            if "{% if fan.specifications.custom_optional_items is string or" in content and "fan.get('custom_optional_items[]')" in content:
                print("✅ Array notation format handling is in place")
            else:
                print("❌ Array notation format handling is missing")
                
            # Check display name handling 
            if "fan.custom_optional_items_display_name is defined" in content:
                print("✅ Display name handling is in place")
            else:
                print("❌ Display name handling is missing")

if __name__ == "__main__":
    test_template() 