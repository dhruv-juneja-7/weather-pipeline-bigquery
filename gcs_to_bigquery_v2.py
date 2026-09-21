from google.cloud import storage, bigquery
import pandas as pd
import json 
from datetime import datetime
import logging


logging_file = f"pipeline_run_{datetime.now().strftime('%Y-%m-%d')}"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler(logging_file),
              logging.StreamHandler()] # to print in the console as well.
)

logger = logging.getLogger(__name__)

credentials_path = "D:/GCP/the-looker-ecommerce-dataset-4ec229e127e8.json"

storage_client = storage.Client.from_service_account_json(credentials_path)

bigquery_client = bigquery.Client.from_service_account_json(credentials_path)

bucket = storage_client.bucket('daily-weather-data')
blobs = bucket.list_blobs()

table_id = "the-looker-ecommerce-dataset.open_meteo.daily_weather"
staging_table_id = "the-looker-ecommerce-dataset.open_meteo.daily_weather_staging"

schema = [
    bigquery.SchemaField("latitude", "FLOAT64"),
    bigquery.SchemaField("longitude", "FLOAT64"),
    bigquery.SchemaField("generationtime_ms", "FLOAT64"),
    bigquery.SchemaField("utc_offset_seconds", "FLOAT64"),
    bigquery.SchemaField("timezone", "string"),
    bigquery.SchemaField("timezone_abbreviation", "STRING"),
    bigquery.SchemaField("time_units", "STRING"),
    bigquery.SchemaField("sunrise_units", "STRING"),
    bigquery.SchemaField("sunset_units", "STRING"),
    bigquery.SchemaField("uv_index_max_units", "STRING"),
    bigquery.SchemaField("temperature_2m_max_units", "STRING"),
    bigquery.SchemaField("temperature_2m_min_units", "STRING"),
    bigquery.SchemaField("precipitation_sum_units", "STRING"),
    bigquery.SchemaField("precipitation_hours_units", "STRING"),
    bigquery.SchemaField("time", "DATE"),
    bigquery.SchemaField("sunrise", "DATETIME"),
    bigquery.SchemaField("sunset", "DATETIME"),
    bigquery.SchemaField("uv_index_max", "FLOAT64"),
    bigquery.SchemaField("temperature_2m_max", "FLOAT64"),
    bigquery.SchemaField("temperature_2m_min", "FLOAT64"),
    bigquery.SchemaField("precipitation_sum", "FLOAT64"),
    bigquery.SchemaField("precipitation_hours", "FLOAT64"),
    bigquery.SchemaField("weather_date", "DATETIME"),
    bigquery.SchemaField("loaded_date", "DATETIME")
]

EXPECTED_COLUMNS = [c.name for c in schema]


try:
    table = bigquery.Table(table_id, schema)
    table = bigquery_client.create_table(table, exists_ok=True)
    logger.info('daily_weather_table created successfully.')
except Exception as e:
    logger.error(f"Error occurred while creating the table {e}")

complete_df = pd.DataFrame()

for blob in blobs:

    public_url = blob.public_url
    uri_val = public_url.replace("https://storage.googleapis.com/", "gs://")
    raw_data = blob.download_as_text()
    weather_data = json.loads(raw_data)
    weather_date = uri_val.split('/')[-1].split('T')[0]
    current_date = datetime.today().isoformat()

    if weather_date != current_date.split('T')[0]:
        continue

    daily_df = pd.DataFrame(weather_data['daily'])
    daily_df['latitude'] = weather_data['latitude']
    daily_df['longitude'] = weather_data['longitude']
    daily_df['generationtime_ms'] = weather_data['generationtime_ms']
    daily_df['utc_offset_seconds'] = weather_data['utc_offset_seconds']
    daily_df['timezone'] = weather_data['timezone']
    daily_df['timezone_abbreviation'] = weather_data['timezone_abbreviation']
    daily_df['time_units'] = weather_data['daily_units'].get('time')
    daily_df['sunrise_units'] = weather_data['daily_units'].get('sunrise')
    daily_df['sunset_units'] = weather_data['daily_units'].get('sunset')
    daily_df['uv_index_max_units'] = weather_data['daily_units'].get('uv_index_max')
    daily_df['temperature_2m_max_units'] = weather_data['daily_units'].get('temperature_2m_max')
    daily_df['temperature_2m_min_units'] = weather_data['daily_units'].get('temperature_2m_min')
    daily_df['precipitation_hours_units'] = weather_data['daily_units'].get('precipitation_hours')
    daily_df['precipitation_sum_units'] = weather_data['daily_units'].get('precipitation_sum')
    daily_df['weather_date'] = pd.to_datetime(weather_date)
    daily_df['loaded_date'] = pd.to_datetime(current_date)

    daily_df_reindexed = daily_df.reindex(columns=EXPECTED_COLUMNS)

    # print(daily_df_reindexed.tail())

    complete_df = pd.concat([complete_df,daily_df_reindexed], axis=0)
    # Configure optional load job settings
    # job_config = bigquery.LoadJobConfig(
    #     write_disposition="WRITE_APPEND",  # Overwrite table if it exists
    # )

    # try:
    #     job = bigquery_client.load_table_from_dataframe(daily_df,table_id, job_config=job_config)
    #     job.result()
    #     print(f"Loaded {job.output_rows} rows into {table_id}.")
    # except Exception as e:
    #     print(f"An error occurred while loading the rows: {e}")
    # print(f"{weather_data}")
    # print(f"{public_url}")

# print(complete_df.tail(10))

complete_df_dedup = complete_df.sort_values(by=['loaded_date']).drop_duplicates(subset=['time'], keep="last")

try:
    staging_table = bigquery.Table(table_ref=staging_table_id, schema=schema)
    staging_table = bigquery_client.create_table(staging_table, exists_ok=True)
    logger.info(f'{staging_table_id} created successfully.')
except Exception as e:
    logger.error(f'An error occurred while creating table {staging_table_id} as {e}.')

job_config = bigquery.LoadJobConfig(
        schema=schema,
        write_disposition="WRITE_TRUNCATE",  # Overwrite table if it exists
    )

try:
    job = bigquery_client.load_table_from_dataframe(complete_df_dedup,staging_table_id,job_config=job_config)
    job.result()
    logger.info(f"Loaded {job.output_rows} rows into {staging_table_id}.")
except Exception as e:
    logger.error('An error occurred while loading rows: {e}')

update_query = (',').join([f'T.{c} = S.{c}' for c in EXPECTED_COLUMNS ])
insert_columns = (',').join(c for c in EXPECTED_COLUMNS)
insert_values = (',').join(f'S.{c}' for c in EXPECTED_COLUMNS)

sql = f"""
    MERGE {table_id} as T
    USING {staging_table_id} S
    ON S.time = T.time
    WHEN MATCHED THEN
        UPDATE SET {update_query}
    WHEN NOT MATCHED THEN
        INSERT ({insert_columns})
        VALUES ({insert_values})
"""

merge_job = bigquery_client.query(sql)
merge_job.result()

logger.info(f'Merge job successful: {merge_job.num_dml_affected_rows} affecting in {table_id}.')