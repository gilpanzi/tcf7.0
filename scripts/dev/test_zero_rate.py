
import requests
import json

def test_zero_vendor_rate():
    url = 'http://localhost:5000/calculate_fan'
    
    # Payload with vendor_rate set to 0.00
    payload = {
        "Fan_Model": "BC-SW",
        "Fan_Size": "122",
        "Class": "1",
        "Arrangement": "4",
        "vendor": "TCF Factory",
        "material": "ms",
        "vendor_rate": "0.00", 
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
            vendor_rate = data.get('vendor_rate')
            print(f"Vendor Rate Returned: {vendor_rate}")
            
            if vendor_rate and float(vendor_rate) > 0:
                print("SUCCESS: Zero vendor_rate was ignored, valid rate used.")
            else:
                print(f"FAILURE: Vendor rate is still {vendor_rate}.")
        else:
            print(f"HTTP ERROR: {response.status_code}")
            print(response.text)

    except Exception as e:
        print(f"EXCEPTION: {e}")

if __name__ == "__main__":
    test_zero_vendor_rate()
