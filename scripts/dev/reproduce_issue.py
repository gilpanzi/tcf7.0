
import json
import logging
import time
from app import create_app

# Set up logging
logging.basicConfig(level=logging.ERROR)

app = create_app()
app.config['TESTING'] = True
app.config['WTF_CSRF_ENABLED'] = False

with app.test_client() as client:
    # 1. Login
    login_resp = client.post('/login', data={'username': 'abdul', 'password': 'tcfsales'}, follow_redirects=True)
    if b'Invalid username or password' in login_resp.data:
        print("Login failed")
        exit(1)
    
    # Unique enquiry number to avoid conflicts
    test_id = f"VERIFY_{int(time.time())}"
    
    # 2. Create Project
    project_payload = {
        "enquiry_number": test_id,
        "customer_name": "Verification Test",
        "total_fans": 1,
        "sales_engineer": "abdul"
    }
    resp = client.post('/api/projects', json=project_payload)
    if resp.status_code != 200:
        print(f"Failed to create project: {resp.status_code}, {resp.data}")
        exit(1)
    print(f"Project {test_id} created.")

    # 3. Test Standard MS Material
    payload_ms = {
        "specifications": {
            "Fan Model": "BC-SW",
            "Fan Size": "270",
            "Class": "1",
            "Arrangement": "1",
            "vendor": "TCF Factory",
            "material": "ms",
            "vibration_isolators": "not_required",
            "fabrication_margin": 25,
            "bought_out_margin": 25,
            "bearing_brand": "SKF"
        },
        "motor": {"brand": "", "kw": "", "pole": "", "efficiency": "", "discount": 0}
    }
    
    print("\n--- Testing Standard MS Material ---")
    resp = client.put(f'/api/projects/{test_id}/fans/1', json=payload_ms)
    print(f"Status: {resp.status_code}")
    
    if resp.status_code == 200:
        data = resp.get_json()
        cost = data.get('costs', {}).get('fabrication_cost')
        print(f"SUCCESS: Fabrication Cost = {cost}")
    else:
        print(f"FAILED: {resp.data}")

    # 4. Test Mixed Material
    payload_mixed = payload_ms.copy()
    payload_mixed['specifications']['material'] = 'mixed'
    payload_mixed['specifications']['ms_percentage'] = 50
    
    print("\n--- Testing Mixed Material (50%) ---")
    resp = client.put(f'/api/projects/{test_id}/fans/1', json=payload_mixed)
    print(f"Status: {resp.status_code}")
    
    if resp.status_code == 200:
        data = resp.get_json()
        cost = data.get('costs', {}).get('fabrication_cost')
        print(f"SUCCESS: Fabrication Cost = {cost}")
    else:
        print(f"FAILED: {resp.data}")
