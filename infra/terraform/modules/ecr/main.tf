resource "aws_ecr_repository" "repo" {
  name                 = var.repository_name
  image_tag_mutability = "MUTABLE"
  force_delete         = true

  image_scanning_configuration {
    scan_on_push = false
  }
}

# Build and push Lambda images with proper architecture settings
resource "null_resource" "lambda_images" {
  triggers = {
    # Trigger rebuild when any Lambda code changes
    extract_code  = filemd5("${path.root}/../../src/lambdas/extract/lambda_function.py")
    transform_code = filemd5("${path.root}/../../src/lambdas/transform/lambda_function.py")
    monitor_code  = filemd5("${path.root}/../../src/lambdas/monitor/lambda_function.py")
    alert_code    = filemd5("${path.root}/../../src/lambdas/alert/lambda_function.py")
  }

  provisioner "local-exec" {
    command = <<EOF
      aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin ${aws_ecr_repository.repo.repository_url}
      cd ${path.root}/../..
      
      # Remove existing builder if it exists
      docker buildx rm lambda-builder || true
      
      # Create new builder for multi-platform builds
      docker buildx create --use --name lambda-builder || true
      
      # Build and push all Lambda images with proper architecture settings
      docker buildx build --platform linux/amd64 --provenance=false --sbom=false --push -t ${aws_ecr_repository.repo.repository_url}:extract-v1 -f src/lambdas/extract/Dockerfile .
      docker buildx build --platform linux/amd64 --provenance=false --sbom=false --push -t ${aws_ecr_repository.repo.repository_url}:transform-v1 -f src/lambdas/transform/Dockerfile .
      docker buildx build --platform linux/amd64 --provenance=false --sbom=false --push -t ${aws_ecr_repository.repo.repository_url}:monitor-v1 -f src/lambdas/monitor/Dockerfile .
      docker buildx build --platform linux/amd64 --provenance=false --sbom=false --push -t ${aws_ecr_repository.repo.repository_url}:alert-v1 -f src/lambdas/alert/Dockerfile .
    EOF
  }
}

# Wait for images to be built before Lambda config runs
data "aws_ecr_image" "extract_image" {
  depends_on = [null_resource.lambda_images]
  repository_name = aws_ecr_repository.repo.name
  image_tag       = "extract-v1"
}

data "aws_ecr_image" "transform_image" {
  depends_on = [null_resource.lambda_images]
  repository_name = aws_ecr_repository.repo.name
  image_tag       = "transform-v1"
}

data "aws_ecr_image" "monitor_image" {
  depends_on = [null_resource.lambda_images]
  repository_name = aws_ecr_repository.repo.name
  image_tag       = "monitor-v1"
}

data "aws_ecr_image" "alert_image" {
  depends_on = [null_resource.lambda_images]
  repository_name = aws_ecr_repository.repo.name
  image_tag       = "alert-v1"
}

output "repository_url" {
  value = aws_ecr_repository.repo.repository_url
}

output "extract_image_uri" {
  value = "${aws_ecr_repository.repo.repository_url}:${data.aws_ecr_image.extract_image.image_tag}"
}

output "transform_image_uri" {
  value = "${aws_ecr_repository.repo.repository_url}:${data.aws_ecr_image.transform_image.image_tag}"
}

output "monitor_image_uri" {
  value = "${aws_ecr_repository.repo.repository_url}:${data.aws_ecr_image.monitor_image.image_tag}"
}

output "alert_image_uri" {
  value = "${aws_ecr_repository.repo.repository_url}:${data.aws_ecr_image.alert_image.image_tag}"
}