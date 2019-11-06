import pytest
import logging
import time
from newrelic_airflow_plugin.harvester import Harvester
from newrelic_telemetry_sdk import MetricClient, GaugeMetric
from newrelic_airflow_plugin.metric_batch import MetricBatch


class Response(object):
    status = 500
    ok = False


@pytest.fixture(autouse=True)
def response():
    yield Response
    Response.status = 500
    Response.ok = False


class MockedMetricClient(MetricClient):
    def __init__(self, *args, **kwargs):
        self.calls = []

    def send_batch(self, items, common=None):
        self.calls.append((items, common))
        return Response


@pytest.fixture
def client(response):
    return MockedMetricClient()


@pytest.fixture
def batch():
    return MetricBatch()


@pytest.fixture
def harvester(client, batch):
    return Harvester(client, batch)


def drain_queue(harvester):
    while True:
        # Force a loop
        exited = harvester._loop()
        assert exited is False
        if harvester._queue.empty():
            break


def test_harvest_loop_unflushed(harvester, batch):
    # place two merged items into the batch
    metric = GaugeMetric("foo", 1000)
    harvester.record(metric)
    harvester.record(metric)

    # disable sending (should not call flush)
    harvester._deadline = time.time() + 600

    drain_queue(harvester)

    items, _ = batch.flush()
    assert len(items) == 1
    assert items[0]["name"] == "foo"
    assert items[0]["value"] == 1000


def test_harvest_loop_flush_no_items(harvester):
    current_time = time.time()

    # If sending is attempted, an exception will be raised
    harvester.client = None

    drain_queue(harvester)
    assert harvester._deadline > (current_time + 5)


def test_harvest_loop_missed_deadline(harvester, monkeypatch):
    monkeypatch.setattr(time, "time", lambda: harvester._deadline + 100)

    # If sending is attempted, an exception will be raised
    harvester.client = None

    drain_queue(harvester)


@pytest.mark.parametrize("response_ok", (True, False))
def test_harvest_loop_flush(harvester, client, batch, response_ok):
    # Override the response ok flag
    Response.ok = response_ok

    # place two merged items into the batch
    metric = GaugeMetric("foo", 1000)
    timestamp = batch._interval_start
    harvester.record(metric)
    harvester.record(metric)

    harvester._deadline = time.time() + 600

    drain_queue(harvester)

    harvester._deadline = 0
    current_time = time.time()
    exited = harvester._loop()
    assert exited is False

    assert harvester._deadline > (current_time + 5)

    calls = client.calls
    assert len(calls) == 1
    items, common = calls[0]
    assert len(items) == 1
    assert items[0]["name"] == "foo"
    assert items[0]["value"] == 1000
    assert common["timestamp"] == timestamp
    assert "interval.ms" in common


def test_harvest_exit(harvester):
    harvester.stop()

    # disable sending (should not call flush)
    harvester._deadline = float("inf")

    exited = harvester._loop()
    assert exited is True


def test_harvest_loop_run(harvester):
    # Force the harvester to exit on first run
    harvester.stop()

    current_time = time.time()
    harvester.start()
    harvester.join()

    assert harvester._deadline > (current_time + 5)
    assert harvester.client is None
    assert harvester.batch is None


def test_send_batch_exception(harvester, caplog):
    batch = MetricBatch()
    batch.record(GaugeMetric("foo", 1000))

    # Cause an exception to be raised since send_batch doesn't exist on object
    harvester._loop(object(), batch)

    assert (
        "newrelic_airflow_plugin.harvester",
        logging.ERROR,
        "New Relic send_batch failed with an exception.",
    ) in caplog.record_tuples


def test_send_batch_failed(harvester, batch, caplog):
    batch.record(GaugeMetric("foo", 1000))

    # Cause a 500 response from send_batch
    drain_queue(harvester)

    assert (
        "newrelic_airflow_plugin.harvester",
        logging.ERROR,
        "New Relic send_batch failed with status code: 500",
    ) in caplog.record_tuples
