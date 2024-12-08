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


# NOTE(zstyblik): class name is far from perfect, but I can't think of better
# one.
@dataclass
class EC2InstanceTypeHelper:
    """Class holds information related to AWS EC2 series/options."""

    label: str
    desc: str
    pattern: str


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

    @staticmethod
    def list_options() -> Dict[str, str]:
        """Return EC2 Instance option => description."""
        return {
            "a": EC2InstanceTypeHelper(
                label="a",
                desc="AMD processors",
                pattern=r"a",
            ),
            "b": EC2InstanceTypeHelper(
                label="b",
                desc="Block storage optimization",
                pattern=r"b",
            ),
            "d": EC2InstanceTypeHelper(
                label="d",
                desc="Instance store volumes",
                pattern=r"d",
            ),
            "e": EC2InstanceTypeHelper(
                label="e",
                desc="Extra storage or memory",
                # collides with 'flex'
                pattern=r"e(?!x)",
            ),
            "flex": EC2InstanceTypeHelper(
                label="flex",
                desc="Flex instance",
                # collides with 'e'
                pattern=r"-flex",
            ),
            "g": EC2InstanceTypeHelper(
                label="g",
                desc="AWS Graviton processors",
                pattern=r"g",
            ),
            "i": EC2InstanceTypeHelper(
                label="i",
                desc="Intel processors",
                pattern=r"i",
            ),
            "n": EC2InstanceTypeHelper(
                label="n",
                desc="Network and EBS optimized",
                pattern=r"n",
            ),
            "q": EC2InstanceTypeHelper(
                label="q",
                desc="Qualcomm inference accelerators",
                pattern=r"q",
            ),
            "z": EC2InstanceTypeHelper(
                label="z",
                desc="High performance",
                pattern=r"z",
            ),
        }

    @staticmethod
    def list_series() -> Dict[str, str]:
        """Return EC2 Instance series => description."""
        # NOTE(zstyblik): look behinds and aheads could be problematic.
        return {
            "c": EC2InstanceTypeHelper(
                label="C",
                desc="Compute optimized",
                # collides with 'Mac'
                pattern=r"(?<!ma)c",
            ),
            "d": EC2InstanceTypeHelper(
                label="D",
                desc="Dense storage",
                pattern=r"d",
            ),
            "f": EC2InstanceTypeHelper(
                label="F",
                desc="FPGA",
                # collides with 'Inf'
                pattern=r"(?<!in)f",
            ),
            "g": EC2InstanceTypeHelper(
                label="G",
                desc="Graphics intensive",
                pattern=r"g",
            ),
            "hpc": EC2InstanceTypeHelper(
                label="Hpc",
                desc="High performance computing",
                # collides with 'p', 'c'
                pattern=r"hpc",
            ),
            "im": EC2InstanceTypeHelper(
                label="Im",
                desc="Storage optimized (1 to 4 ratio of vCPU to memory)",
                # collides with 'i', 'm'
                pattern=r"im",
            ),
            "inf": EC2InstanceTypeHelper(
                label="Inf",
                desc="AWS Inferentia",
                # collides with 'i', 'f'
                pattern=r"inf",
            ),
            "is": EC2InstanceTypeHelper(
                label="Is",
                desc="Storage optimized (1 to 6 ratio of vCPU to memory)",
                # collides with 'i'
                pattern=r"is",
            ),
            "i": EC2InstanceTypeHelper(
                label="I",
                desc="Storage optimized",
                # collides with 'i*'
                pattern=r"i(?!m|nf|s)",
            ),
            "mac": EC2InstanceTypeHelper(
                label="Mac",
                desc="macOS",
                # collides with 'c', 'm'
                pattern=r"mac",
            ),
            "m": EC2InstanceTypeHelper(
                label="M",
                desc="General purpose",
                # collides with 'Mac', 'Im'
                pattern=r"(?<!i)m(?!ac)",
            ),
            "p": EC2InstanceTypeHelper(
                label="P",
                desc="GPU accelerated",
                # collides with 'Hpc'
                pattern=r"(?<!h)p(?!c)",
            ),
            "r": EC2InstanceTypeHelper(
                label="R",
                desc="Memory optimized",
                # collides with 'Trn',
                pattern=r"(?<!t)r(?!n)",
            ),
            "t": EC2InstanceTypeHelper(
                label="T",
                desc="Burstable performance",
                # collides with 'Trn', 'vt'
                pattern=r"(?<!v)t(?!rn)",
            ),
            "trn": EC2InstanceTypeHelper(
                label="Trn",
                desc="AWS Trainium",
                # collides with 't', 'r', 'vt'
                pattern=r"trn",
            ),
            "u": EC2InstanceTypeHelper(
                label="U",
                desc="High memory",
                pattern=r"u",
            ),
            "vt": EC2InstanceTypeHelper(
                label="VT",
                desc="Video transcoding",
                # collides with 't'
                pattern=r"vt",
            ),
            "x": EC2InstanceTypeHelper(
                label="X",
                desc="Memory intensive",
                pattern=r"x",
            ),
        }

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


@dataclass
class RegionDetail:
    """Class represents AWS Region with the list of supported OS-es."""

    region: str
    operating_systems: list
