|header|

.. |header| image:: https://github.com/newrelic/open-source-office/raw/master/examples/categories/images/Experimental.png
    :target: https://github.com/newrelic/open-source-office/blob/master/examples/categories/index.md#category-new-relic-experimental

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

Installation 
------------

Airflow versions >= 1.10 are preferred for ease of use; however, versions >= 1.8 should work.

To start, the ``newrelic-airflow-plugin`` package must be installed. To install
via pip:

.. code-block:: bash

    $ pip install newrelic-airflow-plugin

Getting Started
+++++++++++++

Set the ``NEW_RELIC_INSERT_KEY`` environment variable to a valid
`New Relic insert key <https://docs.newrelic.com/docs/apis/get-started/intro-apis/types-new-relic-api-keys#event-insert-key>`_

The ``NEW_RELIC_SERVICE_NAME`` environment variable can be set to customize the
``service.name`` attribute on all generated metrics. The default value is
``Airflow``.


Airflow Versions >= 1.10:
✨ That's it! ✨

Airflow Versions < 1.10:
The `newrelic_plugin.py <src/newrelic_airflow_plugin/newrelic_plugin.py>`_
file must be copied into the configured ``plugins_folder`` directory. This
defaults to ``{AIRFLOW_HOME}/plugins``.

Support
-------

Should you need assistance with New Relic products, you are in good
hands with several support channels.

If the issue has been confirmed as a bug or is a feature request, file a
GitHub issue.

**Support Channels**

-  `New Relic Documentation <LINK%20to%20specific%20docs%20page>`__:
   Comprehensive guidance for using our platform
-  `New Relic Community <LINK%20to%20specific%20community%20page>`__:
   The best place to engage in troubleshooting questions
-  `New Relic Developer <https://developer.newrelic.com/>`__: Resources
   for building a custom observability applications
-  `New Relic University <https://learn.newrelic.com/>`__: A range of
   online training for New Relic users of every level

Privacy
-------

At New Relic we take your privacy and the security of your information
seriously, and are committed to protecting your information. We must
emphasize the importance of not sharing personal data in public forums,
and ask all users to scrub logs and diagnostic information for sensitive
information, whether personal, proprietary, or otherwise.

We define “Personal Data” as any information relating to an identified
or identifiable individual, including, for example, your name, phone
number, post code or zip code, Device ID, IP address, and email address.

For more information, review `New Relic’s General Data Privacy
Notice <https://newrelic.com/termsandconditions/privacy>`__.

Contribute
----------

We encourage your contributions to improve [project name]! Keep in mind
that when you submit your pull request, you’ll need to sign the CLA via
the click-through using CLA-Assistant. You only have to sign the CLA one
time per project.

If you have any questions, or to execute our corporate CLA (which is
required if your contribution is on behalf of a company), drop us an
email at opensource@newrelic.com.

**A note about vulnerabilities**

As noted in our `security policy <../../security/policy>`__, New Relic
is committed to the privacy and security of our customers and their
data. We believe that providing coordinated disclosure by security
researchers and engaging with the security community are important means
to achieve our security goals.

If you believe you have found a security vulnerability in this project
or any of New Relic’s products or websites, we welcome and greatly
appreciate you reporting it to New Relic through
`HackerOne <https://hackerone.com/newrelic>`__.

If you would like to contribute to this project, review `these
guidelines <./CONTRIBUTING.md>`__.

To `all contributors <LINK%20TO%20contributors>`__, we thank you!
Without your contribution, this project would not be what it is today.
We also host a community project page dedicated to `Project
Name <LINK%20TO%20https://opensource.newrelic.com/projects/...%20PAGE>`__.

License
-------

newrelic-airflow-plugin is licensed under the `Apache
2.0 <http://apache.org/licenses/LICENSE-2.0.txt>`__ License. >


