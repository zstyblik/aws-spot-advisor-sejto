#!/usr/bin/env python3
"""Code related to output formatting for AWS Spot Advisor Sejto.

2024/Nov/14 @ Zdenek Styblik
"""
import csv
import dataclasses
import json
from collections.abc import Callable
from typing import Dict
from typing import IO

from .models import EC2InstanceType


class SejtoJSONEncoder(json.JSONEncoder):
    """Custom JSON Encoder in order to serialize Sejto's data."""

    def default(self, o):
        """Return a serializable object for `o` or call base implementation."""
        if isinstance(o, EC2InstanceType):
            return o.print_dict()

        if dataclasses.is_dataclass(o):
            return dataclasses.asdict(o)

        return super().default(o)


def fmt_csv(
    results: Dict[str, EC2InstanceType], fhandle: IO, sorting_fn: Callable
) -> None:
    """Write results into given file handle in CSV format."""
    # NOTE(zstyblik): we need to get fieldnames somehow.
    fake_instance = EC2InstanceType(instance_type="fake")
    fields = fake_instance.print_dict()
    writer = csv.DictWriter(
        fhandle,
        fields,
        extrasaction="ignore",
    )
    writer.writeheader()
    for instance_type in sorted(results.values(), key=sorting_fn):
        writer.writerow(instance_type.print_dict())


def fmt_json(
    results: Dict[str, EC2InstanceType], fhandle: IO, sorting_fn: Callable
) -> None:
    """Write results into given file handle in JSON format."""
    json.dump(
        list(sorted(results.values(), key=sorting_fn)),
        fhandle,
        indent=4,
        cls=SejtoJSONEncoder,
    )


def fmt_text(
    results: Dict[str, EC2InstanceType], fhandle: IO, sorting_fn: Callable
) -> None:
    """Write results into given file handle in text format."""
    if not results:
        print("", file=fhandle)
        return

    for instance_type in sorted(results.values(), key=sorting_fn):
        print(
            "instance_type={instance_type:s} vcpus={vcpus:d} "
            "mem_gb={mem_gb:.1f} savings={savings:d}% "
            "interrupts={interrupts:s}".format(**instance_type.print_dict()),
            file=fhandle,
        )
