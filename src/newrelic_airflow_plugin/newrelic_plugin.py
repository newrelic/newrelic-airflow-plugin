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
import threading

from newrelic_telemetry_sdk import Harvester as _Harvester
from newrelic_telemetry_sdk import MetricBatch, MetricClient

from airflow.plugins_manager import AirflowPlugin

_logger = logging.getLogger(__name__)


class Harvester(_Harvester):
    IMMEDIATE_FLUSH_PREFIXES = ("ti_", "dagrun.duration.")

    def send_for_metric(self, metric_name):
        for prefix in self.IMMEDIATE_FLUSH_PREFIXES:
            if metric_name.startswith(prefix):
                try:
                    response = self.client.send_batch(*self.batch.flush())
                    if not response.ok:
                        _logger.error(
                            "Sending metrics failed with status code: %r",
                            response.status,
                        )
                except Exception:
                    _logger.exception("Sending metrics failed with an exception.")


class NewRelicStatsLogger(object):
    _harvesters = {}
    _lock = threading.RLock()

    @classmethod
    def harvester(cls):
        pid = os.getpid()
        harvester = cls._harvesters.get(pid, None)
        if harvester:
            return harvester

        with cls._lock:
            harvester = cls._harvesters.get(pid, None)
            if harvester:
                return harvester

            insert_key = os.environ["NEW_RELIC_INSERT_KEY"]
            host = os.environ.get("NEW_RELIC_HOST", None)
            client = MetricClient(insert_key, host=host)

            service_name = os.environ.get("NEW_RELIC_SERVICE_NAME", "Airflow")
            batch = MetricBatch({"service.name": service_name})
            _logger.info("PID: %d -- Using New Relic Stats Recorder", pid)

            harvester = cls._harvesters[pid] = Harvester(client, batch)
            harvester.start()

            atexit.register(harvester.stop)

            return harvester

    @classmethod
    def incr(cls, stat, count=1, rate=1):
        harvester = cls.harvester()
        harvester.batch.record_count(stat, count)
        harvester.send_for_metric(stat)

    @classmethod
    def decr(cls, stat, count=1, rate=1):
        raise NotImplementedError

    @classmethod
    def gauge(cls, stat, value, rate=1, delta=False):
        harvester = cls.harvester()
        harvester.batch.record_gauge(stat, value)
        harvester.send_for_metric(stat)

    @classmethod
    def timing(cls, stat, dt):
        value = None
        tags = None
        try:
            value = dt.microseconds
            tags = {"units": "microseconds"}
        except AttributeError:
            value = float(dt)
        harvester = cls.harvester()
        harvester.batch.record_gauge(stat, value, tags=tags)
        harvester.send_for_metric(stat)


class NewRelicStatsPlugin(AirflowPlugin):
    name = "NewRelicStatsPlugin"
    patched = False

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

        if "NEW_RELIC_INSERT_KEY" in os.environ and not cls.patched:
            cls.patched = True
            _logger.info("Using NewRelicStatsLogger")
            if Stats is DummyStatsLogger:
                for attr in ("incr", "gauge", "timing"):
                    setattr(Stats, attr, getattr(NewRelicStatsLogger, attr))

        return result
