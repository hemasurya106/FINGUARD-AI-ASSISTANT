import requests
import json

BASE_URL = "http://localhost:8000/api"

def test_alerts():
    print("Testing Price Alerts API...")
    
    # 1. Create Alert
    print("\n1. Setting Alert...")
    payload = {
        "product_url": "https://www.amazon.in/test-product",
        "target_price": 50000.0,
        "email": "test@example.com"
    }
    try:
        response = requests.post(f"{BASE_URL}/set-alert", json=payload)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            alert_id = data.get("alert_id")
            
            # 2. Get Alerts
            print(f"\n2. Getting Alerts for {payload['email']}...")
            response = requests.get(f"{BASE_URL}/alerts/{payload['email']}")
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.text}")
            
            # 3. Delete Alert
            if alert_id:
                print(f"\n3. Deleting Alert ID {alert_id}...")
                response = requests.delete(f"{BASE_URL}/alerts/{alert_id}")
                print(f"Status Code: {response.status_code}")
                print(f"Response: {response.text}")
                
    except Exception as e:
        print(f"Test failed: {e}")

if __name__ == "__main__":
    test_alerts()
