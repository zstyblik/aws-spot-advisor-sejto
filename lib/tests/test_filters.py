#!/usr/bin/env python3
"""Unit tests for aws_spot_advisor_sejto.lib.filters.py.

2024/Nov/06 @ Zdenek Styblik
"""
import pytest

from lib import filters


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
