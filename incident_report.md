# Problem Statement -

The pipeline was rigid and assumed that the structure of the json data will always be the same. It ignored the real-world case where there are discrepancies in the source data and the data pipelines should validate the incoming data before loading it. It should detect any schema changes and alert the users.

To check it, I removed one of the keys (precipitation_hours) from the raw json weather file that was being inserted in the dataset table in bigquery. This was a deliberate fault injection, not a production incident.

# Effect -

The complete process of inserting the data in bigquery was shut down. The staging table in the bigquery was created but it was empty. There was no change in the daily_weather table in the bigquery, so the MERGE design kept the final table clean.

# Detection -

It was detected manually during a dry run of the code.
I saw the errors in the std out console.
No alert or automated check fired. I only found it because I was watching.

# Root Cause -

After looking at the console errors, I came to know that it happened as i was directly trying to get the value of removed key without using .get() dict function in Python which returns None if the key is not present.
The deeper cause is that the pipeline had no schema validation on the source data. It trusted the structure of the API response without checking it.
Second thing is because the .get() is now returning None - the rolling 7 day average in the mart table is incorrect when a null row is present.

# Resolution

1. Used .get dict function to avoid hard fail in future. Side effect: a missing key now becomes a silent None instead of a loud failure, so bad data can flow downstream unnoticed.
2. Used logging module to log errors for failure of the insertion script.
3. Created a dbt staging model (stg_daily_weather) on top of the loaded table, which runs before the mart model computes the final aggregation. It checks whether the Primary key in the table which is the time in this case is not null and unique.

# Prevention

1. If there any schema changes like missing columns then the current code could not prevent this. The dbt tests only check the date key, so a missing precipitation_hours would still pass them.
2. Planned: check the expected keys in the loader before inserting, and fail loudly (or log and quarantine the record) when keys are missing.
3. Planned: add not_null and range tests on the value columns in dbt, plus a freshness check, so bad or missing values are caught before the 7-day rolling average runs.

# Future Steps

1. Schedule this pipeline to run daily using Airflow.
2. Whenever any error occurs, sending alerts to the pipeline owners.
