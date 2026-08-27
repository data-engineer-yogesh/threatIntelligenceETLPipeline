import csv
import sqlite3

from bronze.raw_ingestions_of_files_to_bronze import (
    clean_urlhaus_file,
    read_clean_csv,
    create_bronze_table,
    load_bronze
)


def test_clean_urlhaus_file(tmp_path):

    source_file = tmp_path / "urlhaus.csv"
    clean_file = tmp_path / "urlhaus_clean.csv"

    source_content = """# URLHaus Database Dump
# Last updated: 2026-08-27
# Terms Of Use: https://urlhaus.abuse.ch/api/
# id,dateadded,url,url_status,last_online,threat,tags,urlhaus_link,reporter
"1","2026-08-27 10:00:00","http://example.com","online","","malware_download","test","https://urlhaus.abuse.ch/url/1/","testuser"
"2","2026-08-27 10:01:00","http://example.org","online","","malware_download","test","https://urlhaus.abuse.ch/url/2/","testuser"
"""

    source_file.write_text(
        source_content,
        encoding="utf-8"
    )

    clean_urlhaus_file(
        source_file,
        clean_file
    )

    content = clean_file.read_text(
        encoding="utf-8"
    )

    assert "URLHaus Database Dump" not in content
    assert "Last updated" not in content
    assert "Terms Of Use" not in content

    assert content.startswith(
        "id,dateadded,url,url_status,last_online,threat,tags,urlhaus_link,reporter"
    )

    assert '"1","2026-08-27 10:00:00"' in content
    assert '"2","2026-08-27 10:01:00"' in content


def test_read_clean_csv(tmp_path):

    clean_file = tmp_path / "urlhaus_clean.csv"

    content = """id,dateadded,url,url_status,last_online,threat,tags,urlhaus_link,reporter
"1","2026-08-27 10:00:00","http://example.com","online","","malware_download","test","https://urlhaus.abuse.ch/url/1/","testuser"
"""

    clean_file.write_text(
        content,
        encoding="utf-8"
    )

    rows = read_clean_csv(clean_file)

    assert len(rows) == 1
    assert rows[0]["id"] == "1"
    assert rows[0]["url"] == "http://example.com"


def test_create_bronze_table():

    connection = sqlite3.connect(":memory:")

    create_bronze_table(connection)

    cursor = connection.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
        AND name = 'bronze_urlhaus'
        """
    )

    result = cursor.fetchone()

    assert result is not None
    assert result[0] == "bronze_urlhaus"

    connection.close()


def test_load_bronze():

    connection = sqlite3.connect(":memory:")

    create_bronze_table(connection)

    rows = [
        {
            "id": "1",
            "dateadded": "2026-08-27 10:00:00",
            "url": "http://example.com",
            "url_status": "online",
            "last_online": "",
            "threat": "malware_download",
            "tags": "test",
            "urlhaus_link": "https://urlhaus.abuse.ch/url/1/",
            "reporter": "testuser"
        },
        {
            "id": "2",
            "dateadded": "2026-08-27 10:01:00",
            "url": "http://example.org",
            "url_status": "online",
            "last_online": "",
            "threat": "malware_download",
            "tags": "test",
            "urlhaus_link": "https://urlhaus.abuse.ch/url/2/",
            "reporter": "testuser"
        }
    ]

    load_bronze(
        rows,
        connection
    )

    cursor = connection.execute(
        "SELECT COUNT(*) FROM bronze_urlhaus"
    )

    count = cursor.fetchone()[0]

    assert count == 2

    cursor = connection.execute(
        """
        SELECT id, url
        FROM bronze_urlhaus
        ORDER BY id
        """
    )

    results = cursor.fetchall()

    assert results[0] == (1, "http://example.com")
    assert results[1] == (2, "http://example.org")

    connection.close()