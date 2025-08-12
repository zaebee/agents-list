# AI-CRM Phase 2A Infrastructure

This directory contains Terraform configurations for deploying AI-CRM Phase 2A to AWS.

## Architecture

The infrastructure includes:

- **VPC** with public/private subnets across 2 AZs
- **Application Load Balancer** for high availability
- **ECS Fargate** for containerized application deployment
- **RDS PostgreSQL** for database storage
- **ElastiCache Redis** for caching and sessions
- **Secrets Manager** for secure API key storage
- **S3** for file storage
- **Auto Scaling** based on CPU utilization
- **CloudWatch** for logging and monitoring

## Prerequisites

1. AWS CLI configured with appropriate permissions
2. Terraform >= 1.0 installed
3. Docker configured for CI/CD pipeline

## Deployment Steps

### 1. Initialize Terraform Backend

First, create the S3 bucket and DynamoDB table for state management:

```bash
# Create S3 bucket for state
aws s3 mb s3://aicrm-terraform-state --region us-west-2

# Enable versioning
aws s3api put-bucket-versioning \
  --bucket aicrm-terraform-state \
  --versioning-configuration Status=Enabled

# Create DynamoDB table for state locking
aws dynamodb create-table \
  --table-name aicrm-terraform-locks \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --provisioned-throughput ReadCapacityUnits=5,WriteCapacityUnits=5 \
  --region us-west-2
```

### 2. Initialize Terraform

```bash
cd terraform
terraform init
```

### 3. Deploy Staging Environment

```bash
# Plan the deployment
terraform plan -var-file="environments/staging.tfvars" -out=staging.tfplan

# Apply the plan
terraform apply staging.tfplan
```

### 4. Deploy Production Environment

```bash
# Plan the deployment
terraform plan -var-file="environments/production.tfvars" -out=production.tfplan

# Apply the plan
terraform apply production.tfplan
```

### 5. Configure Secrets

After deployment, add your API keys to AWS Secrets Manager:

```bash
# Anthropic API Key
aws secretsmanager put-secret-value \
  --secret-id aicrm-staging-anthropic-api-key \
  --secret-string "your_anthropic_api_key"

# Stripe Secret Key
aws secretsmanager put-secret-value \
  --secret-id aicrm-staging-stripe-secret-key \
  --secret-string "your_stripe_secret_key"

# JWT Secret Key
aws secretsmanager put-secret-value \
  --secret-id aicrm-staging-jwt-secret-key \
  --secret-string "your_jwt_secret_key"
```

## Environment Variables

The following environment variables are available in the ECS container:

- `ENVIRONMENT`: Environment name (staging/production)
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `ANTHROPIC_API_KEY`: From Secrets Manager
- `STRIPE_SECRET_KEY`: From Secrets Manager
- `JWT_SECRET_KEY`: From Secrets Manager

## Monitoring

- **CloudWatch Logs**: `/ecs/aicrm-[environment]`
- **CloudWatch Metrics**: ECS service metrics, RDS metrics, ALB metrics
- **Health Checks**: ALB health check on `/health` endpoint

## Scaling

Auto-scaling is configured to:
- Scale up when CPU > 70%
- Scale down when CPU < 30%
- Min capacity: 1-2 tasks (staging/production)
- Max capacity: 3-10 tasks (staging/production)

## Security

- All resources are deployed in private subnets
- Security groups restrict access to necessary ports only
- Database and Redis are not publicly accessible
- API keys stored in AWS Secrets Manager
- S3 bucket has server-side encryption enabled

## Cost Optimization

Staging environment uses:
- `db.t3.micro` RDS instance
- `cache.t3.micro` ElastiCache instance
- Deletion protection disabled

Production environment uses:
- `db.t3.small` RDS instance
- Higher capacity auto-scaling
- Deletion protection enabled

## Cleanup

To destroy the infrastructure:

```bash
# Staging
terraform destroy -var-file="environments/staging.tfvars"

# Production
terraform destroy -var-file="environments/production.tfvars"
```

## Troubleshooting

### Common Issues

1. **ECS Tasks Failing**: Check CloudWatch logs for container errors
2. **Database Connection Issues**: Verify security groups and connection string
3. **Load Balancer 503 Errors**: Check target group health status
4. **Secrets Access**: Ensure ECS task role has permission to access secrets

### Useful Commands

```bash
# View ECS service status
aws ecs describe-services --cluster aicrm-staging-cluster --services aicrm-staging-service

# Check RDS status
aws rds describe-db-instances --db-instance-identifier aicrm-staging-postgres

# View ALB target health
aws elbv2 describe-target-health --target-group-arn [TARGET_GROUP_ARN]

# Check secrets
aws secretsmanager get-secret-value --secret-id aicrm-staging-anthropic-api-key
```