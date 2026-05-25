import logging
import os

# Create a logs/ directory if it doesn't exist
os.makedirs('logs', exist_ok=True)

def get_logger(name):
    """
    Returns a configured logger for any module that needs it.
    Logs to both the console AND a file simultaneously.

    Usage:
        from orders.logger import get_logger
        logger = get_logger(__name__)
        logger.info("Order created")
        logger.error("Payment failed")
    """
    logger = logging.getLogger(name)

    # Avoid adding duplicate handlers if logger already exists
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)

    # ── Console Handler ──────────────────────────────────────
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)

    # ── File Handler ─────────────────────────────────────────
    file_handler = logging.FileHandler('logs/orders.log')
    file_handler.setLevel(logging.INFO)

    # ── Format ───────────────────────────────────────────────
    formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)s %(name)s — %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger