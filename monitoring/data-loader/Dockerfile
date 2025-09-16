FROM python:3.10-slim

WORKDIR /app

COPY monitoring/data-loader/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY monitoring/data-loader/data_loader.py .
COPY monitoring/data-loader/init_db.sql .

CMD ["python", "data_loader.py"]