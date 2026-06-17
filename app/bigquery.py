from google.cloud import bigquery
from app.config import BQ_PROJECT_ID, BQ_DATASET, BQ_BILLING_PROJECT, MAX_RESULT_ROWS


def _get_client() -> bigquery.Client:
    project = BQ_BILLING_PROJECT or None
    return bigquery.Client(project=project)


def get_schema() -> list[dict]:
    client = _get_client()
    dataset_ref = bigquery.DatasetReference(BQ_PROJECT_ID, BQ_DATASET)
    tables = list(client.list_tables(dataset_ref))

    result = []
    for table_item in tables:
        table = client.get_table(table_item)
        result.append({
            "table": table_item.table_id,
            "columns": [
                {
                    "name": field.name,
                    "type": field.field_type,
                    "description": field.description or "",
                }
                for field in table.schema
            ],
        })
    return result


def dry_run(sql: str) -> tuple[int, str | None]:
    """Returns (bytes_processed, error_message)."""
    client = _get_client()
    job_config = bigquery.QueryJobConfig(dry_run=True, use_query_cache=False)
    try:
        job = client.query(sql, job_config=job_config)
        return job.total_bytes_processed, None
    except Exception as exc:
        return 0, str(exc)


def execute_query(sql: str) -> tuple[list[dict], str | None]:
    """Returns (rows, error_message)."""
    client = _get_client()
    try:
        rows = list(client.query(sql).result())
        return [dict(row) for row in rows[:MAX_RESULT_ROWS]], None
    except Exception as exc:
        return [], str(exc)
