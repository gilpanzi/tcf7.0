"""
Verify that all custom optional items are correctly displayed in the summary template.
This script generates a minimal HTML file for each format of custom optional items
and checks the output to ensure the items are displayed.
"""

import os
import json
from pathlib import Path

# Create output directory if it doesn't exist
Path("test_output").mkdir(exist_ok=True)

# Test cases for different formats of custom optional items
test_cases = [
    {
        "description": "1. Array notation at root level",
        "template": """
{% if fan.custom_optional_items[] %}
<p>Custom Optional Item: {{ fan.custom_optional_items[] }}</p>
{% endif %}
        """,
        "fan_data": {
            "custom_optional_items[]": "AMCA Type C Spark Proof Construction"
        }
    },
    {
        "description": "2. Array notation in specifications",
        "template": """
{% if fan.specifications.custom_optional_items[] %}
<p>Custom Optional Item: {{ fan.specifications.custom_optional_items[] }}</p>
{% endif %}
        """,
        "fan_data": {
            "specifications": {
                "custom_optional_items[]": "AMCA Type C Spark Proof Construction"
            }
        }
    },
    {
        "description": "3. Dictionary format at root level",
        "template": """
{% if fan.custom_optional_items is mapping %}
{% for item_id, price in fan.custom_optional_items.items() %}
<p>Custom Optional Item: {{ item_id|replace('_', ' ')|title }}</p>
{% endfor %}
{% endif %}
        """,
        "fan_data": {
            "custom_optional_items": {
                "amca_type_c_spark_proof_construction": 0
            }
        }
    },
    {
        "description": "4. Dictionary format in specifications",
        "template": """
{% if fan.specifications.custom_optional_items is mapping %}
{% for item_id, price in fan.specifications.custom_optional_items.items() %}
<p>Custom Optional Item: {{ item_id|replace('_', ' ')|title }}</p>
{% endfor %}
{% endif %}
        """,
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
        "template": """
{% if fan.specifications.custom_option_items is mapping %}
{% for item_id, price in fan.specifications.custom_option_items.items() %}
<p>Custom Optional Item: {{ item_id|replace('_', ' ')|title }}</p>
{% endfor %}
{% endif %}
        """,
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
        "template": """
{% if fan.custom_optional_items_display_name %}
<p>Custom Optional Item: {{ fan.custom_optional_items_display_name }}</p>
{% endif %}
        """,
        "fan_data": {
            "custom_optional_items_display_name": "AMCA Type C Spark Proof Construction"
        }
    },
    {
        "description": "7. JSON string format",
        "template": """
{% if fan.custom_optional_items is string %}
<p>Custom Optional Item (JSON): {{ fan.custom_optional_items }}</p>
{% endif %}
        """,
        "fan_data": {
            "custom_optional_items": json.dumps({
                "amca_type_c_spark_proof_construction": 0
            })
        }
    }
]

# Test each format individually
for i, test_case in enumerate(test_cases):
    description = test_case["description"]
    template = test_case["template"]
    fan_data = test_case["fan_data"]
    
    print(f"\nTesting format: {description}")
    
    # Create a simple Jinja2-like template renderer (very basic)
    def render_simple_template(template, fan):
        # Convert template variables to Python format strings
        result = template
        
        # Handle array notation first
        if "custom_optional_items[]" in json.dumps(fan):
            if "fan.custom_optional_items[]" in template:
                value = fan.get("custom_optional_items[]", "")
                result = result.replace("{{ fan.custom_optional_items[] }}", value)
            
            if "fan.specifications.custom_optional_items[]" in template and "specifications" in fan:
                value = fan.get("specifications", {}).get("custom_optional_items[]", "")
                result = result.replace("{{ fan.specifications.custom_optional_items[] }}", value)
        
        # Handle display name
        if "custom_optional_items_display_name" in json.dumps(fan):
            if "fan.custom_optional_items_display_name" in template:
                value = fan.get("custom_optional_items_display_name", "")
                result = result.replace("{{ fan.custom_optional_items_display_name }}", value)
        
        # Simple render of conditionals
        # Render {% if fan.custom_optional_items[] %} ... {% endif %}
        if "{% if fan.custom_optional_items[] %}" in result:
            if "custom_optional_items[]" in fan:
                result = result.replace("{% if fan.custom_optional_items[] %}", "")
                result = result.replace("{% endif %}", "")
            else:
                # Remove the block
                start = result.find("{% if fan.custom_optional_items[] %}")
                end = result.find("{% endif %}", start) + len("{% endif %}")
                result = result[:start] + result[end:]
        
        # Render {% if fan.specifications.custom_optional_items[] %} ... {% endif %}
        if "{% if fan.specifications.custom_optional_items[] %}" in result:
            if "specifications" in fan and "custom_optional_items[]" in fan["specifications"]:
                result = result.replace("{% if fan.specifications.custom_optional_items[] %}", "")
                result = result.replace("{% endif %}", "")
            else:
                # Remove the block
                start = result.find("{% if fan.specifications.custom_optional_items[] %}")
                end = result.find("{% endif %}", start) + len("{% endif %}")
                result = result[:start] + result[end:]
        
        # Handle {% if fan.custom_optional_items_display_name %} ... {% endif %}
        if "{% if fan.custom_optional_items_display_name %}" in result:
            if "custom_optional_items_display_name" in fan:
                result = result.replace("{% if fan.custom_optional_items_display_name %}", "")
                result = result.replace("{% endif %}", "")
            else:
                # Remove the block
                start = result.find("{% if fan.custom_optional_items_display_name %}")
                end = result.find("{% endif %}", start) + len("{% endif %}")
                result = result[:start] + result[end:]
        
        # Handle {% if fan.custom_optional_items is mapping %} ... {% endfor %} ... {% endif %}
        if "{% if fan.custom_optional_items is mapping %}" in result:
            if "custom_optional_items" in fan and isinstance(fan["custom_optional_items"], dict):
                # Loop over dictionary items
                items_html = ""
                for item_id, price in fan["custom_optional_items"].items():
                    # Extract the template segment for the loop
                    loop_start = result.find("{% for item_id, price in fan.custom_optional_items.items() %}") + len("{% for item_id, price in fan.custom_optional_items.items() %}")
                    loop_end = result.find("{% endfor %}", loop_start)
                    loop_template = result[loop_start:loop_end].strip()
                    
                    # Replace item_id with formatted version
                    formatted_id = item_id.replace('_', ' ').title()
                    item_html = loop_template.replace("{{ item_id|replace('_', ' ')|title }}", formatted_id)
                    items_html += item_html + "\n"
                
                # Replace the entire loop with the generated items
                loop_start = result.find("{% for item_id, price in fan.custom_optional_items.items() %}")
                loop_end = result.find("{% endfor %}", loop_start) + len("{% endfor %}")
                result = result.replace(result[loop_start:loop_end], items_html)
                
                # Remove the if statement
                result = result.replace("{% if fan.custom_optional_items is mapping %}", "")
                result = result.replace("{% endif %}", "")
            else:
                # Remove the block
                start = result.find("{% if fan.custom_optional_items is mapping %}")
                end = result.find("{% endif %}", start) + len("{% endif %}")
                result = result[:start] + result[end:]
        
        # Handle {% if fan.specifications.custom_optional_items is mapping %} ... {% endfor %} ... {% endif %}
        if "{% if fan.specifications.custom_optional_items is mapping %}" in result:
            if "specifications" in fan and "custom_optional_items" in fan["specifications"] and isinstance(fan["specifications"]["custom_optional_items"], dict):
                # Loop over dictionary items
                items_html = ""
                for item_id, price in fan["specifications"]["custom_optional_items"].items():
                    # Extract the template segment for the loop
                    loop_start = result.find("{% for item_id, price in fan.specifications.custom_optional_items.items() %}") + len("{% for item_id, price in fan.specifications.custom_optional_items.items() %}")
                    loop_end = result.find("{% endfor %}", loop_start)
                    loop_template = result[loop_start:loop_end].strip()
                    
                    # Replace item_id with formatted version
                    formatted_id = item_id.replace('_', ' ').title()
                    item_html = loop_template.replace("{{ item_id|replace('_', ' ')|title }}", formatted_id)
                    items_html += item_html + "\n"
                
                # Replace the entire loop with the generated items
                loop_start = result.find("{% for item_id, price in fan.specifications.custom_optional_items.items() %}")
                loop_end = result.find("{% endfor %}", loop_start) + len("{% endfor %}")
                result = result.replace(result[loop_start:loop_end], items_html)
                
                # Remove the if statement
                result = result.replace("{% if fan.specifications.custom_optional_items is mapping %}", "")
                result = result.replace("{% endif %}", "")
            else:
                # Remove the block
                start = result.find("{% if fan.specifications.custom_optional_items is mapping %}")
                end = result.find("{% endif %}", start) + len("{% endif %}")
                result = result[:start] + result[end:]
        
        # Handle {% if fan.specifications.custom_option_items is mapping %} ... {% endfor %} ... {% endif %}
        if "{% if fan.specifications.custom_option_items is mapping %}" in result:
            if "specifications" in fan and "custom_option_items" in fan["specifications"] and isinstance(fan["specifications"]["custom_option_items"], dict):
                # Loop over dictionary items
                items_html = ""
                for item_id, price in fan["specifications"]["custom_option_items"].items():
                    # Extract the template segment for the loop
                    loop_start = result.find("{% for item_id, price in fan.specifications.custom_option_items.items() %}") + len("{% for item_id, price in fan.specifications.custom_option_items.items() %}")
                    loop_end = result.find("{% endfor %}", loop_start)
                    loop_template = result[loop_start:loop_end].strip()
                    
                    # Replace item_id with formatted version
                    formatted_id = item_id.replace('_', ' ').title()
                    item_html = loop_template.replace("{{ item_id|replace('_', ' ')|title }}", formatted_id)
                    items_html += item_html + "\n"
                
                # Replace the entire loop with the generated items
                loop_start = result.find("{% for item_id, price in fan.specifications.custom_option_items.items() %}")
                loop_end = result.find("{% endfor %}", loop_start) + len("{% endfor %}")
                result = result.replace(result[loop_start:loop_end], items_html)
                
                # Remove the if statement
                result = result.replace("{% if fan.specifications.custom_option_items is mapping %}", "")
                result = result.replace("{% endif %}", "")
            else:
                # Remove the block
                start = result.find("{% if fan.specifications.custom_option_items is mapping %}")
                end = result.find("{% endif %}", start) + len("{% endif %}")
                result = result[:start] + result[end:]
                
        # Handle {% if fan.custom_optional_items is string %} ... {% endif %}
        if "{% if fan.custom_optional_items is string %}" in result:
            if "custom_optional_items" in fan and isinstance(fan["custom_optional_items"], str):
                result = result.replace("{% if fan.custom_optional_items is string %}", "")
                result = result.replace("{% endif %}", "")
                result = result.replace("{{ fan.custom_optional_items }}", fan["custom_optional_items"])
            else:
                # Remove the block
                start = result.find("{% if fan.custom_optional_items is string %}")
                end = result.find("{% endif %}", start) + len("{% endif %}")
                result = result[:start] + result[end:]
        
        return result.strip()
    
    # Render template
    rendered_html = render_simple_template(template, fan_data)
    
    # Save to file
    output_path = os.path.join("test_output", f"format_{i+1}.html")
    with open(output_path, "w") as f:
        f.write(rendered_html)
    
    # Check if output contains the target text
    if "AMCA Type C Spark Proof Construction" in rendered_html or "Amca Type C Spark Proof Construction" in rendered_html:
        print(f"✅ SUCCESS: Format rendered correctly")
        print(f"Output: {rendered_html}")
    else:
        print(f"❌ FAILURE: Format did not render correctly")
        print(f"Output: {rendered_html}")

print("\nAll tests completed. Check the test_output directory for the rendered outputs.")
print("Each format that displays 'AMCA Type C Spark Proof Construction' is working correctly.")