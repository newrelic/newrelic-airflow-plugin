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

import datetime
import os

import pytest
from newrelic_telemetry_sdk.client import HTTPResponse, MetricClient


@pytest.fixture(scope="module")
def stats():
    from airflow.settings import Stats
    from newrelic_airflow_plugin.newrelic_plugin import NewRelicStatsLogger

    pid = os.getpid()
    assert pid not in NewRelicStatsLogger._harvesters
    yield Stats
    assert pid in NewRelicStatsLogger._harvesters


@pytest.fixture
def capture_sent(monkeypatch):
    _metrics = []

    def send_batch(instance, items, common):
        _metrics.extend(items)
        return HTTPResponse(status=200)

    monkeypatch.setattr(MetricClient, "send_batch", send_batch)
    yield _metrics


def test_send_on_ti_success(stats, capture_sent):
    # Record some metrics
    stats.incr("test.incr")
    stats.gauge("test.gauge", 12)
    stats.timing("tests.timing", 1.32)
    # No metrics should have been sent yet
    assert len(capture_sent) == 0
    # Record a ti_successes metric
    stats.incr("ti_successes")
    # All four metrics should be sent
    assert len(capture_sent) == 4


def test_on_dagrun_failure(stats, capture_sent):
    # Record some metrics
    stats.incr("test.incr")
    stats.gauge("test.gauge", 12)
    stats.timing("tests.timing", 1.32)
    # No metrics should have been sent yet
    assert len(capture_sent) == 0
    # Record a dagrun.duration.failure metric
    stats.timing("dagrun.duration.failure", 0.5)
    # All four metrics should be sent
    assert len(capture_sent) == 4


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
