try:
    from newrelic_airflow_plugin.version import version as __version__
except ImportError:  # pragma: no cover
    __version__ = "unknown"
