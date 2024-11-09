#!/usr/bin/env python3
"""Fixtures shared by pytest in AWS Spot Advisor Sejto.

2024/Nov/06 @ Zdenek Styblik
"""
import os
import tempfile

import pytest
import requests_mock


@pytest.fixture
def fixture_mock_requests():
    """Return started up requests_mock and cleanup on teardown."""
    mock_requests = requests_mock.Mocker(real_http=True)
    mock_requests.start()
    yield mock_requests

    mock_requests.stop()


@pytest.fixture
def fixture_temp_file():
    """Create tmpfile and return its file name."""
    file_desc, fname = tempfile.mkstemp()
    os.fdopen(file_desc).close()
    yield fname
    # Cleanup
    try:
        os.unlink(fname)
    except FileNotFoundError:
        pass
