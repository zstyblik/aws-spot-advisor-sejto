#!/usr/bin/env python3
"""Unit tests for aws_spot_advisor_sejto.py.

2024/Nov/06 @ Zdenek Styblik
"""
import json
import os
import sys
from unittest.mock import call
from unittest.mock import Mock  # noqa: I100
from unittest.mock import patch

import pytest

import aws_spot_advisor_sejto as sejto
from lib import dataset


@pytest.mark.parametrize(
    "count,expected_log_level",
    [
        (-10, 40),
        (0, 40),
        (1, 30),
        (2, 20),
        (3, 10),
        (4, 10),
        (5, 10),
        (50, 10),
    ],
)
def test_calc_log_level(count, expected_log_level):
    """Test that calc_log_level() works as expected."""
    result = sejto.calc_log_level(count)
    assert result == expected_log_level


@patch("aws_spot_advisor_sejto.conf.write")
def test_get_dataset(mock_conf_write, fixture_mock_requests, fixture_temp_file):
    """Test that get_dataset() works as expected."""
    test_url = "https://pytest.example.com/"
    conf_fname = "/pytest/no/config/file"
    data_fname = fixture_temp_file
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

    dset = sejto.get_dataset(conf_fname, fixture_temp_file, test_url)
    assert dset.http_etag == expected_http_etag
    assert dset.http_last_modified == expected_http_lm
    assert "abraka" in dset.data
    #
    with open(data_fname, "r", encoding="utf-8") as fhandle:
        data = json.load(fhandle)

    assert "abraka" in data
    #
    mock_conf_write.assert_called_once()

    req_history = mock_http.request_history
    assert len(req_history) == 1
    assert req_history[0].method == "GET"
    assert req_history[0].url == test_url


@patch("aws_spot_advisor_sejto.get_dataset")
def test_main(mock_get_dataset, capsys, caplog):
    """Test run-through main().

    NOTE(zstyblik): better way would be to provide tmp data dir and let main()
    do its thing with config, JSON and making an HTTP request(which would have
    to be mocked, of course). TODO for next iteration since it's late, again,
    and nobody is going to use this anyway.
    """
    region = "us-east-1"
    os_name = "Linux"
    data = {
        "ranges": [
            {"index": 0, "label": "<5%", "max": 5},
            {"index": 1, "label": "5-10%", "max": 11},
        ],
        "instance_types": {
            "t3.nano": {"emr": True, "cores": 0, "ram_gb": 0},
            "t2.nano": {"emr": True, "cores": 0, "ram_gb": 0},
            "t2.large": {"emr": True, "cores": 0, "ram_gb": 0},
        },
        "spot_advisor": {
            "us-east-1": {
                "Linux": {
                    "t3.nano": {"s": 80, "r": 1},
                    "t2.nano": {"s": 76, "r": 0},
                    "t2.large": {"s": 75, "r": 0},
                },
            },
        },
    }

    expected_log_tuples = []
    expected_output = os.linesep.join(
        [
            (
                "instance_type=t2.nano vcpus=0 mem_gb=0.0 savings=76% "
                "interrupts=<5%"
            ),
            (
                "instance_type=t2.large vcpus=0 mem_gb=0.0 savings=75% "
                "interrupts=<5%"
            ),
            (
                "instance_type=t3.nano vcpus=0 mem_gb=0.0 savings=80% "
                "interrupts=5-10%"
            ),
            "",
        ]
    )

    mock_dset = dataset.DataSet(data=data)
    mock_get_dataset.return_value = mock_dset

    args = [
        "./aws_spot_advisor_sejto.py",
        "--region",
        region,
        "--os",
        os_name,
    ]
    with patch.object(sys, "argv", args):
        sejto.main()

    assert mock_get_dataset.called is True

    captured = capsys.readouterr()
    assert captured.out == expected_output
    assert captured.err == ""

    assert caplog.record_tuples == expected_log_tuples


@patch("aws_spot_advisor_sejto.get_dataset")
def test_main_has_region_check(mock_get_dataset, capsys, caplog):
    """Test that region check works as execpted in main()."""
    region = "us-east-1"
    os_name = "Linux"
    expected_log_tuples = [
        (
            "aws_spot_advisor_sejto",
            40,
            "Region '{:s}' not found in data.".format(region),
        ),
    ]
    expected_mock_calls = [call.has_region(region)]

    mock_dset = Mock()
    mock_dset.has_region.return_value = False
    mock_get_dataset.return_value = mock_dset

    exception = None
    args = [
        "./aws_spot_advisor_sejto.py",
        "--region",
        region,
        "--os",
        os_name,
    ]
    with patch.object(sys, "argv", args):
        try:
            sejto.main()
        except SystemExit as sys_exit:
            exception = sys_exit

    assert isinstance(exception, SystemExit) is True
    assert exception.code == 1
    assert mock_dset.method_calls == expected_mock_calls

    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""

    assert caplog.record_tuples == expected_log_tuples


@patch("aws_spot_advisor_sejto.get_dataset")
def test_main_has_os_check(mock_get_dataset, capsys, caplog):
    """Test that OS check works as execpted in main()."""
    region = "us-east-1"
    os_name = "Linux"
    expected_log_tuples = [
        (
            "aws_spot_advisor_sejto",
            40,
            "OS '{:s}' is not available in region '{:s}'.".format(
                os_name,
                region,
            ),
        ),
    ]
    expected_mock_calls = [
        call.has_region(region),
        call.has_os(region, os_name),
    ]

    mock_dset = Mock()
    mock_dset.has_region.return_value = True
    mock_dset.has_os.return_value = False
    mock_get_dataset.return_value = mock_dset

    exception = None
    args = [
        "./aws_spot_advisor_sejto.py",
        "--region",
        region,
        "--os",
        os_name,
    ]
    with patch.object(sys, "argv", args):
        try:
            sejto.main()
        except SystemExit as sys_exit:
            exception = sys_exit

    assert isinstance(exception, SystemExit) is True
    assert exception.code == 1
    assert mock_dset.method_calls == expected_mock_calls

    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""

    assert caplog.record_tuples == expected_log_tuples


def test_print_out(capsys):
    """Test print_out()."""
    results = {
        "t3.nano": {
            "instance_type": "t3.nano",
            "cores": 0,
            "ram_gb": 0,
            "savings": 80,
            "inter_label": "5-10%",
            "inter_max": 11,
        },
        "t2.nano": {
            "instance_type": "t2.nano",
            "cores": 0,
            "ram_gb": 0,
            "savings": 76,
            "inter_label": "<5%",
            "inter_max": 5,
        },
        "t2.large": {
            "instance_type": "t2.large",
            "cores": 0,
            "ram_gb": 0,
            "savings": 75,
            "inter_label": "<5%",
            "inter_max": 5,
        },
    }
    expected_output = os.linesep.join(
        [
            (
                "instance_type=t2.nano vcpus=0 mem_gb=0.0 savings=76% "
                "interrupts=<5%"
            ),
            (
                "instance_type=t2.large vcpus=0 mem_gb=0.0 savings=75% "
                "interrupts=<5%"
            ),
            (
                "instance_type=t3.nano vcpus=0 mem_gb=0.0 savings=80% "
                "interrupts=5-10%"
            ),
            "",
        ]
    )

    sejto.print_out(results)

    captured = capsys.readouterr()
    assert captured.out == expected_output
