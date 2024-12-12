#!/usr/bin/env python3
"""AWS Spot Advisor Sejto CLI args parsing.

2024/Dec/02 @ Zdenek Styblik
"""
import argparse
import re
from typing import Dict
from typing import List

from .models import EC2InstanceType


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
        "--list-instance-options",
        action="store_true",
        default=False,
        help="Show supported AWS EC2 instance options.",
    )
    action_group.add_argument(
        "--list-instance-series",
        action="store_true",
        default=False,
        help="Show supported AWS EC2 instance series.",
    )
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
    #
    filter_instance_series_group = parser.add_argument_group(
        "filter by instance series",
    )
    filter_instance_series_group.add_argument(
        "--exclude-instance-series",
        action="extend",
        nargs="+",
        help="Exclude instances of listed series.",
    )
    filter_instance_series_group.add_argument(
        "--include-instance-series",
        action="extend",
        nargs="+",
        help="ONLY instances of listed series will be included.",
    )
    #
    filter_instance_gen_group = parser.add_argument_group(
        "filter by instance generation",
    )
    filter_instance_gen_group.add_argument(
        "--include-instance-generations",
        action="extend",
        nargs="+",
        help="ONLY listed instance generation(s) will be included.",
    )
    filter_instance_gen_group.add_argument(
        "--exclude-instance-generations",
        action="extend",
        nargs="+",
        help="Exclude listed instance generation(s).",
    )
    #
    filter_instance_opts_group = parser.add_argument_group(
        "filter by instance options",
    )
    filter_instance_opts_group.add_argument(
        "--exclude-instance-options",
        action="extend",
        nargs="+",
        help="Exclude instances with listed options.",
    )
    filter_instance_opts_group.add_argument(
        "--include-instance-options",
        action="extend",
        nargs="+",
        help="ONLY instances with listed options will be included.",
    )
    #
    others_group = parser.add_argument_group("others", None)
    others_group.add_argument(
        "--data-dir",
        type=str,
        default=data_dir,
        help=(
            "Directory where AWS Spot Advisor's data and configuration file "
            "will be stored. Defaults is '%(default)s'."
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

        args.re_exclude_instance_series = parse_instance_series(
            args.exclude_instance_series
        )
        args.re_include_instance_series = parse_instance_series(
            args.include_instance_series
        )
        #
        args.re_exclude_instance_generations = parse_instance_generations(
            args.exclude_instance_generations
        )
        args.re_include_instance_generations = parse_instance_generations(
            args.include_instance_generations
        )
        #
        args.re_exclude_instance_options = parse_instance_options(
            args.exclude_instance_options
        )
        args.re_include_instance_options = parse_instance_options(
            args.include_instance_options
        )
    except ValueError as exception:
        parser.error(str(exception))

    return args


def parse_instance_generations(input_data: List[str]) -> re.Pattern | None:
    """Return parsed EC2 instance generations as a compiled regex.

    :raises ValueError: raised when invalid data is detected.
    """
    if not input_data:
        return None

    errors = set()
    retval = set()
    for item in input_data:
        for chunk in item.split(","):
            try:
                value = int(chunk)
                if value < 1:
                    raise ValueError

                retval.add(chunk)
            except Exception:
                errors.add(chunk)

    if errors:
        raise ValueError(
            "Unsupported EC2 instance generations '{:s}'".format(
                ",".join(sorted(errors))
            )
        )

    re_gens = re.compile("|".join(sorted(retval)), re.I)
    return re_gens


def parse_instance_options(input_data: List[str]) -> re.Pattern | None:
    """Return parsed EC2 instance options as a compiled regex.

    :raises ValueError: raised when invalid data is detected.
    """
    if not input_data:
        return None

    options = EC2InstanceType.list_options()
    valid_options = {key.lower() for key in options}
    desired_options = {
        chunk.lower() for item in input_data for chunk in item.split(",")
    }
    diff = desired_options - valid_options
    if diff:
        raise ValueError(
            "Unsupported EC2 instance options '{:s}'".format(
                ",".join(sorted(diff))
            )
        )

    options_patterns = [options[opt_key].pattern for opt_key in desired_options]
    re_options = re.compile("|".join(sorted(options_patterns)), re.I)
    return re_options


def parse_instance_series(input_data: List[str]) -> re.Pattern | None:
    """Return parsed EC2 instance series as a compiled regex.

    :raises ValueError: raised when invalid data is detected.
    """
    if not input_data:
        return None

    series = EC2InstanceType.list_series()
    valid_series = {key.lower() for key in series}
    desired_series = {
        chunk.lower() for item in input_data for chunk in item.split(",")
    }
    diff = desired_series - valid_series
    if diff:
        raise ValueError(
            "Unsupported EC2 instance series '{:s}'".format(
                ",".join(sorted(diff))
            )
        )

    series_patterns = [
        series[series_key].pattern for series_key in desired_series
    ]
    re_series = re.compile("|".join(sorted(series_patterns)), re.I)
    return re_series


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
