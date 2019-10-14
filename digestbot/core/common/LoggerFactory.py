import sys
import logging


def create_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """
    Create and return new logger (for settings unification)

    :param name: name of logger
    :param level: logging level
    :return: logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%m.%d.%Y-%I:%M:%S",
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger
