import sqlite3

from gold.load_gold import (
    create_gold_table,
    upsert_gold_data
)


def test_create_gold_table():

    connection = sqlite3.connect(":memory:")

    create_gold_table(connection)

    result = connection.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
        AND name = 'gold_urlhaus_domains'
        """
    ).fetchone()

    assert result is not None

    assert result[0] == "gold_urlhaus_domains"

    connection.close()


def test_gold_table_columns():

    connection = sqlite3.connect(":memory:")

    create_gold_table(connection)

    columns = connection.execute(
        """
        PRAGMA table_info(gold_urlhaus_domains)
        """
    ).fetchall()

    column_names = [
        column[1]
        for column in columns
    ]

    assert column_names == [
        "domain",
        "resolved_ip",
        "last_updated"
    ]

    connection.close()


def test_upsert_inserts_new_records():

    connection = sqlite3.connect(":memory:")

    create_gold_table(connection)

    rows = [
        (
            "example.com",
            "93.184.216.34"
        ),
        (
            "example.org",
            "93.184.216.35"
        )
    ]

    upsert_gold_data(
        rows,
        connection
    )

    result = connection.execute(
        """
        SELECT domain, resolved_ip
        FROM gold_urlhaus_domains
        ORDER BY domain
        """
    ).fetchall()

    assert result == [
        ("example.com", "93.184.216.34"),
        ("example.org", "93.184.216.35")
    ]

    connection.close()


def test_upsert_updates_existing_domain():

    connection = sqlite3.connect(":memory:")

    create_gold_table(connection)

    first_load = [
        (
            "example.com",
            "93.184.216.34"
        )
    ]

    upsert_gold_data(
        first_load,
        connection
    )

    second_load = [
        (
            "example.com",
            "1.2.3.4"
        )
    ]

    upsert_gold_data(
        second_load,
        connection
    )

    result = connection.execute(
        """
        SELECT domain, resolved_ip
        FROM gold_urlhaus_domains
        """
    ).fetchall()

    assert result == [
        ("example.com", "1.2.3.4")
    ]

    connection.close()


def test_upsert_does_not_create_duplicates():

    connection = sqlite3.connect(":memory:")

    create_gold_table(connection)

    rows = [
        (
            "example.com",
            "93.184.216.34"
        )
    ]

    upsert_gold_data(
        rows,
        connection
    )

    upsert_gold_data(
        rows,
        connection
    )

    count = connection.execute(
        """
        SELECT COUNT(*)
        FROM gold_urlhaus_domains
        WHERE domain = 'example.com'
        """
    ).fetchone()[0]

    assert count == 1

    connection.close()


def test_upsert_handles_null_ip():

    connection = sqlite3.connect(":memory:")

    create_gold_table(connection)

    rows = [
        (
            "dead-domain.example",
            None
        )
    ]

    upsert_gold_data(
        rows,
        connection
    )

    result = connection.execute(
        """
        SELECT domain, resolved_ip
        FROM gold_urlhaus_domains
        """
    ).fetchone()

    assert result == (
        "dead-domain.example",
        None
    )

    connection.close()