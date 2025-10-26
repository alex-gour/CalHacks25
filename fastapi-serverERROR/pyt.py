import requests
import json

headers = {
    "Authorization": "Bearer 6fb99f75cac0f56141be2fc9763d9c61411fe34526224a4b6eb7b5dbb429b6e3",
    "Content-Type": "application/json",
}

data = json.dumps({
    "input": [{"keyword":"Nestle Pure Life water bottle, plastic."}],
})

response = requests.post(
    "https://api.brightdata.com/datasets/v3/scrape?dataset_id=gd_l7q7dkf244hwjntr0&notify=false&include_errors=true&type=discover_new&discover_by=keyword",
    headers=headers,
    data=data
)

print(response.json())