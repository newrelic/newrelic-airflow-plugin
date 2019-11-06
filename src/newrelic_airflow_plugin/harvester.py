import logging
import time
import threading
import queue

_logger = logging.getLogger(__name__)


class Harvester(threading.Thread):
    """Report data to New Relic at a fixed interval

    The Harvester is a thread implementation which sends data to New Relic every
    ``harvest_interval`` seconds or until the data buffers are full.

    The reporter will automatically handle error conditions which may occur
    such as:

    * Network timeouts
    * New Relic errors

    :param client: The client instance to call in order to send data.
    :type client: newrelic_sdk.client.Client
    :param batch: A batch with record and flush interfaces.
    :param harvest_interval: (optional) The interval in seconds at which data
        will be reported. (default 5)
    :type harvest_interval: int or float
    :param max_queue_size: (optional) The maximum number of items waiting to be
        aggregated. (default: 10)
    :type max_queue_size: int
    """

    STOP = object()

    def __init__(self, client, batch, harvest_interval=5, max_queue_size=10):
        super(Harvester, self).__init__()
        self.daemon = True
        self.client = client
        self.batch = batch
        self.harvest_interval = harvest_interval
        self._queue = queue.Queue(maxsize=max_queue_size)
        self._deadline = 0

    @property
    def _timeout(self):
        return max(self._deadline - time.time(), 0)

    def _loop(self, client=None, batch=None):
        client = client or self.client
        batch = batch or self.batch

        exited = False
        try:
            item = self._queue.get(timeout=self._timeout)
            if item is self.STOP:
                exited = True
            else:
                batch.record(item)
        except queue.Empty:
            pass

        if exited or time.time() > self._deadline:
            self._deadline = time.time() + self.harvest_interval
            items, common = batch.flush()

            if items:
                try:
                    response = client.send_batch(items, common=common)
                    if not response.ok:
                        _logger.error(
                            "New Relic send_batch failed with status code: %r",
                            response.status,
                        )
                except Exception:
                    _logger.exception("New Relic send_batch failed with an exception.")

            # If sending caused the deadline to be missed, just "skip" to the
            # next harvest interval This is done to allow for a batch of
            # reasonable size to be built and to allow a backpressured queue to
            # empty
            if time.time() > self._deadline:
                self._deadline = time.time() + self.harvest_interval

        return exited

    def run(self):
        """Main loop of the harvester thread"""
        self._deadline = time.time() + self.harvest_interval
        exited = False
        batch = self.batch
        client = self.client

        while not exited:
            exited = self._loop(client, batch)

        self.batch = self.client = None

    def record(self, item):
        """Add an item to the queue to be harvested

        Calling record with an item will merge it into the batch maintained by
        this harvester.

        :param item: A metric or span to be merged into a batch.
        """
        self._queue.put(item)

    def stop(self):
        """Enqueue a stop request

        This will cause the thread to eventually terminate. The thread may not
        terminate immediately so this call is usually followed by a join()
        call.
        """
        self._queue.put(self.STOP)
