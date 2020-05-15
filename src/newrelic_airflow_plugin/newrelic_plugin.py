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

from airflow.plugins_manager import AirflowPlugin
from newrelic_airflow_plugin.metric_batch import MetricBatch
from newrelic_telemetry_sdk import CountMetric, GaugeMetric, MetricClient
import os

import logging
import atexit
import re

_logger = logging.getLogger(__name__)

TI_COMPLETE_RE = re.compile(r"ti_(successes|failures)")
DAG_COMPLETE_RE = re.compile(r"dagrun.duration.(success|failure)")


def send_batch(batch):
    try:
        insert_key = os.environ["NEW_RELIC_INSERT_KEY"]
        client = MetricClient(insert_key)
        response = client.send_batch(*batch.flush())
        if not response.ok:
            _logger.error(
                "New Relic send_batch failed with status code: %r", response.status
            )
    except Exception:
        _logger.exception("New Relic send_batch failed with an exception.")


class NewRelicStatsLogger(object):
    _batches = {}

    @classmethod
    def batch(cls):
        pid = os.getpid()
        batch = cls._batches.get(pid, None)
        if batch:
            return batch

        service_name = os.environ.get("NEW_RELIC_SERVICE_NAME", "Airflow")
        batch = MetricBatch({"service.name": service_name})
        _logger.info("PID: %d -- Using New Relic Stats Recorder", os.getpid())

        atexit.register(send_batch, batch)

        cls._batches[pid] = batch
        return batch

    @classmethod
    def incr(cls, stat, count=1, rate=1):
        metric = CountMetric.from_value(stat, count)
        batch = cls.batch()
        batch.record(metric)
        # If the metric matches ti_successes or ti_failures we know the task
        # instance completed and we want to send metrics before the process
        # exits.
        if TI_COMPLETE_RE.match(stat):
            send_batch(batch)

    @classmethod
    def decr(cls, stat, count=1, rate=1):
        raise NotImplementedError

    @classmethod
    def gauge(cls, stat, value, rate=1, delta=False):
        metric = GaugeMetric.from_value(stat, value)
        batch = cls.batch()
        batch.record(metric)

    @classmethod
    def timing(cls, stat, dt):
        try:
            metric = GaugeMetric.from_value(
                stat, dt.microseconds, tags={"units": "microseconds"}
            )
        except AttributeError:
            metric = GaugeMetric.from_value(stat, float(dt))
        batch = cls.batch()
        batch.record(metric)
        # If the metric matches ti_successes or ti_failures we know the task
        # instance completed and we want to send metrics before the process
        # exits.
        if DAG_COMPLETE_RE.match(stat):
            send_batch(batch)


class NewRelicStatsPlugin(AirflowPlugin):
    name = "NewRelicStatsPlugin"

    @classmethod
    def validate(cls):
        result = super(NewRelicStatsPlugin, cls).validate()

        DummyStatsLogger = Stats = None

        try:
            from airflow.stats import Stats, DummyStatsLogger
        except ImportError:

            try:
                from airflow.settings import Stats, DummyStatsLogger
            except ImportError:
                pass

        if "NEW_RELIC_INSERT_KEY" in os.environ:
            _logger.info("Using NewRelicStatsLogger")
            if Stats is DummyStatsLogger:
                for attr in ("_batches", "batch", "incr", "gauge", "timing"):
                    setattr(Stats, attr, getattr(NewRelicStatsLogger, attr))

        return result
