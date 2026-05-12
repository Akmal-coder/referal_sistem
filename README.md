# referal-sistem -Это сервис авторизации по номеру телефона

Реферальная система с авторизацией по номеру телефона и инвайт-кодами.

## Технологии
- **Python 3.13** + **Django 6.0** + **Django REST Framework**
- **JWT** (djangorestframework-simplejwt)
- **PostgreSQL** (в Docker) / SQLite (для тестов)
- **Docker** + docker-compose
- **drf-spectacular** — Swagger/ReDoc автодокументация

## Установка и запуск (Docker)
Убедиться, что установлен Docker Desktop и он запущен



# Клонировать репозиторий
git clone git@github.com:Akmal-coder/referal_sistem.git
cd referal_sistem

# Собрать и запустить контейнер (PostgreSQL + Django)
docker-compose up -d --build

# Применить миграции
docker-compose exec web python manage.py migrate

# Открыть в браузере
# Интерфейс: http://127.0.0.1:8000/api/auth/
# Swagger:   http://127.0.0.1:8000/api/docs/


# Запуск тестов
docker-compose exec web python manage.py test users



# API
Метод	                URL	                            Назначение
POST	        /api/auth/send-code/	                Отправить SMS-код на телефон
POST	        /api/auth/verify-code/	                Подтвердить код, получить JWT
GET	            /api/profile/	                        Профиль пользователя
POST	        /api/profile/activate-invite/	        Активировать чужой инвайт-код


# Примеры запросов
Отправка кода:
json
POST /api/auth/send-code/
{"phone_number": "+79991234567"}
→ {"message": "Код отправлен на +79991234567"}


# Верификация:
json
POST /api/auth/verify-code/
{"phone_number": "+79991234567", "code": "1234"}
→ {"access": "eyJ...", "refresh": "eyJ..."}

# Профиль:
json
GET /api/profile/
Authorization: Bearer <access_token>
→ {"phone_number": "+7999...", "invite_code": "AbCd12", "activated_invite_code": null, "referrals": []}


# Активация инвайт-кода:
json
POST /api/profile/activate-invite/
Authorization: Bearer <access_token>
{"invite_code": "kp14b6"}
→ {"message": "Инвайт-код kp14b6 активирован"}