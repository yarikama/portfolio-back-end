import logging

from loguru import logger
from opentelemetry import trace


class InterceptHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:  # pragma: no cover
        logger_opt = logger.opt(depth=7, exception=record.exc_info)
        logger_opt.log(record.levelname, record.getMessage())


# Loguru's default format, plus the trace id when there is one.
FORMAT = (
    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
    "<level>{message}</level>{extra[trace]}"
)


def add_trace_id(record) -> None:
    """
    Loguru patcher: lines logged while handling a traced request end with
    its trace id, so Grafana can jump between a trace and its logs.
    """
    context = trace.get_current_span().get_span_context()
    record["extra"]["trace"] = (
        f" trace_id={context.trace_id:032x}" if context.is_valid else ""
    )
