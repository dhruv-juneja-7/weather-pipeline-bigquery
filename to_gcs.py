from google.cloud import storage
import json
import requests
from datetime import datetime

credentials_path = "D:/GCP/the-looker-ecommerce-dataset-4ec229e127e8.json"

storage_client = storage.Client.from_service_account_json(credentials_path)

# result = requests.get("https://api.open-meteo.com/v1/forecast?latitude=20.5937&longitude=78.9629&daily=sunrise,sunset,uv_index_max,temperature_2m_max,temperature_2m_min,precipitation_sum,precipitation_hours&timezone=GMT", timeout=30)
result = requests.get("https://api.open-meteo.com/v1/forecast?latitude=20.5937&longitude=78.9629&daily=sunrise,sunset,uv_index_max,temperature_2m_max,temperature_2m_min,precipitation_sum,precipitation_hours&timezone=GMT", timeout=30)

result.raise_for_status()
# print(result.json())

data = json.dumps(result.json())

today = datetime.today().strftime("%Y-%m-%dT%H-%M-%S")

bucket_name = "daily-weather-data"
destination_blob_name = "raw/" + today + ".json"

try:
    bucket = storage_client.bucket(bucket_name)

    blob = bucket.blob(destination_blob_name)

    blob.upload_from_string(data)

    print(f"Success! daily weather data for {today} uploaded to {destination_blob_name} in bucket {bucket_name}.")

except Exception as e:
    print(f"An error occurred: {e}")

# print(destination_blob_name)
# print(storage_client)