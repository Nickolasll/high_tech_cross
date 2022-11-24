#!/usr/bin/sh
# Этот файл предназначен для первоначальной настройки на локальной машине.
# Подразумевается, что один раз запустил и все настроено и готово к работе.

# install postgres
sudo apt install python3-pip python3-dev libpq-dev postgresql postgresql-contrib

# manage postgres database and user
# в продакшене так, конечно же делать нельзя, нужен докер и environments в которых будут лежать пароли
sudo -u postgres psql -c "create database backend;"
sudo -u postgres psql -c "CREATE USER admin WITH PASSWORD 'admin';"
sudo -u postgres psql -c "ALTER ROLE admin SET client_encoding TO 'utf8';"
sudo -u postgres psql -c "ALTER ROLE admin SET default_transaction_isolation TO 'read committed';"
sudo -u postgres psql -c "ALTER ROLE admin SET timezone TO 'UTC';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE backend TO admin;"
sudo -u postgres psql -c "ALTER USER admin CREATEDB;"

# install requirements
sudo pip3 install -r ./requirements.txt

# django stuff
python3 manage.py makemigrations
python3 manage.py migrate
DJANGO_SUPERUSER_USERNAME=admin DJANGO_SUPERUSER_PASSWORD=admin DJANGO_SUPERUSER_EMAIL="admin@admin.com" python3 manage.py createsuperuser --noinput

# применяем фикстуру
python3 manage.py loaddata initial
# я сделал специальную команду, чтобы создавалось актуальное текущее соревнование с прогрессом команд
python3 manage.py init
