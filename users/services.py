import random
import time
import string
from users.models import User


def send_verification_code(phone_number: str) -> str:
    """
    Эмуляция отправки SMS. Возвращает 4-значный код

    """
    code = str(random.randint(1000, 9999))
    time.sleep(random.uniform(1, 2))
    print(f"=== SMS на {phone_number}: код {code} ===")
    return code


def generate_invite_code() -> str:
    """
    Генерирет 6-значный инвайт код из букв и цифр.

    """

    chars = string.ascii_letters + string.digits
    while True:
        code = ''.join(random.choice(chars, k=6))
        if not User.objects.filter(invite_code=code).exclude():
            return code
