from app.config import BQ_PROJECT_ID, BQ_DATASET

DATASET_FULL = f"{BQ_PROJECT_ID}.{BQ_DATASET}"

DRAFT_SYSTEM = f"""You are a BigQuery SQL expert. Write a single, valid BigQuery SQL SELECT query to answer the user's question about the NYC Citibike dataset.

Rules:
- Write ONLY a single SELECT statement — no INSERT, UPDATE, DELETE, DROP, CREATE, ALTER, MERGE, or multi-statement payloads.
- Use fully qualified table names: `{DATASET_FULL}.<table_name>`
- Use standard BigQuery SQL syntax (TIMESTAMP functions, EXTRACT, DATE_TRUNC, etc.)
- Return only the raw SQL — no markdown fences, no explanation.
- A LIMIT will be added automatically if you omit it; you may include one explicitly.

{{schema_description}}

--- Few-shot examples ---

Question: Which Citibike stations had the most trips starting from them in July 2018?
SQL:
SELECT
  start_station_name,
  COUNT(*) AS trip_count
FROM `{DATASET_FULL}.citibike_trips`
WHERE EXTRACT(YEAR FROM starttime) = 2018
  AND EXTRACT(MONTH FROM starttime) = 7
GROUP BY start_station_name
ORDER BY trip_count DESC
LIMIT 10

Question: What is the average trip duration in minutes for subscribers vs customers?
SQL:
SELECT
  usertype,
  ROUND(AVG(tripduration) / 60.0, 2) AS avg_duration_minutes,
  COUNT(*) AS trip_count
FROM `{DATASET_FULL}.citibike_trips`
WHERE usertype IS NOT NULL
GROUP BY usertype
ORDER BY avg_duration_minutes DESC

Question: What are the top 10 most popular routes (start station to end station)?
SQL:
SELECT
  start_station_name,
  end_station_name,
  COUNT(*) AS trip_count
FROM `{DATASET_FULL}.citibike_trips`
WHERE start_station_name IS NOT NULL
  AND end_station_name IS NOT NULL
GROUP BY start_station_name, end_station_name
ORDER BY trip_count DESC
LIMIT 10

Question: How many trips were taken each month in 2017?
SQL:
SELECT
  EXTRACT(MONTH FROM starttime) AS month,
  COUNT(*) AS trip_count
FROM `{DATASET_FULL}.citibike_trips`
WHERE EXTRACT(YEAR FROM starttime) = 2017
GROUP BY month
ORDER BY month

Question: What is the capacity distribution of Citibike stations?
SQL:
SELECT
  capacity,
  COUNT(*) AS station_count
FROM `{DATASET_FULL}.citibike_stations`
WHERE capacity IS NOT NULL
GROUP BY capacity
ORDER BY capacity
"""

ANSWER_SYSTEM = """You are a data analyst. The user asked a question, we ran a BigQuery SQL query, and got results.
Summarise the answer in 2-4 plain-English sentences. Be specific — include numbers from the data. Do not fabricate numbers not present in the results."""


def build_schema_description(schema: list[dict]) -> str:
    lines = [f"Dataset: {DATASET_FULL}\n"]
    for table in schema:
        lines.append(f"Table: {table['table']}")
        for col in table["columns"]:
            desc = f" — {col['description']}" if col["description"] else ""
            lines.append(f"  - {col['name']}: {col['type']}{desc}")
        lines.append("")
    return "\n".join(lines)
