#!/usr/bin/env python3
"""Unit tests for aws_spot_advisor_sejto.lib.models.py.

2024/Dec/07 @ Zdenek Styblik
"""
import re

import pytest

from aws_spot_advisor_sejto.lib import models


@pytest.mark.parametrize(
    "key,options,should_match",
    [
        ("a", "abcd", True),
        ("b", "abcd", True),
        ("d", "abcd", True),
        ("e", "iedn", True),
        ("e", "flex", False),
        ("flex", "iedn", False),
        ("flex", "a-flex", True),
        ("g", "efg", True),
        ("i", "ijk", True),
        ("n", "iedn", True),
        ("q", "jqk", True),
        ("z", "zdst", True),
    ],
)
def test_ec2it_list_options_patterns(key, options, should_match):
    """Test patterns defined in EC2InstanceType.list_options()."""
    instance_options = models.EC2InstanceType.list_options()
    instance_option = instance_options[key]
    regex = re.compile(instance_option.pattern, re.I)
    result = bool(regex.search(options))
    assert result is should_match


@pytest.mark.parametrize(
    "key,series,should_match",
    [
        ("c", "cyclone", True),
        ("c", "mac", False),
        ("d", "defense", True),
        ("f", "f", True),
        ("f", "inf", False),
        ("g", "grand", True),
        ("hpc", "hpc", True),
        ("hpc", "p", False),
        ("hpc", "c", False),
        ("im", "im", True),
        ("im", "i", False),
        ("im", "m", False),
        ("inf", "inf", True),
        ("inf", "knf", False),
        ("inf", "i", False),
        ("is", "is", True),
        ("is", "i", False),
        ("i", "iddqd", True),
        ("i", "im", False),
        ("i", "inf", False),
        ("i", "is", False),
        ("mac", "mac", True),
        ("mac", "m", False),
        ("mac", "c", False),
        ("m", "mak", True),
        ("m", "mac", False),
        ("m", "im", False),
        ("p", "apk", True),
        ("p", "hpc", False),
        ("r", "rx", True),
        ("r", "trn", False),
        ("t", "trx", True),
        ("t", "vt", False),
        ("t", "trn", False),
        ("trn", "trn", True),
        ("trn", "tvt", False),
        ("trn", "trx", False),
        ("u", "ufo", True),
        ("vt", "zvt", True),
        ("vt", "trn", False),
        ("x", "xyz", True),
    ],
)
def test_ec2it_list_series_patterns(key, series, should_match):
    """Test patterns defined in EC2InstanceType.list_series()."""
    instance_series = models.EC2InstanceType.list_series()
    instance_series = instance_series[key]
    regex = re.compile(instance_series.pattern, re.I)
    result = bool(regex.search(series))
    assert result is should_match
