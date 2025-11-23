#!/bin/bash
echo "Инициализация проекта..."

# Запуск PostgreSQL
docker-compose up -d postgres
echo "PostgreSQL запущен"

# Ждем запуска БД
sleep 5

# Создаем таблицы
cd backend/database
python init_database.py
echo "Таблицы созданы"

# Возвращаемся в корень
cd ../..
echo "Проект готов к работе!"