# Copyright 2019 New Relic, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os

from newrelic_airflow_plugin.newrelic_plugin import (
    ENV_HOST,
    ENV_INSERT_KEY,
    ENV_SERVICE_NAME,
    PROP_HARVESTER_INTERVAL,
    PROP_HOST,
    PROP_INSERT_KEY,
    PROP_SERVICE_NAME,
    get_config,
    get_dimensions,
)


def test_env_configuration():
    os.environ[ENV_SERVICE_NAME] = "test-name"
    os.environ[ENV_INSERT_KEY] = "foo-bar-baz"
    os.environ[ENV_HOST] = "metric-api.eu.newrelic.com"
    config = get_config()
    assert config[PROP_SERVICE_NAME] == "test-name"
    assert config[PROP_HOST] == "metric-api.eu.newrelic.com"
    assert config[PROP_INSERT_KEY] == "foo-bar-baz"
    assert config[PROP_HARVESTER_INTERVAL] == 5


def test_file_configuration():
    airflow_home = os.environ.get("AIRFLOW_HOME")

    os.environ[ENV_SERVICE_NAME] = "test-name"
    os.environ[ENV_INSERT_KEY] = "foo-bar-baz"
    os.environ[ENV_HOST] = "metric-api.eu.newrelic.com"
    os.environ["AIRFLOW_HOME"] = (
        os.path.dirname(os.path.realpath(__file__)) + "/resources"
    )

    config = get_config()
    assert config[PROP_SERVICE_NAME] == "name-from-file"
    assert config[PROP_HOST] == "metric-api.foo.newrelic.com"
    assert config[PROP_INSERT_KEY] == "my-secret-key"
    assert config[PROP_HARVESTER_INTERVAL] == 99

    dims = get_dimensions(config)
    assert dims["foo"] == "bar"
    assert dims["some"] == "thing"

    os.environ["AIRFLOW_HOME"] = airflow_home
