from google.cloud import bigquery

credentials_path = "D:/GCP/the-looker-ecommerce-dataset-4ec229e127e8.json"

client = bigquery.Client.from_service_account_json(credentials_path)

QUERY =  """
    SELECT name, number 
    FROM `bigquery-public-data.usa_names.usa_1910_current` 
    WHERE state = 'NY' 
    LIMIT 5
"""

results = client.query_and_wait(QUERY)

for row in results:
    print(f"{row.name} : {row.number}")

# wearther API = 
# https://api.open-meteo.com/v1/forecast?latitude=20.5937&longitude=78.9629&daily=sunrise,sunset,uv_index_max,temperature_2m_max,temperature_2m_min,precipitation_sum,precipitation_hours&timezone=GMT