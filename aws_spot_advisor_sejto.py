#!/usr/bin/env python3
"""Sejto is a script for filtering AWS Spot Advisor data.

AWS Spot Advisor Sejto aims to provide a bit better filtering capabilities than
AWS Spot Advisor's web site.

2024/Nov/06 @ Zdenek Styblik
"""
import argparse
import logging
import os
import sys
from typing import Any
from typing import Dict

from requests.exceptions import BaseHTTPError

from lib import conf
from lib import filters
from lib import formatters
from lib.dataset import DataSet
from lib.models import EC2InstanceType
from lib.models import RegionDetail

CONFIG_FNAME = "aws_spot_advisor_sejto.ini"
DATA_DIR = os.path.dirname(os.path.realpath(__file__))
DATASET_FNAME = "spot-advisor-data.json"
DATASET_URL = "https://spot-bid-advisor.s3.amazonaws.com/spot-advisor-data.json"


class DataProcessingException(Exception):
    """Custom exception in order to signal problem with data processing."""

    def __init__(self, *args, **kwargs):
        """Init."""
        super().__init__(*args)
        self.message = kwargs.get("message")


def calc_log_level(count: int) -> int:
    """Return logging log level as int based on count."""
    log_level = 40 - max(count, 0) * 10
    log_level = max(log_level, 10)
    return log_level


def get_dataset(
    config_fpath: str, dataset_fpath: str, dataset_url: str
) -> DataSet:
    """Return AWS Spot Advisor dataset.

    :raises requests.exceptions.BaseHTTPError: when fetching data over HTTP
    :raises OSError: when reading/writing data
    """
    config = conf.new()
    _ = config.read(config_fpath)

    dataset = DataSet(
        data_fname=dataset_fpath,
        data_checksum=config.get("spot_advisor", "data_checksum"),
        http_etag=config.get("spot_advisor", "http_etag"),
        http_last_modified=config.get("spot_advisor", "http_last_modified"),
    )
    dataset.update(dataset_url)
    # TODO(zstyblik): "hide" this either into dataset itself or config.
    config.set(
        "spot_advisor", "data_checksum", value=str(dataset.data_checksum)
    )
    config.set("spot_advisor", "http_etag", value=str(dataset.http_etag))
    config.set(
        "spot_advisor",
        "http_last_modified",
        value=str(dataset.http_last_modified),
    )
    conf.write(config, config_fpath)
    return dataset


def get_sorting_function(sort_order: Dict[str, int]):
    """Return function for sorting."""

    def sorter(instance_type: EC2InstanceType):
        """Make EC2InstanceType sortable."""
        return tuple(
            (
                value * getattr(instance_type, key)
                for key, value in sort_order.items()
            )
        )

    return sorter


def list_regions(dataset: DataSet, output_format: str) -> None:
    """Print AWS regions and available OS-es in these regions."""
    results = {
        region: RegionDetail(
            region=region,
            operating_systems=sorted(
                list(dataset.data["spot_advisor"][region].keys())
            ),
        )
        for region in dataset.data["spot_advisor"]
    }
    formatter = formatters.RegionDetailFormatter(
        output_format,
        sys.stdout,
        sorting_fn=lambda region_detail: region_detail.region,
    )
    formatter.fmt(results)


def main():
    """Get data, filter data and print results."""
    args = parse_args(DATA_DIR, DATASET_URL)
    logging.basicConfig(level=args.log_level, stream=sys.stderr)
    logger = logging.getLogger("aws_spot_advisor_sejto")

    config_fpath = os.path.join(args.data_dir, CONFIG_FNAME)
    logger.debug("Config file '%s'.", config_fpath)

    dataset_fpath = os.path.join(args.data_dir, DATASET_FNAME)
    logger.debug("Dataset file '%s'.", dataset_fpath)

    try:
        dataset = get_dataset(config_fpath, dataset_fpath, args.dataset_url)
    except (BaseHTTPError, OSError) as exception:
        logger.error(
            "Failed to get AWS Spot Advisor data due to exception: %s",
            exception,
            exc_info=1,
        )
        sys.exit(1)

    if args.list_regions:
        list_regions(dataset, args.output_format)
    elif args.region:
        if not dataset.has_region(args.region):
            logger.error("Region '%s' not found in data.", args.region)
            sys.exit(1)

        if not dataset.has_os(args.region, args.os):
            logger.error(
                "OS '%s' is not available in region '%s'.",
                args.os,
                args.region,
            )
            sys.exit(1)

        try:
            results = select_data(dataset.data, args)
        except DataProcessingException as exception:
            logger.error("%s", exception.message)
            sys.exit(1)

        sorter = get_sorting_function(args.parsed_sort_order)
        formatter = formatters.EC2InstanceTypeFormatter(
            output_format=args.output_format,
            fhandle=sys.stdout,
            sorting_fn=sorter,
        )
        formatter.fmt(results)
    else:
        logger.error("No action given and I don't know what to do.")
        sys.exit(1)


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


def select_data(
    data: Dict[Any, Any],
    args: argparse.Namespace,
) -> Dict[Any, Any]:
    """Selet data from dataset based on filters and return results.

    :raises DataProcessingException: if interrupt range cannot be found
    """
    # NOTE(zstyblik): turn list of interrupt ranges into lookup table.
    interrupts = {
        int(inter_range["index"]): inter_range for inter_range in data["ranges"]
    }
    # NOTE(zstyblik): pre-filter instances based on region, OS, savings, inters
    available_instances = {
        key: value
        for key, value in data["spot_advisor"][args.region][args.os].items()
        if (
            filters.filter_savings(
                value["s"], args.savings_min, args.savings_max
            )
            and filters.filter_inters(
                interrupts[value["r"]]["max"], args.inters_min, args.inters_max
            )
        )
    }
    # NOTE(zstyblik): filter on pre-filter results, vCPUs, RAM, EMR
    results = {
        key: EC2InstanceType(
            instance_type=key,
            emr=values["emr"],
            vcpus=values["cores"],
            mem_gb=values["ram_gb"],
        )
        for key, values in data["instance_types"].items()
        if (
            key in available_instances
            and filters.include_instance_type(
                key, args.exclude_metal, args.exclude_vm
            )
            and filters.filter_vcpu(
                int(values["cores"]), args.vcpu_min, args.vcpu_max
            )
            and filters.filter_mem(
                float(values["ram_gb"]), args.mem_min, args.mem_max
            )
            and filters.filter_emr(values["emr"], args.emr_only)
        )
    }
    # NOTE(zstyblik): enhance results with savings and interrupts data
    # data['spot_advisor'][...]: {'s': 86, 'r': 1}
    # data['ranges']: {'index': 0, 'label': '<5%', 'dots': 0, 'max': 5}
    for key in results.keys():
        inter_range = int(available_instances[key]["r"])
        if inter_range not in interrupts:
            message = (
                "Interrupt range '{:s}' for instance '{:s}', OS '{:s}', "
                "region '{:s}' is missing."
            ).format(
                inter_range,
                key,
                args.os,
                args.region,
            )
            raise DataProcessingException(message=message)

        # NOTE(zstyblik): savings can be(= tested it) moved into previous loop.
        results[key].savings = int(available_instances[key]["s"])
        # NOTE(zstyblik): re-think how to move these elsewhere(lookup function,
        # pre-process data etc.) and get rid off this whole loop.
        results[key].inter_label = interrupts[inter_range]["label"]
        results[key].inter_max = int(interrupts[inter_range]["max"])

    return results


if __name__ == "__main__":
    main()
