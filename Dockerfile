FROM python:3.13-slim
WORKDIR /lab1

COPY . .

RUN useradd -m labuser && chown -R labuser:labuser /lab1
USER labuser

EXPOSE 1337
