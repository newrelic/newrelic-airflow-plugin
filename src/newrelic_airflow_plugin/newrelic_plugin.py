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

from airflow.plugins_manager import AirflowPlugin
from airflow.configuration import AirflowConfigParser
from newrelic_telemetry_sdk import Harvester as _Harvester
from newrelic_telemetry_sdk import MetricBatch, MetricClient

ENV_SERVICE_NAME = "NEW_RELIC_SERVICE_NAME"
ENV_INSERT_KEY = "NEW_RELIC_INSERT_KEY"
ENV_HOST = "NEW_RELIC_HOST"

PROP_HOST = "host"
PROP_SERVICE_NAME = "service_name"
PROP_INSERT_KEY = "insert_key"
PROP_HARVESTER_INTERVAL = "harvester_interval"

DIM_PREFIX = "nr_dim_"

_logger = logging.getLogger(__name__)


def get_config():
    config_location = os.environ.get("AIRFLOW_HOME", "/opt/airflow") + "/airflow.cfg"

    nr_config = {}
    if os.path.isfile(config_location) and os.access(config_location, os.R_OK):
        file = open(config_location, mode="r")
        airflow_config = file.read()
        file.close()
        airflow_config = AirflowConfigParser(
            default_config=airflow_config.encode("UTF-8").decode()
        )
        section = airflow_config.getsection("newrelic")
        if section is not None:
            nr_config = section
    else:
        _logger.info("Could not find airflow config at ", config_location)

    # Set default configs
    if PROP_INSERT_KEY not in nr_config and ENV_INSERT_KEY in os.environ:
        nr_config[PROP_INSERT_KEY] = os.environ.get(ENV_INSERT_KEY)

    if PROP_SERVICE_NAME not in nr_config:
        nr_config[PROP_SERVICE_NAME] = os.environ.get(ENV_SERVICE_NAME, "Airflow")

    if PROP_HOST not in nr_config:
        nr_config[PROP_HOST] = os.environ.get(ENV_HOST, None)

    if PROP_HARVESTER_INTERVAL not in nr_config:
        nr_config[PROP_HARVESTER_INTERVAL] = 5

    return nr_config


def get_dimensions(config):
    dims = {"service.name": config[PROP_SERVICE_NAME]}
    for key, value in config.items():
        if key.startswith(DIM_PREFIX):
            dims[key[len(DIM_PREFIX) :]] = value

    return dims


config = get_config()


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

            client = MetricClient(config[PROP_INSERT_KEY], host=config[PROP_HOST])

            batch = MetricBatch(get_dimensions(config))
            _logger.info("PID: %d -- Using New Relic Stats Recorder", pid)

            harvester = cls._harvesters[pid] = Harvester(
                client, batch, harvest_interval=config[PROP_HARVESTER_INTERVAL]
            )
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
    patched_attrs = ("incr", "gauge", "timing")

    @classmethod
    def validate(cls):
        result = super(NewRelicStatsPlugin, cls).validate()

        DummyStatsLogger = Stats = None

        try:
            from airflow.stats import DummyStatsLogger, Stats
        except ImportError:
            try:
                from airflow.settings import DummyStatsLogger, Stats
            except ImportError:
                pass

        if PROP_INSERT_KEY in config and not cls.patched:
            cls.patched = True
            _logger.info("Using NewRelicStatsLogger")

            # Patch class
            if Stats is DummyStatsLogger:
                for attr in cls.patched_attrs:
                    setattr(Stats, attr, getattr(NewRelicStatsLogger, attr))

            # Patch instance
            if hasattr(Stats, "instance") and isinstance(
                Stats.instance, DummyStatsLogger
            ):
                for attr in cls.patched_attrs:
                    setattr(Stats.instance, attr, getattr(NewRelicStatsLogger, attr))

        return result
