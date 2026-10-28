FROM node:18-alpine

WORKDIR /app

RUN apk add --no-cache --update python3 make g++ sqlite-dev sqlite-libs

COPY package*.json ./
RUN npm install --legacy-peer-deps

COPY . .

RUN mkdir -p files static dataset data

EXPOSE 5000

CMD ["node", "index.js"]