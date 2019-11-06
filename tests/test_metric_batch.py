import pytest
from newrelic_telemetry_sdk import GaugeMetric, CountMetric, SummaryMetric
from newrelic_airflow_plugin.metric_batch import MetricBatch


@pytest.mark.parametrize("tags", (None, {"foo": "bar"}))
def test_create_identity(tags):
    metric = GaugeMetric("name", 1000, tags=tags)

    expected_tags = frozenset(tags.items()) if tags else None
    identity = MetricBatch.create_identity(metric)
    assert len(identity) == 3
    assert identity[0] is GaugeMetric
    assert identity[1] == "name"
    assert identity[2] == expected_tags


@pytest.mark.parametrize(
    "metric_a, metric_b, expected_value",
    (
        (GaugeMetric("name", 1), GaugeMetric("name", 2), 2),
        (CountMetric("name", 1), CountMetric("name", 2), 3),
        (
            SummaryMetric.from_value("name", 1),
            SummaryMetric.from_value("name", 2),
            {"count": 2, "max": 2, "min": 1, "sum": 3},
        ),
    ),
)
def test_merge_metric(metric_a, metric_b, expected_value):
    batch = MetricBatch()

    batch.record(metric_a)
    batch.record(metric_b)

    assert metric_a.start_time_ms
    assert metric_b.start_time_ms

    assert len(batch._batch) == 1
    _, metric = batch._batch.popitem()

    assert metric.name == "name"
    assert metric.value == expected_value
    assert "timestamp" not in metric


def test_flush():
    batch = MetricBatch()
    initial_batch = batch._batch

    # Initialize with dummy timestamp to verify timestamp update
    batch._interval_start = 0

    metrics, common = batch.flush()

    assert len(metrics) == 0

    assert common["timestamp"] == 0
    assert common["interval.ms"] > 0

    # Verify internal state is updated
    assert batch._interval_start > 0
    assert batch._batch is not initial_batch
