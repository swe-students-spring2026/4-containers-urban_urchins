FROM python:3.10-bookworm

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    g++ \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libgomp1 \
    libgl1 \
    && rm -rf /var/lib/apt/lists/*

COPY Pipfile Pipfile.lock ./

RUN pip install pipenv && \
    pipenv verify && \
    pipenv sync --system

COPY . .

EXPOSE 5000

CMD ["python", "app.py"]
