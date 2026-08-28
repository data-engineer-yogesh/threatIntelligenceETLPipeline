import sqlite3

from silver.transform_silver import (
    parse_url_column,
    extract_domain,
    validate_domain,
    remove_noise_and_duplicates,
    create_silver_table,
    load_silver
)


def test_parse_url_column():

    rows = [
        {"url": "http://example.com/test"},
        {"url": "https://example.org"},
        {"url": ""}
    ]

    result = parse_url_column(rows)

    assert result == [
        {"raw_url": "http://example.com/test"},
        {"raw_url": "https://example.org"}
    ]


def test_extract_domain():

    rows = [
        {"raw_url": "http://example.com/test"},
        {"raw_url": "https://example.org/path"},
        {"raw_url": "http://sub.example.com:8080/test"},
        {"raw_url": "example.net/path"}
    ]

    result = extract_domain(rows)

    domains = [
        row["domain"]
        for row in result
    ]

    assert domains == [
        "example.com",
        "example.org",
        "sub.example.com",
        "example.net"
    ]


def test_validate_domain():

    rows = [
        {"domain": "example.com"},
        {"domain": "sub.example.org"},
        {"domain": "invalid_domain"},
        {"domain": "localhost"},
        {"domain": "example"}
    ]

    result = validate_domain(rows)

    domains = [
        row["domain"]
        for row in result
    ]

    assert domains == [
        "example.com",
        "sub.example.org"
    ]


def test_remove_noise_and_duplicates():

    rows = [
        {"domain": "example.com"},
        {"domain": "example.com"},
        {"domain": "Example.org"},
        {"domain": "localhost"},
        {"domain": "127.0.0.1"},
        {"domain": ""},
        {"domain": "#comment"}
    ]

    result = remove_noise_and_duplicates(rows)

    domains = [
        row["domain"]
        for row in result
    ]

    assert domains == [
        "example.com",
        "example.org"
    ]


def test_create_silver_table():

    connection = sqlite3.connect(":memory:")

    create_silver_table(connection)

    cursor = connection.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
        AND name = 'silver_urlhaus_domains'
        """
    )

    result = cursor.fetchone()

    assert result is not None
    assert result[0] == "silver_urlhaus_domains"

    connection.close()


def test_load_silver():

    connection = sqlite3.connect(":memory:")

    create_silver_table(connection)

    rows = [
        {"domain": "example.com"},
        {"domain": "example.org"}
    ]

    load_silver(
        rows,
        connection
    )

    result = connection.execute(
        """
        SELECT domain
        FROM silver_urlhaus_domains
        ORDER BY domain
        """
    ).fetchall()

    assert result == [
        ("example.com",),
        ("example.org",)
    ]

    connection.close()