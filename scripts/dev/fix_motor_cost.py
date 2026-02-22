import re

def fix_motor_cost_section():
    try:
        # Read routes.py content
        with open('routes.py', 'r', encoding='utf-8') as file:
            content = file.read()
            
        # Find and replace the malformatted motor_cost section
        problem_pattern = r"fan\['costs'\]\['motor_cost'\] = float\(\s*fan\.get\('motor_cost',\s*fan\['costs'\]\.get\('motor_cost',\s*fan\.get\('discounted_motor_price',\s*fan\['costs'\]\.get\('discounted_motor_price', 0\)\s*\)\s*\)\s*\)\s*or 0\s*\)\s*# --- END PATCH ---"
        replacement = """fan['costs']['motor_cost'] = float(
                    fan.get('motor_cost',
                        fan['costs'].get('motor_cost',
                            fan.get('discounted_motor_price',
                                fan['costs'].get('discounted_motor_price', 0)
                            )
                        )
                    ) or 0
                )
                # --- END PATCH ---"""
        
        # Apply the replacement
        new_content = re.sub(problem_pattern, replacement, content)
        
        # Write the fixed content back
        with open('routes.py', 'w', encoding='utf-8') as file:
            file.write(new_content)
            
        print("Successfully fixed motor_cost section in routes.py")
        return True
    except Exception as e:
        print(f"Error fixing motor_cost section: {str(e)}")
        return False

if __name__ == "__main__":
    fix_motor_cost_section() 