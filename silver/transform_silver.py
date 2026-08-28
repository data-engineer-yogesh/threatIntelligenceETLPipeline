import csv
import re
import sqlite3
from pathlib import Path
from urllib.parse import urlparse


PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATABASE_PATH = PROJECT_ROOT / "data" / "threat_intelligence.db"

BRONZE_TABLE = "bronze_urlhaus"

SILVER_TABLE = "silver_urlhaus_domains"


def parse_url_column(rows):

    return [
        {
            "raw_url": row["url"]
        }
        for row in rows
        if row.get("url")
    ]


def extract_domain(rows):

    result = []

    for row in rows:

        raw_url = row["raw_url"].strip()

        if not raw_url:
            continue

        if not re.match(
            r"^https?://",
            raw_url,
            re.IGNORECASE
        ):
            raw_url = "http://" + raw_url

        parsed_url = urlparse(raw_url)

        domain = parsed_url.hostname

        if domain:

            result.append(
                {
                    "raw_url": row["raw_url"],
                    "domain": domain.lower()
                }
            )

    return result


def validate_domain(rows):

    domain_pattern = re.compile(
        r"^(?=.{1,253}$)"
        r"(?:[a-zA-Z0-9]"
        r"(?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+"
        r"[a-zA-Z]{2,63}$"
    )

    return [
        row
        for row in rows
        if domain_pattern.match(
            row["domain"]
        )
    ]


def remove_noise_and_duplicates(rows):

    seen = set()

    result = []

    for row in rows:

        domain = row["domain"].strip().lower()

        if not domain:
            continue

        if domain.startswith("#"):
            continue

        if domain in (
            "localhost",
            "127.0.0.1"
        ):
            continue

        if domain in seen:
            continue

        seen.add(domain)

        result.append(
            {
                "domain": domain
            }
        )

    return result


def read_bronze_data(connection):

    cursor = connection.execute(
        f"""
        SELECT url
        FROM {BRONZE_TABLE}
        """
    )

    columns = [
        description[0]
        for description in cursor.description
    ]

    return [
        dict(zip(columns, row))
        for row in cursor.fetchall()
    ]


def create_silver_table(connection):

    connection.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {SILVER_TABLE} (
            domain TEXT PRIMARY KEY
        )
        """
    )

    connection.commit()


def load_silver(rows, connection):

    connection.execute(
        f"""
        DELETE FROM {SILVER_TABLE}
        """
    )

    connection.executemany(
        f"""
        INSERT INTO {SILVER_TABLE} (
            domain
        )
        VALUES (?)
        """,
        [
            (row["domain"],)
            for row in rows
        ]
    )

    connection.commit()


def main():

    print("URLHaus Silver Transformation Started")

    connection = sqlite3.connect(
        DATABASE_PATH
    )

    try:

        bronze_rows = read_bronze_data(
            connection
        )

        print(
            f"Bronze records: {len(bronze_rows)}"
        )

        parsed_rows = parse_url_column(
            bronze_rows
        )

        print(
            f"URLs extracted: {len(parsed_rows)}"
        )

        domain_rows = extract_domain(
            parsed_rows
        )

        print(
            f"Domains extracted: {len(domain_rows)}"
        )

        valid_rows = validate_domain(
            domain_rows
        )

        print(
            f"Valid domains: {len(valid_rows)}"
        )

        silver_rows = remove_noise_and_duplicates(
            valid_rows
        )

        print(
            f"Unique domains: {len(silver_rows)}"
        )

        create_silver_table(
            connection
        )

        load_silver(
            silver_rows,
            connection
        )

    finally:

        connection.close()

    print("URLHaus Silver Transformation Completed")


if __name__ == "__main__":

    main()