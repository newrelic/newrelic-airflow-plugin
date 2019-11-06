from airflow.plugins_manager import AirflowPlugin
from newrelic_airflow_plugin.harvester import Harvester
from newrelic_airflow_plugin.metric_batch import MetricBatch
from newrelic_telemetry_sdk import CountMetric, GaugeMetric, MetricClient
import os

import logging
import atexit

_logger = logging.getLogger(__name__)

try:
    # sys._getframe is not part of the python spec and is not guaranteed to
    # exist in all python implemenations. However, it does exists in the
    # reference implemenations of cpython 2, 3 and in pypy.
    # It is about 3 orders of magnitude faster than inspect in python 2.7
    # on my laptop. Inspect touches the disk to get filenames and possibly
    # other information which we don't need.
    import sys

    get_frame = sys._getframe
except AttributeError:
    import inspect

    def getframe(depth):
        return inspect.stack(0)[depth]

    get_frame = getframe


def join_harvester(harvester):
    harvester.stop()
    harvester.join()


def send_batch(client, batch):
    try:
        response = client.send_batch(*batch.flush())
        if not response.ok:
            _logger.error(
                "New Relic send_batch failed with status code: %r", response.status
            )
    except Exception:
        _logger.exception("New Relic send_batch failed with an exception.")


class NewRelicStatsLogger(object):
    _recorders = {}

    @staticmethod
    def use_harvester():
        frame = get_frame(2)
        while frame:
            if "/airflow/" in frame.f_code.co_filename:
                if frame.f_code.co_name == "_run_raw_task":
                    return False
                elif (
                    frame.f_code.co_filename.endswith("/bin/cli.py")
                    and frame.f_code.co_name == "run"
                ):
                    return False
            frame = frame.f_back

        return True

    @classmethod
    def recorder(cls):
        pid = os.getpid()
        recorder = cls._recorders.get(pid, None)
        if recorder:
            return recorder

        service_name = os.environ.get("NEW_RELIC_SERVICE_NAME", "Airflow")
        insert_key = os.environ["NEW_RELIC_INSERT_KEY"]
        client = MetricClient(insert_key)
        batch = MetricBatch({"service.name": service_name})
        use_harvester = cls.use_harvester()
        _logger.info(
            "PID: %d -- Using New Relic Stats Recorder -- use_harvester: %r",
            os.getpid(),
            use_harvester,
        )

        if use_harvester:
            recorder = Harvester(client, batch)
            recorder.start()
            atexit.register(join_harvester, recorder)
        else:
            recorder = batch
            atexit.register(send_batch, client, batch)

        cls._recorders[pid] = recorder
        return recorder

    @classmethod
    def incr(cls, stat, count=1, rate=1):
        metric = CountMetric.from_value(stat, count)
        cls.recorder().record(metric)

    @classmethod
    def decr(cls, stat, count=1, rate=1):
        raise NotImplementedError

    @classmethod
    def gauge(cls, stat, value, rate=1, delta=False):
        metric = GaugeMetric.from_value(stat, value)
        cls.recorder().record(metric)

    @classmethod
    def timing(cls, stat, dt):
        try:
            metric = GaugeMetric.from_value(
                stat, dt.microseconds, tags={"units": "microseconds"}
            )
        except AttributeError:
            metric = GaugeMetric.from_value(stat, float(dt))
        cls.recorder().record(metric)


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
                for attr in (
                    "_recorders",
                    "use_harvester",
                    "recorder",
                    "incr",
                    "gauge",
                    "timing",
                ):
                    setattr(Stats, attr, getattr(NewRelicStatsLogger, attr))

        return result
