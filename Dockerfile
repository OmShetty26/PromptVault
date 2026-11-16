
# Stage 1: Build the React frontend
FROM node:24-slim AS frontend-build

WORKDIR /frontend

COPY frontend/package*.json ./

RUN npm ci --include=optional

COPY frontend/ ./

RUN npm run build


# Stage 2: Build the FastAPI application
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install production backend dependencies only
COPY backend/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Copy the backend application
COPY backend/ .

# Copy the compiled React application into the backend
COPY --from=frontend-build /frontend/dist ./static

EXPOSE 10000

# Use Render's PORT variable, with 10000 as the local default
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-10000}"]
