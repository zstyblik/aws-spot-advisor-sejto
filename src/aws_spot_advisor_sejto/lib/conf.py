#!/usr/bin/env python3
"""AWS Spot Advisor Sejto config helpers.

2024/Nov/06 @ Zdenek Styblik
"""
import configparser
from typing import Dict
from typing import List


def layout() -> Dict[str, List]:
    """Return desired/default layout of config file."""
    return {
        "spot_advisor": [
            "data_checksum",
            "http_etag",
            "http_last_modified",
        ]
    }


def new() -> configparser.ConfigParser:
    """Return initialized and empty instance of ConfigParser."""
    config_layout = layout()
    config = configparser.ConfigParser()
    for section, options in config_layout.items():
        config.add_section(section)
        for option in options:
            config.set(section, option, value="")

    return config


def write(config: configparser.ConfigParser, fname: str):
    """Write config into file(just a wrapper, really)."""
    with open(fname, "w", encoding="utf-8") as fhandle:
        config.write(fhandle)
