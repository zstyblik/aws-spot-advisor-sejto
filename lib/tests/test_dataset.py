#!/usr/bin/env python3
"""Unit tests for aws_spot_advisor_sejto.lib.dataset.py.

2024/Nov/06 @ Zdenek Styblik
"""
import json
import os

import pytest

from lib import dataset

SCRIPT_PATH = os.path.dirname(os.path.realpath(__file__))


class MockDataSet(dataset.DataSet):
    """Mock of DataSet."""

    def check_checksum(self):
        """Mock of which will always return True."""
        return True


@pytest.mark.parametrize(
    "data_fname,expected_checksum",
    [
        # NOTE: ERROR log should be checked as well in this case
        ("", ""),
        (
            os.path.join(SCRIPT_PATH, "files", "test_sha256.txt"),
            "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        ),
    ],
)
def test_dataset_calc_checksum(data_fname, expected_checksum):
    """Test that DataSet.calc_checksum() works as expected."""
    dset = dataset.DataSet(data_fname=data_fname)
    result = dset.calc_checksum()
    assert result == expected_checksum


@pytest.mark.parametrize(
    "data_fname,data_checksum,expected",
    [
        (
            os.path.join(SCRIPT_PATH, "files", "test_sha256.txt"),
            "",
            False,
        ),
        (
            "",
            "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            False,
        ),
        (
            os.path.join(SCRIPT_PATH, "files", "test_sha256.txt"),
            "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            True,
        ),
    ],
)
def test_dataset_check_checksum(data_fname, data_checksum, expected):
    """Test that DataSet.check_checksum() works as expected."""
    dset = dataset.DataSet(
        data_fname=data_fname,
        data_checksum=data_checksum,
    )
    result = dset.check_checksum()
    assert result is expected


@pytest.mark.parametrize(
    "headers,expected_http_etag,expected_http_last_modified",
    [
        ({}, "", ""),
        ({"something": "nothing"}, "", ""),
        ({"etag": "pytest_etag"}, "pytest_etag", ""),
        (
            {"last-modified": "pytest_lm", "nothing": "something"},
            "",
            "pytest_lm",
        ),
        (
            {
                "etag": "pytest_etag",
                "last-modified": "pytest_lm",
                "nothing": "something",
            },
            "pytest_etag",
            "pytest_lm",
        ),
    ],
)
def test_dataset_extract_caching_headers(
    headers, expected_http_etag, expected_http_last_modified
):
    """Test that DataSet.extract_caching_headers() works as expected."""
    dset = dataset.DataSet()
    dset.extract_caching_headers(headers)
    assert dset.http_etag == expected_http_etag
    assert dset.http_last_modified == expected_http_last_modified


@pytest.mark.parametrize(
    "data,region,os_name,expected",
    [
        ({}, "pytest", "pyregion", False),
        ({"spot_advisor": {}}, "pyregion", "pyos", False),
        ({"spot_advisor": {"pyregion": {}}}, "pyregion", "pyos", False),
        (
            {"spot_advisor": {"pyregion": {"pyos": []}}},
            "pyregion",
            "pyos",
            True,
        ),
    ],
)
def test_dataset_has_os(data, region, os_name, expected):
    """Test that DataSet.has_os() works as expected."""
    dset = dataset.DataSet(data=data)
    result = dset.has_os(region, os_name)
    assert result is expected


@pytest.mark.parametrize(
    "data,region,expected",
    [
        ({}, "pyregion", False),
        ({"spot_advisor": {}}, "pyregion", False),
        ({"spot_advisor": {"pyregion": {}}}, "pyregion", True),
    ],
)
def test_dataset_has_region(data, region, expected):
    """Test that DataSet.has_region() works as expected."""
    dset = dataset.DataSet(data=data)
    result = dset.has_region(region)
    assert result is expected


@pytest.mark.parametrize(
    "http_etag,http_last_modified,expected",
    [
        ("", "", {}),
        ("etag1234", "", {"if-none-match": "etag1234"}),
        ("", "last modified 123", {"if-modified-since": "last modified 123"}),
        (
            "etag1234",
            "last modified 123",
            {
                "if-none-match": "etag1234",
                "if-modified-since": "last modified 123",
            },
        ),
    ],
)
def test_dataset_make_caching_headers(http_etag, http_last_modified, expected):
    """Test that DataSet.make_caching_headers() works as expected."""
    dset = dataset.DataSet(
        http_etag=http_etag,
        http_last_modified=http_last_modified,
    )
    result = dset.make_caching_headers()
    assert result == expected


def test_dataset_update_http_200(fixture_mock_requests, fixture_temp_file):
    """Test that DataSet.update() handles HTTP Status Code 304 as expected.

    * http_etag and http_last_modified are set/updated
    * needs to write into file
    * check data
    """
    test_url = "https://pytest.example.com/"
    data_checksum_original = (
        "9cbb5471071b825555f00e0102dbfb19f1e446060151c8afcb7fdf17de2395a7"
    )
    expected_http_etag = "pytest_etag"
    expected_http_lm = "pytest_lm"
    mock_http = fixture_mock_requests.get(
        test_url,
        status_code=200,
        text='{"abraka":"dabra"}',
        headers={
            "ETag": expected_http_etag,
            "Last-Modified": expected_http_lm,
        },
    )

    dset = dataset.DataSet(
        data_fname=fixture_temp_file,
        data_checksum=data_checksum_original,
        http_etag="pytest_etag_original",
        http_last_modified="pytest_lm_original",
    )
    dset.update(test_url)

    assert dset.http_etag == expected_http_etag
    assert dset.http_last_modified == expected_http_lm
    assert dset.data_checksum != data_checksum_original
    assert "abraka" in dset.data

    with open(fixture_temp_file, "r", encoding="utf-8") as fhandle:
        data = json.load(fhandle)

    assert "abraka" in data

    req_history = mock_http.request_history
    assert len(req_history) == 1
    assert req_history[0].method == "GET"
    assert req_history[0].url == test_url


def test_dataset_update_http_304(fixture_mock_requests):
    """Test that DataSet.update() handles HTTP Status Code 304 as expected.

    * data should be read from file -> check data
    * check ETag and Last-Modified which should be updated
    """
    test_url = "https://pytest.example.com/"
    data_fname = os.path.join(SCRIPT_PATH, "files", "test_spot_advisor.json")
    data_checksum = (
        "9cbb5471071b825555f00e0102dbfb19f1e446060151c8afcb7fdf17de2395a7"
    )
    expected_http_etag = "pytest_etag_304"
    expected_http_lm = "pytest_lm_304"
    mock_http = fixture_mock_requests.get(
        test_url,
        status_code=304,
        text="does not matter and ignored",
        headers={
            "ETag": expected_http_etag,
            "Last-Modified": expected_http_lm,
        },
    )

    dset = dataset.DataSet(
        data_fname=data_fname,
        data_checksum=data_checksum,
        http_etag="pytest_etag",
        http_last_modified="pytest_lm",
    )
    dset.update(test_url)

    assert dset.http_etag == expected_http_etag
    assert dset.http_last_modified == expected_http_lm
    assert "pytest" in dset.data

    req_history = mock_http.request_history
    assert len(req_history) == 1
    assert req_history[0].method == "GET"
    assert req_history[0].url == test_url


def test_dataset_update_http_304_304(fixture_mock_requests):
    """Test that DataSet.update() raises RecursionError exception as expected.

    RecursionError should be raised on second HTTP Status Code 304.
    """
    test_url = "https://pytest.example.com/"
    data_fname = "/pytest/file/does/not/exist"
    data_checksum = (
        "9cbb5471071b825555f00e0102dbfb19f1e446060151c8afcb7fdf17de2395a7"
    )
    mock_http = fixture_mock_requests.get(
        test_url,
        status_code=304,
        text="does not matter and ignored",
        headers={
            "ETag": "pytest_etag_304",
            "Last-Modified": "pytest_lm_304",
        },
    )

    dset = MockDataSet(
        data_fname=data_fname,
        data_checksum=data_checksum,
        http_etag="pytest_etag",
        http_last_modified="pytest_lm",
    )
    with pytest.raises(RecursionError):
        dset.update(test_url)

    assert dset.http_etag == ""
    assert dset.http_last_modified == ""
    assert dset.data_checksum == ""

    req_history = mock_http.request_history
    assert len(req_history) == 2
    for idx in range(0, 2):
        assert req_history[idx].method == "GET"
        assert req_history[idx].url == test_url


def test_dataset_get_data(fixture_mock_requests):
    """Test that get_data() works as expected."""
    test_url = "https://pytest.example.com/"
    test_text = "pytest"
    mock_http = fixture_mock_requests.get(
        test_url,
        status_code=200,
        text=test_text,
        headers={
            "ETag": "pytest_etag",
            "Last-Modified": "pytest_lm",
        },
    )
    rsp = dataset.get_data(test_url)

    assert rsp.status_code == 200
    assert rsp.text == test_text

    req_history = mock_http.request_history
    assert len(req_history) == 1
    assert req_history[0].method == "GET"
    assert req_history[0].url == test_url
