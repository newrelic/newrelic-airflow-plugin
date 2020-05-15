# Copyright 2019 New Relic, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import pytest
import datetime
import os


@pytest.fixture(scope="module")
def stats():
    from airflow.settings import Stats

    assert hasattr(Stats, "batch")
    pid = os.getpid()
    assert pid not in Stats._batches
    yield Stats
    assert pid in Stats._batches


def test_incr(stats):
    stats.incr("test_metric")


def test_decr(stats):
    stats.decr("test_metric")


def test_gauge(stats):
    stats.gauge("test_metric", 100)


def test_timing_datetime(stats):
    dt = datetime.timedelta(microseconds=1000)
    stats.timing("test_timer", dt)


def test_timing_float(stats):
    stats.timing("test_timer", 0.7)
