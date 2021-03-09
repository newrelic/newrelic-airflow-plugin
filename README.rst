|header|

.. |header| image:: https://github.com/newrelic/opensource-website/raw/master/src/images/categories/Community_Plus.png
    :target: https://opensource.newrelic.com/oss-category/#community-plus

New Relic Airflow Metric Exporter
=================================

|ci| |black|

.. |ci| image:: https://img.shields.io/azure-devops/build/NRAzurePipelines/Python/19.svg
    :target: https://dev.azure.com/NRAzurePipelines/Python/_build/latest?definitionId=19&branchName=master

.. |black| image:: https://img.shields.io/badge/code%20style-black-000000.svg
    :target: https://github.com/psf/black

A plugin for `Apache Airflow <https://airflow.apache.org/>`_ to send
`metrics <https://airflow.apache.org/metrics.html>`_ to
`New Relic <https://docs.newrelic.com>`_.

Requirements
------------

Only supports Airflow versions >= 2.0.

Using the plugin
----------------

To start, the ``newrelic-airflow-plugin`` package must be installed. To install
via pip:

.. code-block:: bash

    $ pip install newrelic-airflow-plugin


Configuration
+++++++++++++

Set the ``NEW_RELIC_INSERT_KEY`` environment variable to a valid
`New Relic insert key <https://docs.newrelic.com/docs/apis/get-started/intro-apis/types-new-relic-api-keys#event-insert-key>`_

The ``NEW_RELIC_SERVICE_NAME`` environment variable can be set to customize the
``service.name`` attribute on all generated metrics. The default value is
``Airflow``.

``NEW_RELIC_HOST`` environment variable can be used to set datacenter host.
For example, to send metrics to EU data center set this variable to ``metric-api.eu.newrelic.com``
By default metrics will be send to US data center.


Airflow Versions >= 2.0
++++++++++++++++++++++++

✨ That's it! ✨
