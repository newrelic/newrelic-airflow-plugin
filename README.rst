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

Airflow versions >= 1.10 are preferred for ease of use; however, versions >= 1.8 should work.

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


Airflow Versions >= 1.10
++++++++++++++++++++++++

✨ That's it! ✨

Airflow Versions < 1.10
+++++++++++++++++++++++

The `newrelic_plugin.py <src/newrelic_airflow_plugin/newrelic_plugin.py>`_
file must be copied into the configured ``plugins_folder`` directory. This
defaults to ``{AIRFLOW_HOME}/plugins``.
