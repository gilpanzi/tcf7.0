import re

def count_placeholders_and_params():
    """Count VALUES placeholders and parameters in the data structure."""
    
    # The VALUES placeholders from the SQL statement
    placeholders = "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
    placeholder_count = placeholders.count('?')
    print(f"Number of placeholders in VALUES clause: {placeholder_count}")
    
    # Parameters in the tuple (count the number of parameters)
    params = [
        "enquiry_number",
        "i",  # fan_number
        "specs.get('fan_model', '')",
        "specs.get('size', '')",
        "specs.get('class', '')",
        "specs.get('arrangement', '')",
        "specs.get('vendor', '')",
        "specs.get('material', '')",
        "accessories",
        "weights.get('bare_fan_weight', 0)",
        "weights.get('accessory_weight', 0)",
        "weights.get('total_weight', 0)",
        "weights.get('fabrication_weight', 0)",
        "weights.get('bought_out_weight', 0)",
        "costs.get('fabrication_cost', 0)",
        "motor_cost",
        "vibration_isolators_cost",
        "drive_pack_cost",
        "bearing_cost",
        "optional_items_cost",
        "flex_connectors_cost",
        "costs.get('bought_out_cost', 0)",
        "costs.get('total_cost', 0)",
        "costs.get('fabrication_selling_price', 0)",
        "costs.get('bought_out_selling_price', 0)",
        "costs.get('total_selling_price', 0)",
        "costs.get('total_job_margin', 0)",
        "specs.get('vibration_isolators', '')",
        "specs.get('drive_pack_kw', 0)",
        "custom_accessories",
        "optional_items",
        "custom_option_items",
        "motor.get('kw', 0)",
        "motor.get('brand', '')",
        "motor.get('pole', 0)",
        "motor.get('efficiency', '')",
        "motor.get('discount_rate', 0)",
        "specs.get('bearing_brand', '')",
        "specs.get('shaft_diameter', 0)",
        "specs.get('no_of_isolators', fan.get('no_of_isolators', 0))",
        "fan.get('fabrication_margin', costs.get('fabrication_margin', 0))",
        "fan.get('bought_out_margin', costs.get('bought_out_margin', 0))"
    ]
    param_count = len(params)
    print(f"Number of parameters supplied: {param_count}")
    
    # Check if there's a mismatch
    if placeholder_count != param_count:
        print(f"MISMATCH: {placeholder_count} placeholders vs {param_count} parameters")
    else:
        print("MATCH: Number of placeholders matches number of parameters")

if __name__ == "__main__":
    count_placeholders_and_params() 