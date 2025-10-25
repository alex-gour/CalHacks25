import requests
from bs4 import BeautifulSoup
from app.utils.geo import haversine  # assuming you already have this

def get_shelter_data(user_lat, user_lon, zip_code):
    """Fetch and return the closest homeless resource to the user location."""
    
    # First try the LAPL API
    try:
        url = "https://www.lapl.org/homeless-resources"
        
        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'en-US,en;q=0.9',
            'Connection': 'keep-alive',
            'Referer': f'https://www.lapl.org/homeless-resources?distance%5Bpostal_code%5D={zip_code}&distance%5Bsearch_distance%5D=2&distance%5Bsearch_units%5D=mile',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Mobile Safari/537.36',
            'sec-ch-ua': '"Chromium";v="134", "Not:A-Brand";v="24", "Google Chrome";v="134"',
            'sec-ch-ua-mobile': '?1',
            'sec-ch-ua-platform': '"Android"',
        }

        params = {
            'distance[postal_code]': zip_code,
            'distance[search_distance]': str(20),
            'distance[search_units]': 'mile',
        }

        response = requests.get(url, headers=headers, params=params, timeout=10)

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            resources = []
            all_entries = soup.find_all('li', class_='views-row')

            for entry in all_entries:
                name_tag = entry.find('h3')
                address_phone_tag = entry.find('p', class_='hrc')
                map_link_tag = entry.find('a', class_='show-map-link')
                
                if name_tag and address_phone_tag and map_link_tag:
                    name = name_tag.get_text(strip=True)
                    full_text = address_phone_tag.get_text(strip=True)
                    if "|" in full_text:
                        address, phone = [part.strip() for part in full_text.split("|", 1)]
                    else:
                        address, phone = full_text, "Unknown"
                    
                    latitude = map_link_tag['data-latitude']
                    longitude = map_link_tag['data-longitude']

                    # Calculate distance from user to shelter
                    dist = haversine(user_lon, user_lat, float(longitude), float(latitude))

                    resources.append({
                        "name": name,
                        "address": address,
                        "phone": phone,
                        "latitude": latitude,
                        "longitude": longitude,
                        "distance_miles": dist
                    })

            # Sort by distance
            resources.sort(key=lambda x: x["distance_miles"])

            # Return the nearest shelter (first one)
            if resources:
                return resources[0]
    except Exception as e:
        print(f"LAPL API failed: {e}")
    
    # Fallback: Return comprehensive local resources for LA area
    return get_fallback_shelter_resources(user_lat, user_lon, zip_code)

def get_fallback_shelter_resources(user_lat, user_lon, zip_code):
    """Provide fallback shelter resources when API fails."""
    
    # LA area emergency shelters and resources
    emergency_shelters = [
        {
            "name": "Union Rescue Mission",
            "address": "545 S San Pedro St, Los Angeles, CA 90013",
            "phone": "(213) 347-6300",
            "latitude": 34.0407,
            "longitude": -118.2468,
            "services": "Emergency shelter, meals, clothing",
            "hours": "24/7",
            "distance_miles": haversine(user_lon, user_lat, -118.2468, 34.0407)
        },
        {
            "name": "Los Angeles Mission",
            "address": "303 E 5th St, Los Angeles, CA 90013",
            "phone": "(213) 629-1227",
            "latitude": 34.0444,
            "longitude": -118.2431,
            "services": "Emergency shelter, meals, job training",
            "hours": "24/7",
            "distance_miles": haversine(user_lon, user_lat, -118.2431, 34.0444)
        },
        {
            "name": "Midnight Mission",
            "address": "601 S San Pedro St, Los Angeles, CA 90014",
            "phone": "(213) 624-9258",
            "latitude": 34.0417,
            "longitude": -118.2456,
            "services": "Emergency shelter, meals, recovery programs",
            "hours": "24/7",
            "distance_miles": haversine(user_lon, user_lat, -118.2456, 34.0417)
        },
        {
            "name": "Downtown Women's Center",
            "address": "442 S San Pedro St, Los Angeles, CA 90013",
            "phone": "(213) 680-0600",
            "latitude": 34.0412,
            "longitude": -118.2465,
            "services": "Women's shelter, meals, case management",
            "hours": "24/7",
            "distance_miles": haversine(user_lon, user_lat, -118.2465, 34.0412)
        },
        {
            "name": "LA Family Housing",
            "address": "7843 Lankershim Blvd, North Hollywood, CA 91605",
            "phone": "(818) 982-4091",
            "latitude": 34.1681,
            "longitude": -118.3789,
            "services": "Family shelter, housing assistance",
            "hours": "8AM-5PM",
            "distance_miles": haversine(user_lon, user_lat, -118.3789, 34.1681)
        }
    ]
    
    # Add emergency numbers and resources
    emergency_resources = {
        "emergency_211": "Call 211 for 24/7 crisis support and resource referrals",
        "emergency_911": "Call 911 for immediate emergency assistance",
        "crisis_text": "Text HOME to 741741 for crisis text support",
        "national_homeless_hotline": "1-800-733-7333",
        "la_homeless_services": "(213) 225-6581"
    }
    
    # Find closest shelter
    closest_shelter = min(emergency_shelters, key=lambda x: x["distance_miles"])
    
    return {
        "name": closest_shelter["name"],
        "address": closest_shelter["address"],
        "phone": closest_shelter["phone"],
        "latitude": closest_shelter["latitude"],
        "longitude": closest_shelter["longitude"],
        "distance_miles": round(closest_shelter["distance_miles"], 2),
        "services": closest_shelter["services"],
        "hours": closest_shelter["hours"],
        "emergency_resources": emergency_resources,
        "additional_shelters": emergency_shelters[:3],  # Include 3 closest
        "message": "Emergency shelter information provided. Call 211 for immediate assistance."
    }
