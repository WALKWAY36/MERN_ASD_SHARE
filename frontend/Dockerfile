FROM node:18-alpine AS build

WORKDIR /app

# Копируем package.json
COPY package*.json ./

# Устанавливаем зависимости с флагами для решения конфликтов
RUN npm install --legacy-peer-deps --force

# Устанавливаем недостающий модуль явно
RUN npm install ajv@8.12.0 --legacy-peer-deps

# Копируем исходный код
COPY . .

# Проверяем структуру
RUN ls -la /app/public/ 2>/dev/null || echo "public folder not found"
RUN ls -la /app/src/ 2>/dev/null || echo "src folder not found"

# Собираем проект
RUN npm run build

# Production стадия с nginx
FROM nginx:alpine

# Копируем кастомный конфиг nginx
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Копируем собранные файлы
COPY --from=build /app/build /usr/share/nginx/html/autmama

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]