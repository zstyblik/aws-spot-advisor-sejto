#!/usr/bin/env python3
"""Unit tests for aws_spot_advisor_sejto.lib.formatters.py.

2024/Nov/14 @ Zdenek Styblik
"""
import os
import sys

import pytest

from aws_spot_advisor_sejto.lib import formatters
from aws_spot_advisor_sejto.lib.models import EC2InstanceType
from aws_spot_advisor_sejto.lib.models import RegionDetail
from aws_spot_advisor_sejto.sejto import get_sorting_function


@pytest.fixture
def fixture_sorter():
    """Return sorting function."""
    sort_order = {"inter_max": 1, "savings": (-1)}
    yield get_sorting_function(sort_order)


@pytest.mark.parametrize(
    "results,expected_output",
    [
        (
            {
                "t3.nano": EC2InstanceType(
                    instance_type="t3.nano",
                    vcpus=4,
                    mem_gb=1.5,
                    savings=80,
                    inter_label="5-10%",
                    inter_max=11,
                ),
                "t2.nano": EC2InstanceType(
                    instance_type="t2.nano",
                    vcpus=3,
                    mem_gb=0.5,
                    emr=True,
                    savings=76,
                    inter_label="<5%",
                    inter_max=5,
                ),
                "t2.large": EC2InstanceType(
                    instance_type="t2.large",
                    vcpus=1,
                    mem_gb=2,
                    savings=75,
                    inter_label="<5%",
                    inter_max=5,
                ),
            },
            (
                "instance_type,vcpus,mem_gb,emr,savings,interrupts\r\n"
                "t2.nano,3,0.5,True,76,<5%\r\n"
                "t2.large,1,2,False,75,<5%\r\n"
                "t3.nano,4,1.5,False,80,5-10%\r\n"
            ),
        ),
        (
            {},
            "instance_type,vcpus,mem_gb,emr,savings,interrupts\r\n",
        ),
    ],
)
def test_ec2it_formatter_fmt_csv(
    results, expected_output, capsys, fixture_sorter
):
    """Test fmt_csv()."""
    formatter = formatters.EC2InstanceTypeFormatter(
        output_format="csv",
        fhandle=sys.stdout,
        sorting_fn=fixture_sorter,
    )
    formatter.fmt(results)

    captured = capsys.readouterr()
    assert captured.out == expected_output


@pytest.mark.parametrize(
    "results,expected_output",
    [
        (
            {
                "t3.nano": EC2InstanceType(
                    instance_type="t3.nano",
                    vcpus=4,
                    mem_gb=1.5,
                    savings=80,
                    inter_label="5-10%",
                    inter_max=11,
                ),
                "t2.nano": EC2InstanceType(
                    instance_type="t2.nano",
                    vcpus=3,
                    mem_gb=0.5,
                    emr=True,
                    savings=76,
                    inter_label="<5%",
                    inter_max=5,
                ),
                "t2.large": EC2InstanceType(
                    instance_type="t2.large",
                    vcpus=1,
                    mem_gb=2,
                    savings=75,
                    inter_label="<5%",
                    inter_max=5,
                ),
            },
            os.linesep.join(
                [
                    "[",
                    "    {",
                    '        "instance_type": "t2.nano",',
                    '        "vcpus": 3,',
                    '        "mem_gb": 0.5,',
                    '        "emr": true,',
                    '        "savings": 76,',
                    '        "interrupts": "<5%"',
                    "    },",
                    "    {",
                    '        "instance_type": "t2.large",',
                    '        "vcpus": 1,',
                    '        "mem_gb": 2,',
                    '        "emr": false,',
                    '        "savings": 75,',
                    '        "interrupts": "<5%"',
                    "    },",
                    "    {",
                    '        "instance_type": "t3.nano",',
                    '        "vcpus": 4,',
                    '        "mem_gb": 1.5,',
                    '        "emr": false,',
                    '        "savings": 80,',
                    '        "interrupts": "5-10%"',
                    "    }",
                    "]",
                ]
            ),
        ),
        ({}, "[]"),
    ],
)
def test_ec2it_formatter_fmt_json(
    results, expected_output, capsys, fixture_sorter
):
    """Test fmt_json()."""
    formatter = formatters.EC2InstanceTypeFormatter(
        output_format="json",
        fhandle=sys.stdout,
        sorting_fn=fixture_sorter,
    )
    formatter.fmt(results)

    captured = capsys.readouterr()
    assert captured.out == expected_output


@pytest.mark.parametrize(
    "results,expected_output",
    [
        (
            {
                "t3.nano": EC2InstanceType(
                    instance_type="t3.nano",
                    vcpus=4,
                    mem_gb=1.5,
                    savings=80,
                    inter_label="5-10%",
                    inter_max=11,
                ),
                "t2.nano": EC2InstanceType(
                    instance_type="t2.nano",
                    vcpus=3,
                    mem_gb=0.5,
                    emr=True,
                    savings=76,
                    inter_label="<5%",
                    inter_max=5,
                ),
                "t2.large": EC2InstanceType(
                    instance_type="t2.large",
                    vcpus=1,
                    mem_gb=2,
                    savings=75,
                    inter_label="<5%",
                    inter_max=5,
                ),
            },
            os.linesep.join(
                [
                    (
                        "instance_type=t2.nano vcpus=3 mem_gb=0.5 savings=76% "
                        "interrupts=<5%"
                    ),
                    (
                        "instance_type=t2.large vcpus=1 mem_gb=2.0 savings=75% "
                        "interrupts=<5%"
                    ),
                    (
                        "instance_type=t3.nano vcpus=4 mem_gb=1.5 savings=80% "
                        "interrupts=5-10%"
                    ),
                    "",
                ]
            ),
        ),
        ({}, "{}".format(os.linesep)),
    ],
)
def test_ec2it_formatter_fmt_text(
    results, expected_output, capsys, fixture_sorter
):
    """Test fmt_text()."""
    formatter = formatters.EC2InstanceTypeFormatter(
        output_format="text",
        fhandle=sys.stdout,
        sorting_fn=fixture_sorter,
    )
    formatter.fmt(results)

    captured = capsys.readouterr()
    assert captured.out == expected_output


@pytest.mark.parametrize(
    "results,expected_output",
    [
        (
            {
                "us-east-1": RegionDetail(
                    region="us-east-1",
                    operating_systems=["Linux", "Windows"],
                ),
                "eu-central-1": RegionDetail(
                    region="eu-central-1",
                    operating_systems=["Linux"],
                ),
            },
            (
                "region,operating_systems\r\n"
                "eu-central-1,Linux\r\n"
                'us-east-1,"Linux,Windows"\r\n'
            ),
        ),
        ({}, "region,operating_systems\r\n"),
    ],
)
def test_region_detail_formatter_csv(results, expected_output, capsys, caplog):
    """Test that CSV output in RegionDetailFormatter() works as expected."""
    expected_log_tuples = []

    formatter = formatters.RegionDetailFormatter(
        output_format="csv",
        fhandle=sys.stdout,
        sorting_fn=lambda region_detail: region_detail.region,
    )
    formatter.fmt(results)

    captured = capsys.readouterr()
    assert captured.out == expected_output
    assert captured.err == ""

    assert caplog.record_tuples == expected_log_tuples


@pytest.mark.parametrize(
    "results,expected_output",
    [
        (
            {
                "us-east-1": RegionDetail(
                    region="us-east-1",
                    operating_systems=["Linux", "Windows"],
                ),
                "eu-central-1": RegionDetail(
                    region="eu-central-1",
                    operating_systems=["Linux"],
                ),
            },
            os.linesep.join(
                [
                    "[",
                    "    {",
                    '        "operating_systems": [',
                    '            "Linux"',
                    "        ],",
                    '        "region": "eu-central-1"',
                    "    },",
                    "    {",
                    '        "operating_systems": [',
                    '            "Linux",',
                    '            "Windows"',
                    "        ],",
                    '        "region": "us-east-1"',
                    "    }",
                    "]",
                ]
            ),
        ),
        ({}, "[]"),
    ],
)
def test_region_detail_formatter_json(results, expected_output, capsys, caplog):
    """Test that JSON output in RegionDetailFormatter() works as expected."""
    expected_log_tuples = []

    formatter = formatters.RegionDetailFormatter(
        output_format="json",
        fhandle=sys.stdout,
        sorting_fn=lambda region_detail: region_detail.region,
    )
    formatter.fmt(results)

    captured = capsys.readouterr()
    assert captured.out == expected_output
    assert captured.err == ""

    assert caplog.record_tuples == expected_log_tuples


@pytest.mark.parametrize(
    "results,expected_output",
    [
        (
            {
                "us-east-1": RegionDetail(
                    region="us-east-1",
                    operating_systems=["Linux", "Windows"],
                ),
                "eu-central-1": RegionDetail(
                    region="eu-central-1",
                    operating_systems=["Linux"],
                ),
            },
            os.linesep.join(
                [
                    "region=eu-central-1 operating_systems=Linux",
                    "region=us-east-1 operating_systems=Linux,Windows",
                    "",
                ],
            ),
        ),
        ({}, "{}".format(os.linesep)),
    ],
)
def test_region_detail_formatter_text(results, expected_output, capsys, caplog):
    """Test that TEXT output in RegionDetailFormatter() works as expected."""
    expected_log_tuples = []

    formatter = formatters.RegionDetailFormatter(
        output_format="text",
        fhandle=sys.stdout,
        sorting_fn=lambda region_detail: region_detail.region,
    )
    formatter.fmt(results)

    captured = capsys.readouterr()
    assert captured.out == expected_output
    assert captured.err == ""

    assert caplog.record_tuples == expected_log_tuples


def test_region_detail_formatter_output_fmt_validation():
    """Check that RegionDetailFormatter() raises ValueError.

    Exception should be raised when invalid output_format is given.
    """
    expected = "Output format 'pytest_format' is not supported"
    with pytest.raises(ValueError) as excinfo:
        _ = formatters.RegionDetailFormatter(
            output_format="pytest_format",
            fhandle=sys.stdout,
            sorting_fn=lambda region_detail: region_detail.region,
        )

    assert expected == str(excinfo.value)
