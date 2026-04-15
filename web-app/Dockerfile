FROM python:3.10-bookworm

WORKDIR /app

COPY Pipfile Pipfile.lock ./

RUN pip install pipenv && \
    pipenv verify && \
    pipenv sync --system

COPY . .

EXPOSE 5000

CMD ["python", "app.py"]