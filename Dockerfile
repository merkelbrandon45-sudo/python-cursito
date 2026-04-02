FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir gunicorn

COPY . .

EXPOSE 8000

# APP_MODULE can be overridden in the hosting service settings.
ENV APP_MODULE=app:app

CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:${PORT:-8000} ${APP_MODULE} --workers 2 --timeout 120"]
