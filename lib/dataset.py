#!/usr/bin/env python3
"""Code related to handling data for AWS Spot Advisor Sejto.

2024/Nov/06 @ Zdenek Styblik
"""
import hashlib
import json
import logging
import traceback
from dataclasses import dataclass
from dataclasses import field
from typing import Dict

import requests

HTTP_TIMEOUT = 30  # seconds

module_logger = logging.getLogger("aws_spot_advisor_sejto.lib.dataset")


@dataclass
class DataSet:
    """Class represents data source with related attributes and data."""

    data: dict = field(default_factory=dict)
    data_fname: str = field(default_factory=str)
    data_checksum: str = field(default_factory=str)
    http_etag: str = field(default_factory=str)
    http_last_modified: str = field(default_factory=str)

    def calc_checksum(self, digest: str = "sha256") -> str:
        """Return SHA256 of dataset file.

        If SHA256 cannot be calculated, return an empty string.
        NOTE that `digest` arg is ignored and defaults to SHA256 for now.
        """
        digest = "sha256"
        try:
            with open(self.data_fname, "rb") as fhandle:
                digest = hashlib.file_digest(fhandle, digest)
        except Exception:
            module_logger.error(
                "Failed to calc SHA256 of '%s' due to: %s",
                self.data_fname,
                traceback.format_exc(),
            )
            return ""

        return digest.hexdigest()

    def check_checksum(self) -> bool:
        """Check whether checksum of local data matches expected checksum."""
        if not self.data_checksum:
            return False

        calculated_checksum = self.calc_checksum()
        if calculated_checksum != self.data_checksum:
            return False

        return True

    def extract_caching_headers(self, headers: Dict[str, str]) -> None:
        """Extract cache related headers from given dict."""
        self.http_etag = ""
        self.http_last_modified = ""
        for key, value in headers.items():
            key = key.lower()
            if key == "etag":
                self.http_etag = str(value)
            elif key == "last-modified":
                self.http_last_modified = str(value)

    def has_os(self, region: str, os_name: str) -> bool:
        """Check whether given OS is available in given region."""
        if (
            "spot_advisor" in self.data
            and region in self.data["spot_advisor"]
            and os_name in self.data["spot_advisor"][region]
        ):
            return True

        return False

    def has_region(self, region: str) -> bool:
        """Check whether given region exists/is available."""
        if "spot_advisor" in self.data and region in self.data["spot_advisor"]:
            return True

        return False

    def make_caching_headers(self) -> Dict[str, str]:
        """Return cache related headers as a dict."""
        headers = {}
        if self.http_etag:
            headers["if-none-match"] = self.http_etag

        if self.http_last_modified:
            headers["if-modified-since"] = self.http_last_modified

        return headers

    def update(
        self, url: str, http_timeout: int = HTTP_TIMEOUT, is_retry: bool = False
    ) -> None:
        """Update data.

        Check whether anything has changed on remote end. If so, write new data
        to local disk. If not so, load data from local disk.

        This function might raise OSError or requests' related exceptions.

        :raises requests.exceptions.BaseHTTPError: when fetching data over HTTP
        :raises OSError: when reading/writing data
        :raises ValueError: if HTTP Status code isn't 200 or 304
        """
        caching_headers = self.make_caching_headers()
        is_valid = self.check_checksum()
        if not is_valid:
            # NOTE(zstyblik): dataset is invalid -> drop headers, fetch fresh
            # dataset.
            module_logger.debug(
                "Dataset '%s' SHA256 checksum mismatch - fetch fresh data.",
                self.data_fname,
            )
            caching_headers = {}

        rsp = get_data(url, timeout=http_timeout, extra_headers=caching_headers)
        if rsp.status_code == 304:
            module_logger.debug(
                "No change in data - data from local disk will be used."
            )
            try:
                with open(self.data_fname, "r", encoding="utf-8") as fhandle:
                    self.data = json.load(fhandle)
            except FileNotFoundError as exception:
                # NOTE(zstyblik): not the best solution, but it's late, I'm
                # tired and this (retry path) was the last minute find/idea.
                # Idea with `is_retry` is to guard against 304-loop.
                if is_retry:
                    raise RecursionError from exception

                module_logger.error(
                    "Data file '%s' doesn't exist - trying to fetch fresh data",
                    self.data_fname,
                )
                self.http_etag = ""
                self.http_last_modified = ""
                self.data_checksum = ""
                self.update(url=url, http_timeout=http_timeout, is_retry=True)
        elif rsp.status_code == 200:
            module_logger.debug(
                "Change in data detected - overwrite local copy."
            )
            self.data = rsp.json()
            with open(self.data_fname, "w", encoding="utf-8") as fhandle:
                json.dump(self.data, fhandle)

            self.data_checksum = self.calc_checksum()
        else:
            raise ValueError(
                "Unexpected HTTP Status Code '{:s}'".format(rsp.status_code)
            )

        self.extract_caching_headers(rsp.headers)


def get_data(
    url: str,
    timeout: int = HTTP_TIMEOUT,
    extra_headers: Dict = None,
) -> requests.models.Response:
    """Fetch data over HTTP and return response."""
    user_agent = "aws-spot-advisor-sejto"
    headers = {"User-Agent": user_agent}
    if extra_headers:
        for key, value in extra_headers.items():
            headers[key] = value

    module_logger.debug("HTTP req GET %s", url)
    module_logger.debug("HTTP req Headers %s", headers)
    rsp = requests.get(url, timeout=timeout, headers=headers)
    module_logger.debug("HTTP rsp Status Code: %i", rsp.status_code)
    module_logger.debug("HTTP rsp Headers: %s", rsp.headers)
    return rsp
