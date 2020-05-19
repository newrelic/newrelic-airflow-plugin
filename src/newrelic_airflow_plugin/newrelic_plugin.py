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

import atexit
import logging
import os

from airflow.plugins_manager import AirflowPlugin
from newrelic_airflow_plugin.metric_batch import MetricBatch as _MetricBatch
from newrelic_telemetry_sdk import CountMetric, GaugeMetric, MetricClient

_logger = logging.getLogger(__name__)


class MetricBatch(_MetricBatch):
    IMMEDIATE_FLUSH_PREFIXES = ("ti_", "dagrun.duration.")

    @property
    def client(self):
        if hasattr(self, "_client"):
            return self._client

        insert_key = os.environ["NEW_RELIC_INSERT_KEY"]
        self._client = client = MetricClient(insert_key)
        return client

    def record(self, metric, *args, **kwargs):
        result = super(MetricBatch, self).record(metric, *args, **kwargs)

        for prefix in self.IMMEDIATE_FLUSH_PREFIXES:
            if metric.name.startswith(prefix):
                self.flush_and_send()
                break

        return result

    def flush_and_send(self):
        try:
            args = super(MetricBatch, self).flush()
            response = self.client.send_batch(*args)
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
        _logger.info("PID: %d -- Using New Relic Stats Recorder", pid)

        atexit.register(batch.flush_and_send)

        cls._batches[pid] = batch
        return batch

    @classmethod
    def record_metric(cls, metric):
        batch = cls.batch()
        batch.record(metric)

    @classmethod
    def incr(cls, stat, count=1, rate=1):
        metric = CountMetric.from_value(stat, count)
        cls.record_metric(metric)

    @classmethod
    def decr(cls, stat, count=1, rate=1):
        raise NotImplementedError

    @classmethod
    def gauge(cls, stat, value, rate=1, delta=False):
        metric = GaugeMetric.from_value(stat, value)
        cls.record_metric(metric)

    @classmethod
    def timing(cls, stat, dt):
        try:
            metric = GaugeMetric.from_value(
                stat, dt.microseconds, tags={"units": "microseconds"}
            )
        except AttributeError:
            metric = GaugeMetric.from_value(stat, float(dt))
        cls.record_metric(metric)


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
