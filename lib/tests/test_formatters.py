#!/usr/bin/env python3
"""Unit tests for aws_spot_advisor_sejto.lib.formatters.py.

2024/Nov/14 @ Zdenek Styblik
"""
import os
import sys

import pytest

from lib import formatters
from lib.models import EC2InstanceType


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
def test_formatters_fmt_csv(results, expected_output, capsys):
    """Test fmt_csv()."""
    formatters.fmt_csv(results, sys.stdout)

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
def test_formatters_fmt_json(results, expected_output, capsys):
    """Test fmt_json()."""
    formatters.fmt_json(results, sys.stdout)

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
def test_formatters_fmt_text(results, expected_output, capsys):
    """Test fmt_text()."""
    formatters.fmt_text(results, sys.stdout)

    captured = capsys.readouterr()
    assert captured.out == expected_output
