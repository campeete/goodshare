import logging
import os
import sys

def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        level = getattr(logging, os.environ.get('LOG_LEVEL', 'DEBUG').upper(), logging.DEBUG)
        logger.setLevel(level)
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(level)
        formatter = logging.Formatter(
            fmt='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger

_root = get_logger('crisisfeed')

def log_request(endpoint, method, status, duration_ms=None):
    msg = f"REQUEST | {method} {endpoint} | {status}"
    if duration_ms:
        msg += f" | {duration_ms:.1f}ms"
    if status >= 500:
        _root.error(msg)
    elif status >= 400:
        _root.warning(msg)
    else:
        _root.info(msg)

def log_external_api(service, endpoint, success, detail=''):
    status = 'SUCCESS' if success else 'FAILED'
    _root.info(f"EXTERNAL_API | {service} | {endpoint} | {status} | {detail}")
