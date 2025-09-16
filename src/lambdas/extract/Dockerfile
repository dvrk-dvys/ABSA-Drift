FROM public.ecr.aws/lambda/python:3.10
LABEL authors="jharr"

RUN pip install --upgrade pip

COPY ["src/lambdas/extract/requirements.txt", "./"]

# Add awslambdaric for local Lambda testing
RUN pip install --no-cache-dir -r requirements.txt awslambdaric

COPY ["src/lambdas/extract/lambda_function.py", "./"]
COPY ["src/utils/", "./src/utils/"]
COPY ["src/__init__.py", "./src/"]

CMD ["lambda_function.lambda_handler"]

# Build: docker build -t absa-extract:v1 .
# Run: docker run -it --rm -p 8080:8080 -v ~/.aws:/root/.aws absa-extract:v1