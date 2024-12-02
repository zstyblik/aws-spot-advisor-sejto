#!/usr/bin/env python3
"""AWS Spot Advisor Sejto CLI args parsing.

2024/Dec/02 @ Zdenek Styblik
"""
import argparse
from typing import Dict


def calc_log_level(count: int) -> int:
    """Return logging log level as int based on count."""
    log_level = 40 - max(count, 0) * 10
    log_level = max(log_level, 10)
    return log_level


def parse_args(data_dir: str, dataset_url: str) -> argparse.Namespace:
    """Return parsed CLI args."""
    parser = argparse.ArgumentParser(
        allow_abbrev=False,
        description=(
            "Sejto - slightly better filtering of AWS Spot Advisor's data."
        ),
        epilog="AWS Spot Advisor Sejto by Zdenek Styblik",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="Increase log level verbosity. Can be passed multiple times.",
    )

    action_group = parser.add_mutually_exclusive_group(required=True)
    action_group.add_argument(
        "--list-regions",
        action="store_true",
        default=False,
        help="List AWS regions and available Operating Systems.",
    )
    action_group.add_argument(
        "--region",
        type=str,
        help="AWS Region.",
    )

    parser.add_argument(
        "--os",
        type=str,
        choices=["Linux", "Windows"],
        default="Linux",
        help="Operating System. Default is 'Linux'.",
    )
    parser.add_argument(
        "--output-format",
        choices=["csv", "json", "text"],
        default="text",
        help="Output format. Default is '%(default)s' format.",
    )

    filters_group = parser.add_argument_group(
        "filters",
        (
            "options for AWS Spot Advisor data filtering. "
            "NOTE that AWS provides very rough estimate of interruptions."
        ),
    )
    filters_group.add_argument(
        "--vcpu-min",
        type=int,
        default=(-1),
        help="Minimum vCPUs.",
    )
    filters_group.add_argument(
        "--vcpu-max",
        type=int,
        default=65535,
        help="Maximum vCPUs.",
    )
    filters_group.add_argument(
        "--mem-min",
        type=float,
        default=(-1),
        help="Minimum memory in GB.",
    )
    filters_group.add_argument(
        "--mem-max",
        type=float,
        default=65535,
        help="Maximum memory in GB.",
    )
    filters_group.add_argument(
        "--emr-only",
        action="store_true",
        default=False,
        help="Only instances supported by EMR.",
    )
    #
    filters_group.add_argument(
        "--inters-min",
        type=int,
        default=(-1),
        help="Minimum interruptions in percent.",
    )
    filters_group.add_argument(
        "--inters-max",
        type=int,
        default=101,
        help="Maximum interruptions in percent.",
    )
    filters_group.add_argument(
        "--savings-min",
        type=int,
        default=(-1),
        help="Minimum savings in percent.",
    )
    filters_group.add_argument(
        "--savings-max",
        type=int,
        default=101,
        help="Maximum savings in percent.",
    )
    #
    group = filters_group.add_mutually_exclusive_group()
    group.add_argument(
        "--exclude-metal",
        action="store_true",
        default=False,
        help="Exclude bare metal instances.",
    )
    group.add_argument(
        "--exclude-vm",
        action="store_true",
        default=False,
        help="Exclude Virtual Machine instances.",
    )

    sorting_group = parser.add_argument_group("sorting", None)
    sorting_group.add_argument(
        "--sort-order",
        type=str,
        default="interrupts:asc,savings:desc",
        help=(
            "Specify how to sort results. "
            "Expected format is 'columnA:sort_order,columnB:sort_order,...'. "
            "Valid columns are instance_type, vcpus, mem_gb, emr, savings, "
            "interrupts. "
            "Valid sort orders are asc or desc. "
            "Default is '%(default)s'."
        ),
    )

    others_group = parser.add_argument_group("others", None)
    others_group.add_argument(
        "--data-dir",
        type=str,
        default=data_dir,
        help=(
            "Directory where AWS Spot Advisor and config file are/will be "
            "stored."
        ),
    )
    others_group.add_argument(
        "--dataset-url",
        type=str,
        default=dataset_url,
        help="URL of AWS Spot dataset.",
    )

    args = parser.parse_args()
    args.log_level = calc_log_level(args.verbose)
    try:
        args.parsed_sort_order = parse_sort_order(args.sort_order)
        if not args.parsed_sort_order:
            raise ValueError("No sort order at all. That's impossible!")
    except ValueError as exception:
        parser.error(str(exception))

    return args


def parse_sort_order(input_data: str) -> Dict[str, int]:
    """Return parsed and processed sort order provided by user as a dictionary.

    :raises ValueError: raised on invalid data is detected.
    """
    order_lookup = {
        "asc": 1,
        "desc": (-1),
    }
    # For attribute remapping.
    column_lookup = {
        "instance_type": "instance_type",
        "vcpus": "vcpus",
        "mem_gb": "mem_gb",
        "emr": "emr",
        "savings": "savings",
        "interrupts": "inter_max",
    }
    retval = {}
    for chunk in input_data.split(","):
        if ":" not in chunk:
            raise ValueError(
                "Input format must be 'column:sort_order', not '{:s}'.".format(
                    chunk
                )
            )

        column_name, order = chunk.split(":", maxsplit=1)
        column_name = column_name.lower()
        order = order.lower()
        if column_name not in column_lookup:
            raise ValueError(
                "Column '{:s}' is invalid. Valid columns "
                "are {:s}.".format(
                    column_name,
                    ", ".join(["'{:s}'".format(key) for key in column_lookup]),
                ),
            )

        if order not in order_lookup:
            raise ValueError(
                "Sort order '{:s}' is invalid. Valid "
                "values are {:s}.".format(
                    order,
                    ", ".join(
                        ["'{:s}'".format(key) for key in order_lookup],
                    ),
                ),
            )

        column_name = column_lookup.get(column_name)
        retval[column_name] = order_lookup.get(order)

    return retval
