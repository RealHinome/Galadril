from __future__ import annotations

from typing import Any
import duckdb


def run_duckdb_aggregation(
    rows: list[dict[str, Any]], query: str
) -> list[dict[str, Any]]:
    if not rows:
        return rows

    con = duckdb.connect(database=":memory:")
    con.register("input", rows)
    result = con.execute(query).fetchdf()
    return result.to_dict(orient="records")
