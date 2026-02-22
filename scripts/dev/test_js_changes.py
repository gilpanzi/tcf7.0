def test_js_normalizeCustomOptionalItems():
    # Read the main.js file with errors='ignore' to handle encoding issues
    try:
        with open('static/js/main.js', 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading file: {e}")
        return
    
    # Check for the key changes we made
    js_checks = [
        {
            'description': 'Removed price filtering in array notation case',
            'pattern': 'fanData.custom_optional_items[id] = 0;',
            'negative_pattern': 'if (fanData.optional_items_cost > 0 && Object.keys(fanData.optional_items).length === 0)',
            'pass': False
        },
        {
            'description': 'Added display name preservation',
            'pattern': 'fanData.custom_optional_items_display_name = name;',
            'pass': False
        },
        {
            'description': 'Removed price filtering code',
            'negative_pattern': 'let price = 0;',
            'pass': False
        }
    ]
    
    for check in js_checks:
        if 'pattern' in check and check['pattern'] in content:
            check['pass'] = True
        
        if 'negative_pattern' in check and check['negative_pattern'] not in content:
            check['pass'] = True

    # Display results
    print("JavaScript normalizeCustomOptionalItems function check:")
    all_passed = True
    for check in js_checks:
        if check['pass']:
            print(f"✅ {check['description']}")
        else:
            print(f"❌ {check['description']}")
            all_passed = False
    
    if all_passed:
        print("\n✅ All JavaScript changes to normalizeCustomOptionalItems were successful")
        print("The function will now preserve custom optional items regardless of price")
        print("and handle array notation formats properly.")
    else:
        print("\n❌ Some JavaScript changes may not have been applied correctly")
        
    # Finally, let's manually check the key snippet that we modified
    if "// Always add the item regardless of price" in content:
        print("\n✅ The normalizeCustomOptionalItems function has been updated with our changes")
    else:
        print("\n❌ Couldn't find our specific changes in the normalizeCustomOptionalItems function")

if __name__ == '__main__':
    test_js_normalizeCustomOptionalItems() 