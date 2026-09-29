-- staging file for saving the intermediate results

SELECT
    CAST(latitude AS FLOAT64) AS latitude,
    CAST(longitude AS FLOAT64) AS longitude,
    timezone,
    CAST(time AS DATE) AS weather_time,
    CAST(sunrise AS DATETIME) AS sunrise,
    CAST(sunset AS DATETIME) AS sunset,
    CAST(uv_index_max AS FLOAT64) AS uv_index_max,
    CAST(temperature_2m_max AS FLOAT64) AS temperature_2m_max,
    CAST(temperature_2m_min AS FLOAT64) AS temperature_2m_min,
    CAST(precipitation_sum AS FLOAT64) AS precipitation_sum,
    CAST(precipitation_hours AS FLOAT64) AS precipitation_hours,
    CAST(weather_date AS DATE) AS weather_date,
    CAST(loaded_date AS DATETIME) AS loaded_date
FROM {{ source('open_meteo', 'daily_weather') }}

