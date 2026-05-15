import random
import time
import logging

logger = logging.getLogger(__name__)


def send_verification_code(phone_number: str) -> str:
    """Эмуляция отправки SMS. Возвращает 4-значный код."""
    code = str(random.randint(1000, 9999))
    time.sleep(random.uniform(1, 2))
    logger.info("SMS sent to %s: code %s", phone_number, code)
    return code
