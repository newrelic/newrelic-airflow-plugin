from newrelic_telemetry_sdk import CountMetric, SummaryMetric
import time


class MetricBatch(object):
    """Maps a metric identity to its aggregated value

    This is used to hold unfinalized metrics for further aggregation until they
    are flushed to a backend.

    :param tags: (optional) A dictionary of tags to attach to all flushes.
    :type tags: dict
    """

    def __init__(self, tags=None):
        self._interval_start = int(time.time() * 1000.0)
        self._batch = {}
        tags = tags and tags.copy() or {}
        self._common = {"attributes": tags}

    @staticmethod
    def create_identity(metric):
        """Creates a deterministic hashable identity for a metric

        :param metric: A New Relic metric object
        :type metric: newrelic_telemetry_sdk.metric.Metric

        Usage::

            >>> from newrelic_telemetry_sdk import GaugeMetric
            >>> metric_a = GaugeMetric('foo', 0, tags={'units': 'C'})
            >>> metric_b = GaugeMetric('foo', 1, tags={'units': 'C'})
            >>> MetricBatch.create_identity(metric_a) == \
                MetricBatch.create_identity(metric_b)
            True
        """
        tags = metric.tags
        if tags:
            tags = frozenset(tags.items())
        identity = (type(metric), metric.name, tags)
        return identity

    def record(self, metric):
        """Merge a metric into the batch

        :param metric: The metric to merge into the batch.
        :type metric: newrelic_telemetry_sdk.metric.Metric
        """
        identity = self.create_identity(metric)

        if identity in self._batch:
            merged = self._batch[identity]
            value = metric["value"]

            if isinstance(metric, SummaryMetric):
                merged_value = merged["value"]
                merged_value["count"] += value["count"]
                merged_value["sum"] += value["sum"]
                merged_value["min"] = min(value["min"], merged_value["min"])
                merged_value["max"] = max(value["max"], merged_value["max"])
            elif isinstance(metric, CountMetric):
                merged["value"] += value
            else:
                merged["value"] = value

        else:
            metric = self._batch[identity] = metric.copy()
            # Timestamp will now be tracked as part of the batch
            metric.pop("timestamp")

    def flush(self):
        """Flush all metrics from the batch

        This method returns all metrics in the batch and a common block
        representing timestamp as the start time for the period since creation
        or last flush, and interval representing the total amount of time in
        milliseconds between flushes.

        As a side effect, the batch's interval is reset in anticipation of
        subsequent calls to flush.

        :returns: A tuple of (metrics, common)
        :rtype: tuple
        """
        common = self._common.copy()
        common["timestamp"] = self._interval_start
        timestamp = int(time.time() * 1000.0)
        interval = timestamp - self._interval_start
        common["interval.ms"] = interval
        self._interval_start = timestamp
        batch = self._batch
        self._batch = {}
        return tuple(batch.values()), common
