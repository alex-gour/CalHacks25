//@input Component.Camera camera
//@input SceneObject screenSpace
//@input string apiUrl = "http://127.0.0.1:8000/api"
//@ui {"widget":"label", "label":"AI Assistant Lens - Homeless Support"}

// Global variables
var textComp;
var isProcessing = false;
var currentSessionId = null;

// Initialize the lens
function initialize() {
    // Get the Screen space object
    var screenTransform = script.screenSpace.getComponent("ScreenTransform");
    
    // Create a text component
    textComp = script.screenSpace.createComponent("Text");
    
    // Configure text
    textComp.text = "AI Assistant Ready\nTap to get help";
    textComp.fontSize = 48;
    textComp.fontColor = new vec4(1, 1, 1, 1); // White color
    textComp.alignment = TextAlignment.Center;
    
    // Make sure it's visible
    script.screenSpace.enabled = true;
    
    // Add tap event
    var touchComponent = script.screenSpace.createComponent("Component.TouchComponent");
    touchComponent.onTouch.add(function(eventData) {
        if (!isProcessing) {
            handleUserRequest();
        }
    });
    
    print("AI Assistant Lens initialized successfully!");
}

// Handle user request
function handleUserRequest() {
    if (isProcessing) return;
    
    isProcessing = true;
    textComp.text = "Processing your request...\nPlease wait";
    
    // Get user's location (simulated for demo)
    var userLat = 34.0522; // Los Angeles latitude
    var userLon = -118.2437; // Los Angeles longitude
    
    // Create a test request
    var requestData = {
        user_prompt: "I need help finding shelter and medical care",
        latitude: userLat,
        longitude: userLon
    };
    
    // Make API call
    makeAPIRequest(requestData);
}

// Make API request to backend
function makeAPIRequest(data) {
    var request = new XMLHttpRequest();
    request.open("POST", script.apiUrl + "/orchestrate", true);
    request.setRequestHeader("Content-Type", "application/json");
    
    request.onreadystatechange = function() {
        if (request.readyState === 4) {
            isProcessing = false;
            
            if (request.status === 200) {
                try {
                    var response = JSON.parse(request.responseText);
                    displayResponse(response);
                } catch (e) {
                    textComp.text = "Error parsing response\nPlease try again";
                    print("JSON parse error: " + e);
                }
            } else {
                textComp.text = "Connection error\nPlease check your internet";
                print("API request failed: " + request.status);
            }
        }
    };
    
    request.send(JSON.stringify(data));
}

// Display response to user
function displayResponse(response) {
    if (response.error) {
        textComp.text = "Error: " + response.error;
        return;
    }
    
    var responseText = "";
    
    if (response.response) {
        responseText = response.response;
    } else if (response.nearest_resource) {
        var resource = response.nearest_resource;
        if (resource.error) {
            responseText = "No shelters found nearby\nTry medical facilities";
        } else {
            responseText = "Nearest Shelter:\n" + resource.name + "\n" + resource.address;
        }
    } else if (response.facilities && response.facilities.length > 0) {
        var facility = response.facilities[0];
        responseText = "Nearest Medical:\n" + facility.name + "\n" + facility.type + "\nDistance: " + Math.round(facility.distance * 10) / 10 + " miles";
    } else if (response.nearestRestroom) {
        var restroom = response.nearestRestroom;
        responseText = "Nearest Restroom:\n" + restroom.facility + "\nDistance: " + Math.round(restroom.distance_miles * 10) / 10 + " miles";
    } else {
        responseText = "Help is on the way!\nCheck your location services";
    }
    
    // Limit text length for display
    if (responseText.length > 120) {
        responseText = responseText.substring(0, 117) + "...";
    }
    
    textComp.text = responseText;
    
    // Reset after 8 seconds
    script.createEvent("DelayedCallbackEvent").bind(function() {
        textComp.text = "AI Assistant Ready\nTap to get help";
    });
    script.createEvent("DelayedCallbackEvent").reset(8.0);
}

// Initialize when script starts
initialize();
