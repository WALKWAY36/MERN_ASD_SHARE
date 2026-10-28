# Запуск проекта

## Предварительные требования

1. Установите Docker Desktop:
   - Windows: https://docs.docker.com/desktop/install/windows-install/
   - Mac: https://docs.docker.com/desktop/install/mac-install/
   - Linux: https://docs.docker.com/desktop/install/linux-install/

2. Убедитесь, что Docker запущен (иконка в трее)

## Подготовка

1. Распакуйте архив с проектом
2. Поместите файлы моделей в соответствующие папки:
   - Модели: `ml-service/models/`
   - Датасет: `ml-service/dataset/`

## Запуск

### Первый запуск (займет 5-10 минут):
```bash
docker-compose up --build
```

### Пользовательский интерфейс
Перейти в бразуер и ввести в адресную строку: `http://127.0.0.1:3000/autmama/`

Далее авторизироваться:
login: `admin@mail.ru`
pass: `!oRka12*`