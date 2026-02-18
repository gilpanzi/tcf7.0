import requests
import json
import sys

def test_missing_weight_behavior():
    url = 'http://localhost:5000/calculate_fan'
    
    payload = {
        "Fan_Model": "BC-SW",
        "Fan_Size": "122",
        "Class": "1",
        "Arrangement": "4",
        "vendor": "TCF Factory",
        "vendor": "TCF Factory",
        "material": "mixed",
        "ms_percentage": 50,
        "accessories": [], 
        "shaft_diameter": 50,
        "no_of_isolators": 4,
        "customAccessories": {},
        "optional_items": {}
    }

    try:
        response = requests.post(url, json=payload)
        
        if response.status_code == 200:
            data = response.json()
            weights = data.get('weights', {})
            shaft = weights.get('shaft_diameter')
            isolators = weights.get('no_of_isolators')
            vendor_rate = data.get('vendor_rate')
            
            print(f"STATUS_200_OK")
            print(f"SHAFT_VAL:{shaft}")
            print(f"ISOLATORS_VAL:{isolators}")
            print(f"VENDOR_RATE:{vendor_rate}")
            
        else:
            print(f"STATUS_{response.status_code}")
            print(f"ERROR_MSG:{response.text[:200]}")

    except Exception as e:
        print(f"EXCEPTION:{e}")

if __name__ == "__main__":
    test_missing_weight_behavior()
