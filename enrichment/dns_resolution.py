import socket
import sqlite3
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATABASE_PATH = PROJECT_ROOT / "data" / "threat_intelligence.db"

SILVER_TABLE = "silver_urlhaus_domains"

ENRICHED_TABLE = "silver_urlhaus_domains_enriched"

MAX_WORKERS = 20


def resolve_ipv4(domain):

    try:

        results = socket.getaddrinfo(
            domain,
            None,
            socket.AF_INET,
            socket.SOCK_STREAM
        )

        if results:

            return results[0][4][0]

    except (
        socket.gaierror,
        socket.timeout,
        OSError
    ):

        return None

    return None


def resolve_domains(domains):

    results = [None] * len(domains)

    with ThreadPoolExecutor(
        max_workers=MAX_WORKERS
    ) as executor:

        future_to_index = {
            executor.submit(
                resolve_ipv4,
                domain
            ): index
            for index, domain in enumerate(domains)
        }

        for future in as_completed(
            future_to_index
        ):

            index = future_to_index[future]

            try:

                results[index] = future.result()

            except Exception:

                results[index] = None

    return results


def read_silver_domains(connection):

    cursor = connection.execute(
        f"""
        SELECT domain
        FROM {SILVER_TABLE}
        """
    )

    return [
        row[0]
        for row in cursor.fetchall()
    ]


def create_enriched_table(connection):

    connection.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {ENRICHED_TABLE} (
            domain TEXT PRIMARY KEY,
            ipv4 TEXT
        )
        """
    )

    connection.commit()


def load_enriched_data(
    domains,
    ipv4_results,
    connection
):

    records = list(
        zip(
            domains,
            ipv4_results
        )
    )

    connection.executemany(
        f"""
        INSERT OR REPLACE INTO {ENRICHED_TABLE} (
            domain,
            ipv4
        )
        VALUES (?, ?)
        """,
        records
    )

    connection.commit()

    print(
        f"Enriched records loaded: {len(records)}"
    )


def main():

    print(
        "URLHaus DNS Enrichment Started"
    )

    connection = sqlite3.connect(
        DATABASE_PATH,
        timeout=30
    )

    try:

        domains = read_silver_domains(
            connection
        )

        print(
            f"Domains loaded: {len(domains)}"
        )

        ipv4_results = resolve_domains(
            domains
        )

        resolved_count = sum(
            ip is not None
            for ip in ipv4_results
        )

        failed_count = len(ipv4_results) - resolved_count

        print(
            f"DNS resolved: {resolved_count}"
        )

        print(
            f"DNS failed: {failed_count}"
        )

        create_enriched_table(
            connection
        )

        load_enriched_data(
            domains,
            ipv4_results,
            connection
        )

    finally:

        connection.close()

    print(
        "URLHaus DNS Enrichment Completed"
    )


if __name__ == "__main__":

    main()