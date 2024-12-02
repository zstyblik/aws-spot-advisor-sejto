#!/usr/bin/env python3
"""Unit tests for aws_spot_advisor_sejto.lib.cli_args.py.

2024/Nov/06 @ Zdenek Styblik
"""
import sys
from unittest.mock import patch

import pytest

from lib import cli_args


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
    result = cli_args.calc_log_level(count)
    assert result == expected_log_level


def test_parse_args_sort_oder_exc(capsys):
    """Test that parse_args() handles ValueError exception as expected.

    parse_sort_order() raises ValueError exception which should be handled as an
    error message and SystemExit RC=2.
    """
    region = "us-east-1"
    os_name = "Linux"

    exception = None
    args = [
        "./aws_spot_advisor_sejto.py",
        "--region",
        region,
        "--os",
        os_name,
        "--sort-order",
        "pytest:pytest",
    ]
    with patch.object(sys, "argv", args):
        try:
            cli_args.parse_args("/path/doesnt/exist", "https://example.com")
        except SystemExit as sys_exit:
            exception = sys_exit

    assert isinstance(exception, SystemExit) is True
    assert exception.code == 2

    captured = capsys.readouterr()
    assert captured.out == ""
    assert "Column 'pytest' is invalid. Valid columns are" in captured.err


@pytest.mark.parametrize(
    "input_data,expected",
    [
        (
            "interrupts:asc,savings:desc",
            {
                "inter_max": 1,
                "savings": (-1),
            },
        ),
        (
            "interrupts:desc,savings:asc",
            {
                "inter_max": (-1),
                "savings": 1,
            },
        ),
        (
            "instance_type:asc,vcpus:asc,mem_gb:asc,savings:asc,interrupts:asc",
            {
                "instance_type": 1,
                "vcpus": 1,
                "mem_gb": 1,
                "savings": 1,
                "inter_max": 1,
            },
        ),
    ],
)
def test_parse_sort_order(input_data, expected):
    """Test parse_sort_order() under ideal conditions."""
    results = cli_args.parse_sort_order(input_data)
    print(results)
    assert results == expected


@pytest.mark.parametrize(
    "input_data,expected",
    [
        ("", "Input format must be 'column:sort_order', not ''."),
        (
            ":",
            (
                "Column '' is invalid. Valid columns are "
                "'instance_type', 'vcpus', 'mem_gb', 'emr', 'savings', "
                "'interrupts'."
            ),
        ),
        (
            "::",
            (
                "Column '' is invalid. Valid columns are "
                "'instance_type', 'vcpus', 'mem_gb', 'emr', 'savings', "
                "'interrupts'."
            ),
        ),
        ("pytest", "Input format must be 'column:sort_order', not 'pytest'."),
        (
            ":pytest",
            (
                "Column '' is invalid. Valid columns are "
                "'instance_type', 'vcpus', 'mem_gb', 'emr', 'savings', "
                "'interrupts'."
            ),
        ),
        (
            "pytest:",
            (
                "Column 'pytest' is invalid. Valid columns are "
                "'instance_type', 'vcpus', 'mem_gb', 'emr', 'savings', "
                "'interrupts'."
            ),
        ),
        (
            "vcpus:pytest:pytest",
            (
                "Sort order 'pytest:pytest' is invalid. "
                "Valid values are 'asc', 'desc'."
            ),
        ),
        (
            "vcpus:pytest",
            (
                "Sort order 'pytest' is invalid. "
                "Valid values are 'asc', 'desc'."
            ),
        ),
    ],
)
def test_parse_sort_order_exceptions(input_data, expected):
    """Test exceptions and input validation in parse_sort_order()."""
    with pytest.raises(ValueError) as excinfo:
        cli_args.parse_sort_order(input_data)

    assert expected == str(excinfo.value)
