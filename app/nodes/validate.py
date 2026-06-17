import sqlglot
from sqlglot import expressions as exp

from app.state import AgentState
from app.config import DEFAULT_LIMIT, BYTE_CAP
from app.bigquery import dry_run

_BLOCKED = (
    exp.Insert,
    exp.Update,
    exp.Delete,
    exp.Drop,
    exp.Create,
    exp.Alter,
    exp.Merge,
    exp.Command,
    exp.Transaction,
)


def _parse_and_guard(sql: str) -> tuple[str, str | None]:
    """Parse SQL, enforce read-only, inject LIMIT. Returns (cleaned_sql, error)."""
    try:
        statements = sqlglot.parse(
            sql.strip(), dialect="bigquery", error_level=sqlglot.ErrorLevel.RAISE
        )
    except sqlglot.errors.ParseError as exc:
        return sql, f"SQL parse error: {exc}"

    statements = [s for s in statements if s is not None]

    if not statements:
        return sql, "Empty SQL statement."

    if len(statements) > 1:
        return sql, "Multi-statement queries are not allowed."

    stmt = statements[0]

    if not isinstance(stmt, exp.Select):
        return sql, f"Only SELECT queries are allowed; got {type(stmt).__name__}."

    # Walk AST to catch blocked expressions anywhere in the tree
    for node in stmt.walk():
        if isinstance(node, _BLOCKED):
            return sql, f"Blocked SQL operation: {type(node).__name__}."

    # Inject LIMIT when absent
    if stmt.args.get("limit") is None:
        stmt = stmt.copy()
        stmt.set(
            "limit",
            exp.Limit(this=exp.Literal.number(DEFAULT_LIMIT)),
        )

    return stmt.sql(dialect="bigquery"), None


def validate_node(state: AgentState) -> dict:
    cleaned_sql, parse_error = _parse_and_guard(state["sql"])
    if parse_error:
        return {"error": parse_error, "sql": state["sql"]}

    bytes_processed, dry_run_error = dry_run(cleaned_sql)
    if dry_run_error:
        return {"error": f"BigQuery dry-run failed: {dry_run_error}", "sql": cleaned_sql}

    if bytes_processed > BYTE_CAP:
        gb = bytes_processed / 1e9
        cap_gb = BYTE_CAP / 1e9
        return {
            "error": (
                f"Query would scan {gb:.1f} GB, exceeding the {cap_gb:.0f} GB cap. "
                "Rewrite the query to be more selective (add a WHERE clause or reduce scope)."
            ),
            "sql": cleaned_sql,
        }

    return {"sql": cleaned_sql, "error": None}
