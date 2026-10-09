FROM node:22-alpine AS frontend
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY index.html vite.config.js ./
COPY public ./public
COPY src ./src
RUN npm run build

FROM python:3.13-slim
WORKDIR /app
COPY backend/requirements*.txt ./backend/
RUN pip install --no-cache-dir -r backend/requirements-integrations.txt
COPY backend ./backend
COPY --from=frontend /app/dist ./dist
RUN mkdir -p /app/backend/data && useradd --create-home internflow && chown -R internflow:internflow /app
USER internflow
EXPOSE 8000
CMD ["python", "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
