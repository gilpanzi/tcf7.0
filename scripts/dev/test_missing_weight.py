
import requests
import json

def test_missing_weight_error():
    url = 'http://localhost:5000/calculate_fan'
    
    payload = {
        "Fan_Model": "BC-SW",
        "Fan_Size": "122",
        "Class": "1",
        "Arrangement": "4",
        "vendor": "TCF Factory",
        "material": "ms",
        "accessories": ["NonExistentAccessory"], 
        "shaft_diameter": 50,
        "no_of_isolators": 4,
        "customAccessories": {},
        "optional_items": {}
    }

    try:
        response = requests.post(url, json=payload)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 400 and "Missing weight" in response.text:
            print("SUCCESS: Correctly received 400 error for missing weight.")
        else:
            print("FAILURE: Did not receive expected 400 error.")

    except Exception as e:
        print(f"EXCEPTION: {e}")

if __name__ == "__main__":
    test_missing_weight_error()
