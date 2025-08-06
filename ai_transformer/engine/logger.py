import logging

def get_logger(name='ai_transformer'):
    logger = logging.getLogger(name)

    if not logger.hasHandlers():
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '[%(levelname)s] [%(name)s] [%(context)s] %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    logger.setLevel(logging.INFO)
    logger = ContextLogger(logger)
    return logger


class ContextLogger:
    """
    Wraps a logger to add 'context' field to every log entry.
    """

    def __init__(self, base_logger):
        self._logger = base_logger

    def _log(self, level, msg, context='-'):
        extra = {'context': context}
        self._logger.log(level, msg, extra=extra)

    def debug(self, msg, context='-'):
        self._log(logging.DEBUG, msg, context)

    def info(self, msg, context='-'):
        self._log(logging.INFO, msg, context)

    def warning(self, msg, context='-'):
        self._log(logging.WARNING, msg, context)

    def error(self, msg, context='-'):
        self._log(logging.ERROR, msg, context)

    def critical(self, msg, context='-'):
        self._log(logging.CRITICAL, msg, context)
