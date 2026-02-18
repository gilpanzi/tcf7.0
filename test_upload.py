import requests
import os

url = 'http://127.0.0.1:5000/db-admin/upload-motor-prices'
file_path = 'All Motor New Price Book1 (Without H.P).xlsx'

if not os.path.exists(file_path):
    print(f"File not found: {file_path}")
    exit(1)

# Basic Auth credentials from db_admin.py defaults
auth = ('admin', 'tcfadmin2024')

try:
    with open(file_path, 'rb') as f:
        files = {'file': f}
        response = requests.post(url, files=files, auth=auth)
        
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        print("Upload successful!")
        if "Success" in response.text:
            print("Server reported success.")
        else:
            print("Response content:", response.text[:200])
    else:
        print("Upload failed.")
        print(response.text)
except Exception as e:
    print(f"Error: {e}")
    print("Make sure the app is running (python app.py)")
