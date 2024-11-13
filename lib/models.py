#!/usr/bin/env python3
"""Data models for AWS Spot Advisor Sejto.

NOTE(zstyblik): to call this models, let alone data models, is rather far
fetched.

2024/Nov/13 @ Zdenek Styblik
"""
from dataclasses import dataclass
from dataclasses import field
from typing import Any
from typing import Dict


@dataclass
class EC2InstanceType:
    """Class represents AWS EC2 Instance Type."""

    instance_type: str
    vcpus: int = field(default=0)
    mem_gb: float = field(default=0)
    emr: bool = field(default=False)
    savings: int = field(default=0)
    inter_label: str = field(default="")
    inter_max: int = field(default=0)

    def print_dict(self) -> Dict[str, Any]:
        """Return some attributes as dict.

        This is in order to control what gets into JSON and as unfortunate as it
        is, this is the best solution I could come up with.
        """
        return {
            "instance_type": self.instance_type,
            "vcpus": self.vcpus,
            "mem_gb": self.mem_gb,
            "emr": self.emr,
            "savings": self.savings,
            "interrupts": self.inter_label,
        }
