#!/usr/bin/env python3
"""Filtering functions for aws_spot_advisor_sejto.

2024/Nov/06 @ Zdenek Styblik
"""
import re

RE_METAL = re.compile(r"metal")


def filter_emr(emr_supported: bool, emr_only: bool) -> bool:
    """Check whether EMR has been requested and whether is supported or not."""
    if not emr_only:
        # NOTE(zstyblik): We don't care whether instance supports EMR or not.
        return True

    return emr_supported


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
