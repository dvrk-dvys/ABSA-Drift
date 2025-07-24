FROM python:3.10-slim
LABEL authors="jharr"


WORKDIR /app
RUN pip install --upgrade pip

COPY ["requirements.txt", "./"]

RUN pip install --no-cache-dir -r requirements.txt

RUN mkdir -p /app/mlflow_data

EXPOSE 5001

CMD ["mlflow", "server", \
     "--backend-store-uri=sqlite:///mlflow_data/mlflow.db", \
     "--default-artifact-root=s3://absa-drift-models/mlflow", \
     "--host=0.0.0.0", \
     "--port=5001"]