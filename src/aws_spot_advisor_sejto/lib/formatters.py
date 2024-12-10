#!/usr/bin/env python3
"""Code related to output formatting for AWS Spot Advisor Sejto.

2024/Nov/14 @ Zdenek Styblik
"""
import csv
import dataclasses
import json
from collections.abc import Callable
from typing import Any
from typing import Dict
from typing import IO

from .models import EC2InstanceType
from .models import RegionDetail


class SejtoJSONEncoder(json.JSONEncoder):
    """Custom JSON Encoder in order to serialize Sejto's data."""

    def default(self, o):
        """Return a serializable object for `o` or call base implementation."""
        if isinstance(o, EC2InstanceType):
            return o.print_dict()

        if dataclasses.is_dataclass(o):
            return dataclasses.asdict(o)

        return super().default(o)


class SejtoBaseFormatter:
    """Base formatter class for Sejto."""

    def __init__(self, output_format: str, fhandle: IO, sorting_fn: Callable):
        """Init."""
        self.output_formats = {
            "csv": self.fmt_csv,
            "json": self.fmt_json,
            "text": self.fmt_text,
        }
        self.output_format = output_format
        self.fhandle = fhandle
        self.sorting_fn = sorting_fn

    @property
    def output_format(self):
        """Defines in which format results will be printed out.

        :raises ValueError: on unsupported or invalid format
        """
        return self.__output_format

    @output_format.setter
    def output_format(self, val: str):
        """Setter for output format."""
        if val not in self.output_formats:
            raise ValueError("Output format '{}' is not supported".format(val))

        self.__output_format = val

    def fmt(self, results: Dict[str, RegionDetail]) -> None:
        """Format results.

        Results will be written into `self.fhandle` in format specified by
        `self.output_format`.
        """
        print_fn = self.output_formats.get(self.output_format)
        print_fn(results)

    def fmt_csv(self, results: Any):
        """Write results in CSV format - not implemented in base class."""
        raise NotImplementedError

    def fmt_json(self, results: Any):
        """Write results in CSV format - not implemented in base class."""
        raise NotImplementedError

    def fmt_text(self, results: Any):
        """Write results in CSV format - not implemented in base class."""
        raise NotImplementedError


class EC2InstanceTypeFormatter(SejtoBaseFormatter):
    """Formatter for EC2InstanceType results."""

    def fmt(self, results: Dict[str, EC2InstanceType]) -> None:
        """Format results.

        Results will be written into `self.fhandle` in format specified by
        `self.output_format`.
        """
        print_fn = self.output_formats.get(self.output_format)
        print_fn(results)

    def fmt_csv(self, results: Dict[str, EC2InstanceType]) -> None:
        """Write results in CSV format."""
        # NOTE(zstyblik): we need to get fieldnames somehow.
        fake_instance = EC2InstanceType(instance_type="fake")
        fields = fake_instance.print_dict()
        writer = csv.DictWriter(
            self.fhandle,
            fields,
            extrasaction="ignore",
        )
        writer.writeheader()
        for instance_type in sorted(results.values(), key=self.sorting_fn):
            writer.writerow(instance_type.print_dict())

    def fmt_json(self, results: Dict[str, EC2InstanceType]) -> None:
        """Write results in JSON format."""
        json.dump(
            list(sorted(results.values(), key=self.sorting_fn)),
            self.fhandle,
            indent=4,
            cls=SejtoJSONEncoder,
        )

    def fmt_text(self, results: Dict[str, EC2InstanceType]) -> None:
        """Write results in text format."""
        if not results:
            print("", file=self.fhandle)
            return

        for instance_type in sorted(results.values(), key=self.sorting_fn):
            print(
                "instance_type={instance_type:s} vcpus={vcpus:d} "
                "mem_gb={mem_gb:.1f} savings={savings:d}% "
                "interrupts={interrupts:s}".format(
                    **instance_type.print_dict()
                ),
                file=self.fhandle,
            )


class RegionDetailFormatter(SejtoBaseFormatter):
    """Formatter for RegionDetail results."""

    csv_fields = ["region", "operating_systems"]

    def fmt(self, results: Dict[str, RegionDetail]) -> None:
        """Format results.

        Results will be written into `self.fhandle` in format specified by
        `self.output_format`.
        """
        print_fn = self.output_formats.get(self.output_format)
        print_fn(results)

    def fmt_csv(self, results: Dict[str, RegionDetail]) -> None:
        """Write results in CSV format."""
        writer = csv.DictWriter(
            self.fhandle,
            self.csv_fields,
            extrasaction="ignore",
        )
        writer.writeheader()
        for region in sorted(results.values(), key=self.sorting_fn):
            writer.writerow(
                {
                    "region": region.region,
                    "operating_systems": ",".join(region.operating_systems),
                }
            )

    def fmt_json(self, results: Dict[str, RegionDetail]) -> None:
        """Write results in JSON format."""
        json.dump(
            list(sorted(results.values(), key=self.sorting_fn)),
            self.fhandle,
            indent=4,
            sort_keys=True,
            cls=SejtoJSONEncoder,
        )

    def fmt_text(self, results: Dict[str, RegionDetail]) -> None:
        """Write results in text format."""
        if not results:
            print("", file=self.fhandle)
            return

        for region in sorted(results.values(), key=self.sorting_fn):
            print(
                "region={region:s} "
                "operating_systems={operating_systems:s}".format(
                    region=region.region,
                    operating_systems=",".join(region.operating_systems),
                ),
                file=self.fhandle,
            )
