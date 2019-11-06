import pytest
import datetime
import os


@pytest.fixture(scope="module")
def stats():
    from airflow.settings import Stats

    assert hasattr(Stats, "recorder")
    pid = os.getpid()
    assert pid not in Stats._recorders
    yield Stats
    assert pid in Stats._recorders


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
