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

from lib import conf
from lib import filters
from lib.dataset import DataSet

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
    """Return AWS Spot Advisor dataset."""
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


def main():
    """Get data, filter data and print results."""
    args = parse_args()
    logging.basicConfig(level=args.log_level, stream=sys.stderr)
    logger = logging.getLogger("aws_spot_advisor_sejto")

    config_fpath = os.path.join(args.data_dir, CONFIG_FNAME)
    logger.debug("Config file '%s'.", config_fpath)

    dataset_fpath = os.path.join(args.data_dir, DATASET_FNAME)
    logger.debug("Dataset file '%s'.", dataset_fpath)

    dataset = get_dataset(config_fpath, dataset_fpath, args.dataset_url)
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

    print_out(results)


def parse_args() -> argparse.Namespace:
    """Return parsed CLI args."""
    parser = argparse.ArgumentParser(
        allow_abbrev=False,
        epilog="NOTE that AWS provides very rough estimate of interruptions.",
    )
    parser.add_argument(
        "--region",
        type=str,
        required=True,
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
        "--vcpu-min",
        type=int,
        default=(-1),
        help="Minimum vCPUs.",
    )
    parser.add_argument(
        "--vcpu-max",
        type=int,
        default=65535,
        help="Maximum vCPUs.",
    )
    parser.add_argument(
        "--mem-min",
        type=float,
        default=(-1),
        help="Minimum memory in GB.",
    )
    parser.add_argument(
        "--mem-max",
        type=float,
        default=65535,
        help="Maximum memory in GB.",
    )
    parser.add_argument(
        "--emr-only",
        action="store_true",
        default=False,
        help="Only instances supported by EMR.",
    )
    #
    parser.add_argument(
        "--inters-min",
        type=int,
        default=(-1),
        help="Minimum interruptions in percent.",
    )
    parser.add_argument(
        "--inters-max",
        type=int,
        default=101,
        help="Maximum interruptions in percent.",
    )
    parser.add_argument(
        "--savings-min",
        type=int,
        default=(-1),
        help="Minimum savings in percent.",
    )
    parser.add_argument(
        "--savings-max",
        type=int,
        default=101,
        help="Maximum savings in percent.",
    )
    #
    group = parser.add_mutually_exclusive_group()
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
    parser.add_argument(
        "--data-dir",
        type=str,
        default=DATA_DIR,
        help=(
            "Directory where AWS Spot Advisor and config file are/will be "
            "stored."
        ),
    )
    parser.add_argument(
        "--dataset-url",
        type=str,
        default=DATASET_URL,
        help="URL of AWS Spot dataset.",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="count",
        default=0,
        help="Increase log level verbosity. Can be passed multiple times.",
    )

    args = parser.parse_args()
    args.log_level = calc_log_level(args.verbose)
    return args


def print_out(results) -> None:
    """Print out results."""
    # NOTE(zstyblik): notice minus sign inside sorted!!!
    for value in sorted(
        results.values(), key=lambda x: (x["inter_max"], (-1) * x["savings"])
    ):
        print(
            "instance_type={:s} vcpus={:d} mem_gb={:.1f} savings={:d}% "
            "interrupts={:s}".format(
                value["instance_type"],
                value["cores"],
                value["ram_gb"],
                value["savings"],
                value["inter_label"],
            )
        )


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
        key: values
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

        extra_data = {
            "savings": int(available_instances[key]["s"]),
            "inter_label": interrupts[inter_range]["label"],
            "inter_max": int(interrupts[inter_range]["max"]),
        }
        results[key].update(extra_data)
        results[key].update({"instance_type": key})

    return results


if __name__ == "__main__":
    main()
