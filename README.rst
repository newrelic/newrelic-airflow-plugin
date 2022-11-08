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

Airflow versions >= 1.10 are preferred for ease of use; however, versions >= 1.8 should work.

Using the plugin
----------------

To start, the ``newrelic-airflow-plugin`` package must be installed. To install
via pip:

.. code-block:: bash

    $ pip install newrelic-airflow-plugin


Configuration
----------------

The integration can either be configured via configuration file (`airflow.cfg`) or via environment variables.

Via configuration file
++++++++++++++++++++++++

Per default the integration will look for a configuration file called ``airflow.cfg`` in the ``/opt/airflow`` directory. 

The directory can be changed via the ``AIRFLOW_HOME`` environment variable.

The integration is configured within the ``[newrelic]`` section (see [docker example](./docker/airflow.cfg)).


Following properties are supported:
```
[newrelic]

insert_key = abc-your-ingest-key-here   # Insert API Key
host = metric-api.eu.newrelic.com       # Datacenter host (defaults to US region)
service_name = local-airflow-docker     # Custom service name, under which the data will be reported (defaults to Airflow)
harvester_interval = 10                 # Harvester interval (defaults to 5)

# Additional dimensions to pass
nr_dim_foo = bar
nr_dim_baz = lol
nr_dim_some = thing
```


Additional dimensions can be added only in the configuration file.

They need to start with the `nr_dim_` prefix, which will be cut away when sending to New Relic.


Via Environment
++++++++++++++++++++++++

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

Disable Airflow's lazy plugin loading. This is required for the plugin to properly patch Airflow's Stats engine.

This can be done via environment variable:

``AIRFLOW__CORE__LAZY_LOAD_PLUGINS=False``

Or can be set in your config file (``airflow.cfg``):

.. code-block::

    [core]
    lazy_load_plugins = False


Airflow Versions >= 1.10,<2.0
++++++++++++++++++++++++++++++

✨ That's it! ✨

Airflow Versions < 1.10
+++++++++++++++++++++++

The `newrelic_plugin.py <src/newrelic_airflow_plugin/newrelic_plugin.py>`_
file must be copied into the configured ``plugins_folder`` directory. This
defaults to ``{AIRFLOW_HOME}/plugins``.