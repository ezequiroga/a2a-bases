#!/usr/bin/env python3
"""
Test script for the flights findings HTTP endpoint.
This script demonstrates how to send flight data to the chat agent.
"""
import requests
import json
from datetime import datetime

CHAT_AGENT_URL = "http://localhost:9990"
FLIGHTS_ENDPOINT = "/api/flights-findings"

def test_flight_findings():
    """Test sending flight findings to the chat agent."""
    
    flight_data = {
        "airport_code": "MAD",
        "airport_name": "Madrid-Barajas Airport",
        "date": "2024-02-15",
        "flights": [
            {
                "airline": "Iberia",
                "flight_number": "IB6250",
                "departure_time": "08:30",
                "arrival_time": "11:45",
                "destination": "London Heathrow",
                "destination_code": "LHR",
                "price": "€245",
                "availability": "Available"
            },
            {
                "airline": "Vueling",
                "flight_number": "VY1234",
                "departure_time": "14:20",
                "arrival_time": "17:35",
                "destination": "Paris Charles de Gaulle",
                "destination_code": "CDG",
                "price": "€189",
                "availability": "Available"
            },
            {
                "airline": "Air Europa",
                "flight_number": "UX1056",
                "departure_time": "19:15",
                "arrival_time": "21:30",
                "destination": "Rome Fiumicino",
                "destination_code": "FCO",
                "price": "€298",
                "availability": "Available"
            }
        ],
        "source": "flight_search_system",
        "metadata": {
            "search_timestamp": datetime.now().isoformat(),
            "search_criteria": "departure_date=2024-02-15",
            "total_results": 3
        }
    }
    
    try:
        print("🛫 Testing flight findings endpoint...")
        print(f"📡 Sending data to: {CHAT_AGENT_URL}{FLIGHTS_ENDPOINT}")
        print(f"📊 Flight data: {len(flight_data['flights'])} flights for {flight_data['airport_name']}")
        
        response = requests.post(
            f"{CHAT_AGENT_URL}{FLIGHTS_ENDPOINT}",
            json=flight_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Success!")
            print(f"📝 Response: {result}")
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"📝 Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection error: Make sure the chat agent is running on localhost:9990")
    except Exception as e:
        print(f"❌ Error: {str(e)}")


def test_status():
    """Test the status endpoint."""
    
    try:
        print("\n📊 Testing status endpoint...")
        print(f"📡 Requesting: {CHAT_AGENT_URL}/api/status")
        
        response = requests.get(f"{CHAT_AGENT_URL}/api/status")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Success!")
            print(f"📝 Status: {json.dumps(result, indent=2)}")
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"📝 Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection error: Make sure the chat agent is running on localhost:9990")
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    print("🧪 Testing Chat Agent HTTP Endpoints")
    print("=" * 50)
    
    test_status()
    test_flight_findings()
    
    print("\n✅ Test completed!")
    print("💡 Check the chat agent console to see how the messages appear.") 