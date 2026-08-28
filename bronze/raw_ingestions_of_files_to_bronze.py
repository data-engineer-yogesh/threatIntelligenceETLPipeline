import csv
import sqlite3
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent

SOURCE_PATH = PROJECT_ROOT / "data" / "raw" / "urlhaus.csv"

CLEAN_PATH = PROJECT_ROOT / "data" / "bronze" / "urlhaus_clean.csv"

DATABASE_PATH = PROJECT_ROOT / "data" / "threat_intelligence.db"

BRONZE_TABLE = "bronze_urlhaus"


def clean_urlhaus_file(source_path, clean_path):

    clean_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(
        source_path,
        "r",
        encoding="utf-8"
    ) as source_file:

        lines = source_file.readlines()

    clean_lines = []

    for line in lines:

        line = line.strip()

        if line.startswith("# id,"):

            clean_lines.append(
                line[2:] + "\n"
            )

        elif line.startswith("#"):

            continue

        elif line:

            clean_lines.append(
                line + "\n"
            )

    with open(
        clean_path,
        "w",
        encoding="utf-8",
        newline=""
    ) as clean_file:

        clean_file.writelines(clean_lines)

    print("URLHaus comments removed.")
    print(f"Clean file created: {clean_path}")


def read_clean_csv(clean_path):

    with open(
        clean_path,
        "r",
        encoding="utf-8",
        newline=""
    ) as file:

        reader = csv.DictReader(file)

        rows = list(reader)

    return rows


def create_bronze_table(connection):

    connection.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {BRONZE_TABLE} (
            id INTEGER,
            dateadded TEXT,
            url TEXT,
            url_status TEXT,
            last_online TEXT,
            threat TEXT,
            tags TEXT,
            urlhaus_link TEXT,
            reporter TEXT
        )
        """
    )

    connection.commit()


def load_bronze(rows, connection):

    insert_sql = f"""
        INSERT INTO {BRONZE_TABLE} (
            id,
            dateadded,
            url,
            url_status,
            last_online,
            threat,
            tags,
            urlhaus_link,
            reporter
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """

    records = [
        (
            row.get("id"),
            row.get("dateadded"),
            row.get("url"),
            row.get("url_status"),
            row.get("last_online"),
            row.get("threat"),
            row.get("tags"),
            row.get("urlhaus_link"),
            row.get("reporter")
        )
        for row in rows
    ]

    connection.executemany(
        insert_sql,
        records
    )

    connection.commit()

    print(
        f"Bronze records inserted: {len(records)}"
    )


def main():

    print("URLHaus Bronze Ingestion Started")

    if not SOURCE_PATH.exists():

        raise FileNotFoundError(
            f"Source file not found: {SOURCE_PATH}"
        )

    clean_urlhaus_file(
        SOURCE_PATH,
        CLEAN_PATH
    )

    rows = read_clean_csv(
        CLEAN_PATH
    )

    print(
        f"Clean CSV records: {len(rows)}"
    )

    DATABASE_PATH.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    connection = sqlite3.connect(
        DATABASE_PATH
    )

    try:

        create_bronze_table(
            connection
        )

        load_bronze(
            rows,
            connection
        )

    finally:

        connection.close()

    print("URLHaus Bronze Ingestion Completed")


if __name__ == "__main__":

    main()