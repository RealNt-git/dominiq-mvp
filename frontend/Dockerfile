# frontend/Dockerfile
FROM node:18-alpine as build

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .
RUN npm run build

# Второй этап для запуска dev-сервера (для разработки)
FROM node:18-alpine

WORKDIR /app

COPY --from=build /app /app

EXPOSE 5173

CMD ["npm", "run", "dev", "--", "--host"]