#!/usr/bin/env python3
"""Filtering functions for aws_spot_advisor_sejto.

2024/Nov/06 @ Zdenek Styblik
"""
import re

# NOTE(zstyblik): eg. 'c7i-flex'
RE_EC2IT1 = re.compile(r"^(?P<series>[a-z]+)(?P<gen>[0-9]+)(?P<opts>.*)", re.I)
# NOTE(zstyblik): eg. 'u-6tb1'
RE_EC2IT2 = re.compile(r"^(?P<series>[a-z]+)\-(?P<opts>.+)", re.I)
RE_METAL = re.compile(r"metal")


def filter_by_regex(
    input_data: str,
    re_exclude: re.Pattern | None,
    re_include: re.Pattern | None,
) -> bool:
    """Filter input data by regex.

    Return True when data should be kept, False means data should be discarded.
    If re_include matches, then function returns and re_exclude is skipped.
    """
    if re_include:
        if re_include.search(input_data):
            return True

        return False

    if re_exclude and re_exclude.search(input_data):
        return False

    return True


def filter_emr(emr_supported: bool, emr_only: bool) -> bool:
    """Check whether EMR has been requested and whether is supported or not."""
    if not emr_only:
        # NOTE(zstyblik): We don't care whether instance supports EMR or not.
        return True

    return emr_supported


def filter_instance_type(
    instance_type: str,
    re_exclude_instance_series: re.Pattern | None,
    re_include_instance_series: re.Pattern | None,
    re_exclude_instance_generations: re.Pattern | None,
    re_include_instance_generations: re.Pattern | None,
    re_exclude_instance_options: re.Pattern | None,
    re_include_instance_options: re.Pattern | None,
) -> bool:
    """Filter EC2 instance type by series, generation and options.

    If either of series, generation or options should be excluded, then the
    whole EC2 instance should be excluded, resp. function will return False.
    """
    try:
        series, gen, options, _ = parse_ec2_instance_type(instance_type)
    except ValueError:
        return True

    keep_series = filter_by_regex(
        series,
        re_exclude_instance_series,
        re_include_instance_series,
    )
    keep_gen = filter_by_regex(
        gen,
        re_exclude_instance_generations,
        re_include_instance_generations,
    )
    keep_options = filter_by_regex(
        options,
        re_exclude_instance_options,
        re_include_instance_options,
    )
    if not keep_series or not keep_gen or not keep_options:
        return False

    return True


def filter_inters(inters: int, inters_min: int, inters_max: int) -> bool:
    """Check whether interruptions are within limits or not."""
    if int(inters) >= inters_min and int(inters) <= inters_max:
        return True

    return False


def filter_mem(mem_gb: float, mem_min: float, mem_max: float) -> bool:
    """Check whether memory is within limits or not."""
    if mem_gb >= mem_min and mem_gb <= mem_max:
        return True

    return False


def filter_savings(savings: int, savings_min: int, savings_max: int) -> bool:
    """Check whether savings(pct) are within limits or not."""
    if int(savings) >= savings_min and int(savings) <= savings_max:
        return True

    return False


def filter_vcpu(vcpus: int, vcpu_min: int, vcpu_max: int) -> bool:
    """Check whether vCPUs are within limits or not."""
    if vcpus >= vcpu_min and vcpus <= vcpu_max:
        return True

    return False


def include_instance_type(
    instance_type: str, exclude_metal: bool, exclude_vm: bool
):
    """Based on args, decide whether instance should be discarded or kept.

    Returns False if instance should be discarded, otherwise returns True.
    """
    if not exclude_metal and not exclude_vm:
        # NOTE(zstyblik): No need to check anything, include everything.
        return True

    # NOTE(zstyblik): expected instance_type "c7gn.2xlarge"
    splitted = instance_type.split(".")
    if len(splitted) != 2:
        raise ValueError(
            "Unexpected instance_type '{:s}'".format(instance_type)
        )

    is_metal = RE_METAL.search(splitted[1])
    if is_metal and exclude_metal:
        # Filter out Bare Metal instances.
        return False

    if not is_metal and exclude_vm:
        # Filter out VM instances.
        return False

    return True


def parse_ec2_instance_type(instance_type: str) -> tuple[str, str, str, str]:
    """Disassemble EC2 Instance Type into series, generation and options.

    :raises ValueError: on invalid data
    """
    splitted = instance_type.split(".")
    if len(splitted) != 2:
        raise ValueError(
            "Unexpected instance_type '{:s}'".format(instance_type)
        )

    match = RE_EC2IT1.search(splitted[0])
    if not match:
        match = RE_EC2IT2.search(splitted[0])

    if not match:
        raise ValueError(
            "Unable to parse instance_type '{:s}'".format(instance_type)
        )

    match_dict = match.groupdict()
    series = match_dict.get("series", "")
    gen = match_dict.get("gen", "0")
    opts = match_dict.get("opts", "")
    size = splitted[1]
    return (series.lower(), gen, opts.lower(), size.lower())
