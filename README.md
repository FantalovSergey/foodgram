# Описание
Проект «Фудграм» — сайт, на котором пользователи могут публиковать свои рецепты, добавлять рецепты других авторов в избранное и подписываться на их публикации. Также пользователям доступен сервис «Список покупок». Он позволяет создавать список продуктов, которые нужно купить для приготовления выбранных блюд.

# Ссылки
- https://foodgram-sf.dynnamn.ru - главная страница
- https://foodgram-sf.dynnamn.ru/api/docs/ - полный список типовых запросов к API и ответов на эти запросы

# Установка
Cоздайте файл .env со следующими переменными:
- DJANGO_SECRET_KEY - секретный ключ Django
- DEBUG - логическая переменная, определяющая, находится ли проект в режиме отладки
- ALLOWED_HOSTS - список разрешённых хостов (разделены пробелом)
- CSRF_TRUSTED_ORIGINS - список доверенных источников для CSRF-защиты (например, https://*.your_host; разделять пробелом, если несколько источников)
- POSTGRES_DB - имя базы данных POSTGRE
- POSTGRES_USER - имя пользователя базы данных POSTGRE
- POSTGRES_PASSWORD - пароль для подключения к базе данных POSTGRE
- DB_HOST - хост базы данных POSTGRE
- DB_PORT - порт базы данных POSTGRE

## Установка на локальном компьютере:
- Разместите файл .env в директории /backend/
- Находясь в корневой директории проекта командами в терминале запустите docker compose

```
docker compose up -d
```

- примените миграции

```
docker compose exec backend python manage.py migrate
```

- соберите статику для админ-зоны

```
docker compose exec backend python manage.py collectstatic --no-input
```

- при необходимости импортируйте ингредиенты в базу данных 

```
docker compose exec backend python manage.py import_ingredients
```


## Установка на удалённом сервере:
- Откройте файл конфигурации веб-сервера, выполнив команду

```
sudo nano /etc/nginx/sites-enabled/default
```

- Установите перенаправление запросов в контейнер nginx следующей записью

```
server {
    server_name your_host;

    location / {
        proxy_set_header Host $http_host;
        proxy_pass http://127.0.0.1:8800;
        client_max_body_size 10M;
    }
}
```
- В директории home/username/ создайте директорию foodgram/, перейдите в неё, разместите в ней файлы .env и docker-compose.production.yml
- Командами в терминале загрузите докер-образы из dockerhub

```
sudo docker compose -f docker-compose.production.yml pull
```

- удалите контейнеры

```
sudo docker compose -f docker-compose.production.yml down
```

- запустите docker compose

```
sudo docker compose -f docker-compose.production.yml up -d
```

- примените миграции

```
sudo docker compose -f docker-compose.production.yml exec backend python manage.py migrate
```

- соберите статику для админ-зоны

```
sudo docker compose -f docker-compose.production.yml exec backend python manage.py collectstatic --no-input
```

- при необходимости импортируйте ингредиенты в базу данных

```
sudo docker compose -f docker-compose.production.yml exec backend python manage.py import_ingredients
```

удалите неиспользуемые докер-образы

```
sudo docker image prune -af
```

# Стек
- Node.js 21.7.1
- Python 3.12
- Nginx 1.25.4
- Docker 4.42.1
- Github Actions
- Django REST framework
- djoser

# Об авторе
Студент факультета Бэкенд платформы Яндекс.Практикум [Фанталов Сергей](https://github.com/FantalovSergey).
