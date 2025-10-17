"""Logging configuration."""

import functools
import inspect
import logging
import sys
from typing import Any, Callable

import structlog


def setup_logging(log_level: str = "INFO") -> None:
    """Configure structured logging."""

    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper()),
    )


def trace_function(func: Callable) -> Callable:
    """
    Decorator to trace function entry, exit, inputs, and outputs at DEBUG level.

    Usage:
        @trace_function
        def my_function(arg1, arg2):
            ...

    Logs:
        - Function entry with all arguments
        - Function exit with return value
        - Any exceptions raised
    """
    logger = structlog.get_logger(func.__module__)

    @functools.wraps(func)
    async def async_wrapper(*args, **kwargs):
        # Get function signature
        sig = inspect.signature(func)
        bound_args = sig.bind(*args, **kwargs)
        bound_args.apply_defaults()

        # Convert args to loggable format (truncate long values)
        args_dict = {}
        for param_name, param_value in bound_args.arguments.items():
            # Skip 'self' and 'cls'
            if param_name in ("self", "cls"):
                continue
            # Truncate long strings/bytes
            if isinstance(param_value, (str, bytes)):
                args_dict[param_name] = str(param_value)[:200] + ("..." if len(str(param_value)) > 200 else "")
            else:
                args_dict[param_name] = str(param_value)[:200]

        logger.debug(
            "function_entry",
            function=func.__name__,
            module=func.__module__,
            args=args_dict,
        )

        try:
            result = await func(*args, **kwargs)

            # Log result (truncated)
            result_str = str(result)[:200] + ("..." if len(str(result)) > 200 else "")
            logger.debug(
                "function_exit",
                function=func.__name__,
                module=func.__module__,
                result=result_str,
            )

            return result
        except Exception as e:
            logger.debug(
                "function_exception",
                function=func.__name__,
                module=func.__module__,
                exception=str(e),
                exception_type=type(e).__name__,
            )
            raise

    @functools.wraps(func)
    def sync_wrapper(*args, **kwargs):
        # Get function signature
        sig = inspect.signature(func)
        bound_args = sig.bind(*args, **kwargs)
        bound_args.apply_defaults()

        # Convert args to loggable format
        args_dict = {}
        for param_name, param_value in bound_args.arguments.items():
            if param_name in ("self", "cls"):
                continue
            if isinstance(param_value, (str, bytes)):
                args_dict[param_name] = str(param_value)[:200] + ("..." if len(str(param_value)) > 200 else "")
            else:
                args_dict[param_name] = str(param_value)[:200]

        logger.debug(
            "function_entry",
            function=func.__name__,
            module=func.__module__,
            args=args_dict,
        )

        try:
            result = func(*args, **kwargs)

            result_str = str(result)[:200] + ("..." if len(str(result)) > 200 else "")
            logger.debug(
                "function_exit",
                function=func.__name__,
                module=func.__module__,
                result=result_str,
            )

            return result
        except Exception as e:
            logger.debug(
                "function_exception",
                function=func.__name__,
                module=func.__module__,
                exception=str(e),
                exception_type=type(e).__name__,
            )
            raise

    # Return appropriate wrapper based on whether function is async
    if inspect.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper
