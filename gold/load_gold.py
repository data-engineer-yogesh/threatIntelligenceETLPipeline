import sqlite3
from datetime import datetime, timezone
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATABASE_PATH = PROJECT_ROOT / "data" / "threat_intelligence.db"

ENRICHED_TABLE = "silver_urlhaus_domains_enriched"

GOLD_TABLE = "gold_urlhaus_domains"


def read_enriched_data(connection):

    cursor = connection.execute(
        f"""
        SELECT domain, ipv4
        FROM {ENRICHED_TABLE}
        """
    )

    return cursor.fetchall()


def create_gold_table(connection):

    connection.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {GOLD_TABLE} (
            domain TEXT PRIMARY KEY,
            resolved_ip TEXT,
            last_updated TEXT
        )
        """
    )

    connection.commit()


def upsert_gold_data(rows, connection):

    last_updated = datetime.now(
        timezone.utc
    ).isoformat()

    records = [
        (
            domain,
            ipv4,
            last_updated
        )
        for domain, ipv4 in rows
    ]

    connection.executemany(
        f"""
        INSERT INTO {GOLD_TABLE} (
            domain,
            resolved_ip,
            last_updated
        )
        VALUES (?, ?, ?)

        ON CONFLICT(domain)
        DO UPDATE SET
            resolved_ip = excluded.resolved_ip,
            last_updated = excluded.last_updated
        """,
        records
    )

    connection.commit()

    print(
        f"Gold records upserted: {len(records)}"
    )


def main():

    print(
        "URLHaus Gold Load Started"
    )

    connection = sqlite3.connect(
        DATABASE_PATH,
        timeout=30
    )

    try:

        rows = read_enriched_data(
            connection
        )

        print(
            f"Enriched records loaded: {len(rows)}"
        )

        create_gold_table(
            connection
        )

        upsert_gold_data(
            rows,
            connection
        )

    finally:

        connection.close()

    print(
        "URLHaus Gold Load Completed"
    )


if __name__ == "__main__":

    main()