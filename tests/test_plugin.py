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

from newrelic_telemetry_sdk.client import MetricClient, HTTPResponse


@pytest.fixture(scope="module")
def stats():
    from airflow.settings import Stats

    assert hasattr(Stats, "batch")
    pid = os.getpid()
    assert pid not in Stats._batches
    yield Stats
    assert pid in Stats._batches


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


def test_send_on_threshold(monkeypatch, stats, capture_sent):
    from newrelic_airflow_plugin.newrelic_plugin import NewRelicStatsLogger

    # monkeypatch to send after 5 metrics are recorded
    monkeypatch.setattr(NewRelicStatsLogger, "SEND_THRESHOLD", 5)

    stats.incr("test.incr.a")
    stats.incr("test.incr.b")
    stats.gauge("test.gauge.a", 12)
    stats.gauge("test.gauge.b", 12)
    stats.timing("test.timing", 1.32)
    # No metrics should have been sent yet
    assert len(capture_sent) == 0
    # Record one more metric to pass the threshold
    stats.timing("dagrun.duration.dag", 0.5)
    # All six metrics should be sent
    assert len(capture_sent) == 6


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
