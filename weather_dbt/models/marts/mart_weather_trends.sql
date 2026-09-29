select weather_time,
round(avg(temperature_2m_max) over(order by weather_time ROWS BETWEEN 6 PRECEDING AND CURRENT ROW),2) as rolling_7_day_avg 
from {{ref('stg_daily_weather') }}
order by weather_time