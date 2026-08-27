import socket
import sqlite3
from unittest.mock import patch


from enrichment.dns_resolution import (
    resolve_ipv4,
    resolve_domains,
    create_enriched_table,
    load_enriched_data
)


@patch("enrichment.dns_resolution.socket.getaddrinfo")
def test_resolve_ipv4_success(mock_getaddrinfo):

    mock_getaddrinfo.return_value = [
        (
            2,
            1,
            6,
            "",
            ("93.184.216.34", 0)
        )
    ]

    result = resolve_ipv4(
        "example.com"
    )

    assert result == "93.184.216.34"

    mock_getaddrinfo.assert_called_once_with(
        "example.com",
        None,
        2,
        1
    )


@patch("enrichment.dns_resolution.socket.getaddrinfo")
def test_resolve_ipv4_failure(mock_getaddrinfo):

    mock_getaddrinfo.side_effect = socket.gaierror(
        "DNS resolution failed"
    )

    result = resolve_ipv4(
        "invalid-domain.example"
    )

    assert result is None

    mock_getaddrinfo.assert_called_once()


@patch("enrichment.dns_resolution.resolve_ipv4")
def test_resolve_domains(mock_resolve_ipv4):

    def fake_resolve(domain):

        results = {
            "example.com": "93.184.216.34",
            "example.org": "93.184.216.35",
            "invalid.example": None
        }

        return results.get(domain)

    mock_resolve_ipv4.side_effect = fake_resolve

    domains = [
        "example.com",
        "example.org",
        "invalid.example"
    ]

    results = resolve_domains(
        domains
    )

    assert results == [
        "93.184.216.34",
        "93.184.216.35",
        None
    ]

    assert mock_resolve_ipv4.call_count == 3


def test_create_enriched_table():

    connection = sqlite3.connect(
        ":memory:"
    )

    create_enriched_table(
        connection
    )

    result = connection.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
        AND name = 'silver_urlhaus_domains_enriched'
        """
    ).fetchone()

    assert result is not None

    assert result[0] == (
        "silver_urlhaus_domains_enriched"
    )

    connection.close()


def test_load_enriched_data():

    connection = sqlite3.connect(
        ":memory:"
    )

    create_enriched_table(
        connection
    )

    domains = [
        "example.com",
        "example.org",
        "invalid.example"
    ]

    ipv4_results = [
        "93.184.216.34",
        "93.184.216.35",
        None
    ]

    load_enriched_data(
        domains,
        ipv4_results,
        connection
    )

    results = connection.execute(
        """
        SELECT domain, ipv4
        FROM silver_urlhaus_domains_enriched
        ORDER BY domain
        """
    ).fetchall()

    assert results == [
        ("example.com", "93.184.216.34"),
        ("example.org", "93.184.216.35"),
        ("invalid.example", None)
    ]

    connection.close()