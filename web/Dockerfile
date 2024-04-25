FROM python:3.9-alpine

WORKDIR /app

COPY . .

RUN pip install -r requirements.txt

USER python
EXPOSE 8000
CMD ["python3", "main.py"]