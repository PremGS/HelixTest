"""Structured logging setup.

This module is the integration point for shipping logs to Azure Monitor /
Application Insights (per the "Azure Monitor + App Insights" component in
``.helix/ARCHITECTURE.md``). For this scaffold it simply configures standard
library logging with a consistent format; wiring an OpenTelemetry / Azure
Monitor exporter is left as a TODO.
"""

import logging
import sys

_CONFIGURED = False


def configure_logging(level: int = logging.INFO) -> None:
    """Configure root logging handlers for the application.

    Safe to call multiple times; only configures handlers once per process.

    TODO: integrate ``azure-monitor-opentelemetry`` (or the OpenCensus Azure
    Monitor exporter) here to ship traces/logs/metrics to Application
    Insights, using the connection string from ``Settings``.
    """

    global _CONFIGURED
    if _CONFIGURED:
        return

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter(
            fmt="%(asctime)s %(levelname)s %(name)s :: %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S%z",
        )
    )

    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.addHandler(handler)

    _CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    """Return a module-level logger, ensuring logging has been configured."""

    configure_logging()
    return logging.getLogger(name)
