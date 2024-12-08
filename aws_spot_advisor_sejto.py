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
from typing import IO

from requests.exceptions import BaseHTTPError

from lib import cli_args
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


def list_ec2_instance_options(fhandle: IO):
    """List supported EC2 instance options."""
    ec2_options = EC2InstanceType.list_options()
    for option in ec2_options.values():
        print("{:s}: {:s}".format(option.label, option.desc), file=fhandle)


def list_ec2_instance_series(fhandle: IO):
    """List supported EC2 instance series."""
    ec2_series = EC2InstanceType.list_series()
    for series in ec2_series.values():
        print("{:s}: {:s}".format(series.label, series.desc), file=fhandle)


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
    args = cli_args.parse_args(DATA_DIR, DATASET_URL)
    logging.basicConfig(level=args.log_level, stream=sys.stderr)
    logger = logging.getLogger("aws_spot_advisor_sejto")

    if args.list_instance_options:
        list_ec2_instance_options(sys.stdout)
        sys.exit(0)

    if args.list_instance_series:
        list_ec2_instance_series(sys.stdout)
        sys.exit(0)

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
            and filters.filter_instance_type(
                key,
                args.re_exclude_instance_series,
                args.re_include_instance_series,
                args.re_exclude_instance_generations,
                args.re_include_instance_generations,
                args.re_exclude_instance_options,
                args.re_include_instance_options,
            )
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
