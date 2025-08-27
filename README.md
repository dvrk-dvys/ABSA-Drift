## Code snippets

### Building and running Docker images



please export your aws env variables first

export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret  
export AWS_DEFAULT_REGION=us-east-1


```
mlflow server \
  --backend-store-uri=sqlite:///mlflow.db \
  --default-artifact-root=s3://absa-drift-models/mlflow \
  --host 0.0.0.0 \
  --port 5001
```
  http://127.0.0.1:5001

```
docker-compose build
docker-compose up -d
```








#--------------------------------------------------------
```
# docker build -t lambda-func-duration:v1 .                                                                                             ─╯
```

```
docker run -it --rm \
    -p 8080:8080 \
    -e PREDICTIONS_STREAM_NAME="ride_predictions" \
    -e TEST_RUN="True" \
    -e AWS_DEFAULT_REGION="us-east-1" \
    -v ~/.aws:/root/.aws \
    lambda-func-duration:v1
```

```
# First time: Build and start
docker-compose up --build

# Or separately:
docker-compose build
docker-compose up -d

# Subsequent times: Just start (if no code changes)
docker-compose up -d

docker-compose down

```

```
hooks

pip install pre-commit black isort pylint pytest
pre-commit install
```


```
!!! start the docker daemon 1st !!!

terraform init
terraform plan  #source-stream-name : ride-events-stg
terraform apply


var.model_bucket
  s3_bucket

  Enter a value: stg-mlflow-models

var.output_stream_name
  Enter a value: stg_ride_predictions

var.source_stream_name
  Enter a value: stg_ride_events
```

```

# Switch back to staging state and destroy
terraform init -backend-config="key=mlops-zoomcamp-stg.tfstate"
terraform destroy -var-file="vars/stg.tfvars" -auto-approve

# Then create production fresh
terraform init -backend-config="key=mlops-zoomcamp-prod.tfstate"
terraform apply -var-file="vars/prod.tfvars"



this is proper name of the ecr repo
prod_stream_model_duration_mlops-zoomcamp
├── latest (Docker image tag)
├── v1.0 (another possible tag)
└── sha256-abc123... (image by digest)

watch the hyphen and the underscores
```



Dont forget to create the s3 buckets for the comment sections raw data to then be put inot inference

in my project i am not using kinessis streams because i am doing batch processing  or the comments. no need for live 

the reason why i went with parquet uploads to s3 is because the s3 data needs to be preprocessed for nlp data first. 

the pre processor uploads to parquet in a patch with create a directory of parquets
# If you want to upload the entire partitioned directory
aws s3 sync /path/to/absa_debug_train_dataframe.parquet/ s3://absa-drift-data/hourly_comments/2025_07_30_14/ --exclude "*" --include "part-*.parquet"


!using an s3 uri automatically writes the df to s3! how elegant!

'URI as path
When you pass a path that starts with s3://…, pandas (via the chosen parquet engine—usually PyArrow or Fastparquet—and fsspec with s3fs) recognizes that it needs to write to S3 rather than local disk.'
final_df.to_parquet(s3_uri, index=False)


