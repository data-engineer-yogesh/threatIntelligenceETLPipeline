from unittest.mock import patch, Mock

from ingestion.download_urlhaus import download_urlhaus


@patch("ingestion.download_urlhaus.requests.get")
def test_download_urlhaus(mock_get, tmp_path):

    # --------------------------------------------------------
    # Mock HTTP response
    # --------------------------------------------------------

    mock_response = Mock()

    mock_response.content = (
        b"# URLHaus test file\n"
        b"# id,dateadded,url\n"
        b"123,2026-08-27,http://example.com\n"
    )

    mock_response.raise_for_status.return_value = None

    mock_get.return_value = mock_response


    # --------------------------------------------------------
    # Run function
    # --------------------------------------------------------

    with patch(
        "ingestion.download_urlhaus.RAW_DIR",
        tmp_path
    ), patch(
        "ingestion.download_urlhaus.OUTPUT_FILE",
        tmp_path / "urlhaus.csv"
    ):

        download_urlhaus()


    # --------------------------------------------------------
    # Verify file was created
    # --------------------------------------------------------

    output_file = tmp_path / "urlhaus.csv"

    assert output_file.exists()


    # --------------------------------------------------------
    # Verify content
    # --------------------------------------------------------

    content = output_file.read_bytes()

    assert b"URLHaus test file" in content
    assert b"123,2026-08-27,http://example.com" in content


    # --------------------------------------------------------
    # Verify HTTP request
    # --------------------------------------------------------

    mock_get.assert_called_once()