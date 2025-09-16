FROM public.ecr.aws/lambda/python:3.10
LABEL authors="jharr"

RUN pip install --upgrade pip

COPY ["src/lambdas/alert/requirements.txt", "./"]

# Add awslambdaric for local Lambda testing
RUN pip install --no-cache-dir -r requirements.txt awslambdaric

COPY ["src/lambdas/alert/lambda_function.py", "./"]

CMD ["lambda_function.lambda_handler"]

# Build: docker build -t absa-alert:v1 .
# Run: docker run -it --rm -p 8083:8080 -v ~/.aws:/root/.aws absa-alert:v1