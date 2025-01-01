import requests

def get_realtime_location():
    try:
        # Use a public IP geolocation API
        response = requests.get("https://ipinfo.io/json")
        response.raise_for_status()

        # Parse the JSON response
        data = response.json()
        location_info = {
            "IP": data.get("ip"),
            "City": data.get("city"),
            "Region": data.get("region"),
            "Country": data.get("country"),
            "Location": data.get("loc"),  # Latitude, Longitude
            "Organization": data.get("org"),
            "Postal": data.get("postal"),
        }

        return location_info

    except requests.exceptions.RequestException as e:
        print(f"Error fetching location: {e}")
        return None

if __name__ == "__main__":
    location = get_realtime_location()
    if location:
        print("Real-time Location Information:")
        for key, value in location.items():
            print(f"{key}: {value}")
    else:
        print("Could not retrieve location information.")
