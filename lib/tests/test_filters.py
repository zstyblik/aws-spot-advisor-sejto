#!/usr/bin/env python3
"""Unit tests for aws_spot_advisor_sejto.lib.filters.py.

2024/Nov/06 @ Zdenek Styblik
"""
import re
from unittest.mock import patch

import pytest

from lib import filters


@pytest.mark.parametrize(
    "re_exclude,re_include,expected",
    [
        (
            None,
            None,
            # falltrough
            True,
        ),
        (
            None,
            # defined and re_include match
            re.compile(r"^abc$"),
            True,
        ),
        (
            None,
            # defined and re_include no match
            re.compile(r"^$"),
            False,
        ),
        (
            # defined and re_exclude no match
            re.compile(r"^$"),
            None,
            True,
        ),
        (
            # defined and re_exclude match
            re.compile(r"^abc$"),
            None,
            False,
        ),
    ],
)
def test_filter_by_regex(re_exclude, re_include, expected):
    """Check whether filter_by_regex() works as expected."""
    result = filters.filter_by_regex("abc", re_exclude, re_include)
    assert result == expected


@pytest.mark.parametrize(
    "emr_supported,emr_only,expected",
    [
        (True, True, True),
        (False, False, True),
        (True, False, True),
        (False, True, False),
    ],
)
def test_filter_emr(emr_supported, emr_only, expected):
    """Check whether filter_emr() works as expected."""
    result = filters.filter_emr(emr_supported, emr_only)
    assert result is expected


def test_filter_instance_type():
    """Smoke test of filter_instance_type()."""
    result = filters.filter_instance_type(
        "t2n.nano",
        re.compile(r"^$"),
        None,
        re.compile(r"^$"),
        None,
        re.compile(r"^$"),
        None,
    )
    assert result is True


@pytest.mark.parametrize(
    "keep_retvals,expected",
    [
        ([True, True, True], True),
        ([False, True, True], False),
        ([True, False, True], False),
        ([True, True, False], False),
    ],
)
@patch("lib.filters.filter_by_regex")
def test_filter_instance_type_logic(
    mock_by_regex,
    keep_retvals,
    expected,
):
    """Test eval logic in filter_instance_type()."""
    mock_by_regex.side_effect = keep_retvals
    result = filters.filter_instance_type(
        "t2.nano",
        re.compile(r""),
        re.compile(r""),
        re.compile(r""),
        re.compile(r""),
        re.compile(r""),
        re.compile(r""),
    )
    assert mock_by_regex.called is True
    assert result == expected


@patch("lib.filters.parse_ec2_instance_type")
def test_filter_instance_type_exc(mock_parse_ec2_it):
    """Check that filter_instance_type() returns True on ValueError.

    Check that filter_instance_type() returns True on ValueError from
    parse_ec2_instance_type().
    """
    mock_parse_ec2_it.side_effect = ValueError("pytest")
    result = filters.filter_instance_type(
        "pytest",
        re.compile(r""),
        re.compile(r"^$"),
        re.compile(r""),
        re.compile(r"^$"),
        re.compile(r""),
        re.compile(r"^$"),
    )
    assert result is True
    assert mock_parse_ec2_it.called is True


@pytest.mark.parametrize(
    "inters_min,inters_max,inters,expected",
    [
        ((-1), 101, 6, True),
        ((-1), 10, 6, True),
        (0, 10, 6, True),
        (5, 10, 6, True),
        (5, 10, 20, False),
        ((-1), 6, 6, True),
        (6, 10, 6, True),
    ],
)
def test_filter_inters(inters_min, inters_max, inters, expected):
    """Check whether filter_inters() works as expected."""
    result = filters.filter_inters(inters, inters_min, inters_max)
    assert result is expected


@pytest.mark.parametrize(
    "savings_min,savings_max,savings,expected",
    [
        ((-1), 101, 72, True),
        ((-1), 50, 72, False),
        (72, 101, 72, True),
        (72, 80, 72, True),
        (72, 80, 80, True),
        (72, 80, 81, False),
        (72, 80, 71, False),
        (72, 80, 50, False),
    ],
)
def test_filter_savings(savings_min, savings_max, savings, expected):
    """Check whether filter_savings() works as expected."""
    result = filters.filter_savings(savings, savings_min, savings_max)
    assert result is expected


@pytest.mark.parametrize(
    "vcpu_min,vcpu_max,vcpus,expected",
    [
        ((-1), 101, 32, True),
        ((-1), 48, 32, True),
        (8, 101, 32, True),
        (8, 32, 32, True),
        (8, 32, 8, True),
        (8, 32, 7, False),
        (8, 32, 33, False),
    ],
)
def test_filter_vcpu(vcpu_min, vcpu_max, vcpus, expected):
    """Check whether filter_vcpu() works as expected."""
    result = filters.filter_vcpu(vcpus, vcpu_min, vcpu_max)
    assert result is expected


@pytest.mark.parametrize(
    "instance_type,exclude_metal,exclude_vm,expected",
    [
        ("test.metal", False, False, True),
        ("test.metal", False, True, True),
        ("test.metal", True, False, False),
        ("test.itsavm", False, True, False),
        ("test.itsavm", True, False, True),
        ("test.itsavm", False, False, True),
        # NOTE: this shouldn't be possible IRL
        ("test.metal", True, True, False),
        ("test.itsavm", True, True, False),
    ],
)
def test_include_instance_type(
    instance_type, exclude_metal, exclude_vm, expected
):
    """Check whether include_instance_type() works as expected."""
    result = filters.include_instance_type(
        instance_type,
        exclude_metal,
        exclude_vm,
    )
    assert result is expected


@pytest.mark.parametrize(
    "instance_type",
    [
        "test",
        "test.pytest.test",
    ],
)
def test_include_instance_type_exception(instance_type):
    """Test include_instance_type() when invalid instance type is given."""
    with pytest.raises(ValueError) as excinfo:
        filters.include_instance_type(instance_type, True, False)

    expected = "Unexpected instance_type '{:s}'".format(instance_type)
    assert str(excinfo.value) == expected


@pytest.mark.parametrize(
    "instance_type,expected",
    [
        (
            "mac1.metal",
            ("mac", "1", "", "metal"),
        ),
        (
            "mac2-m2.metal",
            ("mac", "2", "-m2", "metal"),
        ),
        (
            "mac2.metal",
            ("mac", "2", "", "metal"),
        ),
        (
            "mac2-m2pro.metal",
            ("mac", "2", "-m2pro", "metal"),
        ),
        (
            "mac2-m1ultra.metal",
            ("mac", "2", "-m1ultra", "metal"),
        ),
        (
            "i2.2xlarge",
            ("i", "2", "", "2xlarge"),
        ),
        (
            "u-6tb1.56xlarge",
            ("u", "0", "6tb1", "56xlarge"),
        ),
        (
            "c7i-flex.large",
            ("c", "7", "i-flex", "large"),
        ),
        (
            "inf1.24xlarge",
            ("inf", "1", "", "24xlarge"),
        ),
        (
            "u7in-32tb.224xlarge",
            ("u", "7", "in-32tb", "224xlarge"),
        ),
        (
            "t2.2xlarge",
            ("t", "2", "", "2xlarge"),
        ),
        (
            "i3en.xlarge",
            ("i", "3", "en", "xlarge"),
        ),
        (
            "r7iz.large",
            ("r", "7", "iz", "large"),
        ),
    ],
)
def test_parse_ec2_instance_type(instance_type, expected):
    """Check whether parse_ec2_instance_type() works as expected."""
    result = filters.parse_ec2_instance_type(instance_type)
    assert result == expected


@pytest.mark.parametrize(
    "instance_type,expected_message",
    [
        ("foo", "Unexpected instance_type 'foo'"),
        ("foo.bar.lar", "Unexpected instance_type 'foo.bar.lar'"),
        ("12345abc.metal", "Unable to parse instance_type '12345abc.metal'"),
    ],
)
def test_parse_ec2_instance_type_exc(instance_type, expected_message):
    """Test parse_ec2_instance_type() when invalid input is given."""
    with pytest.raises(ValueError) as excinfo:
        filters.parse_ec2_instance_type(instance_type)

    assert str(excinfo.value) == expected_message
