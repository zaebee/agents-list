# 🚀 Deployment Guide

This guide provides instructions for deploying the AI-CRM system to a production environment. The recommended deployment strategy uses Docker Compose for container orchestration and Terraform for infrastructure as code on AWS.

## 📋 Table of Contents

1. [Deployment Overview](#-deployment-overview)
2. [Prerequisites](#-prerequisites)
3. [Infrastructure Provisioning (Terraform)](#-infrastructure-provisioning-terraform)
4. [Application Deployment (Docker Compose)](#-application-deployment-docker-compose)
5. [Post-Deployment Steps](#-post-deployment-steps)
6. [Security & SSL](#-security--ssl)
7. [Monitoring](#-monitoring)
8. [Troubleshooting](#-troubleshooting)

## 🎯 Deployment Overview

The production architecture consists of the following components:

- **AWS**: The primary cloud provider for hosting the infrastructure.
- **Terraform**: Used to define and provision the AWS infrastructure as code.
- **Docker Compose**: Used to build and run the application containers on the provisioned infrastructure.
- **NGINX**: Acts as a reverse proxy, handling SSL termination and routing traffic to the frontend and backend services.
- **Route53**: Manages the DNS for the `crm.zae.life` domain.

```mermaid
graph TD
    subgraph "AWS Cloud"
        A[Route53 (crm.zae.life)] --> B[Application Load Balancer]
        B --> C[NGINX Reverse Proxy]
        C --> D[Frontend Container (React)]
        C --> E[Backend Container (FastAPI)]
        E --> F[RDS (PostgreSQL)]
        E --> G[ElastiCache (Redis)]
    end
```

## 🛠️ Prerequisites

- **AWS Account**: An AWS account with the necessary permissions to create resources.
- **Terraform**: Terraform CLI installed on your local machine.
- **Docker & Docker Compose**: Docker and Docker Compose installed on your local machine.
- **Domain Name**: A registered domain name. This guide assumes you are using a subdomain of `zae.life`, but you can adapt it to your own domain.
- **YouGile API Key**: A valid YouGile API key.

## 🏗️ Infrastructure Provisioning (Terraform)

The Terraform configuration for this project is located in the `deployment/terraform/aws` directory.

1.  **Initialize Terraform**:
    ```bash
    cd deployment/terraform/aws
    terraform init
    ```

2.  **Configure Variables**:
    Create a `terraform.tfvars` file to provide values for the variables defined in `variables.tf`. At a minimum, you will need to provide your AWS region, access key, and secret key.

    **`terraform.tfvars`**
    ```hcl
    aws_region = "us-east-1"
    domain_name = "crm.zae.life"
    ```

3.  **Plan and Apply**:
    ```bash
    terraform plan
    terraform apply
    ```
    This will provision the necessary AWS resources, including VPC, subnets, security groups, EC2 instance, RDS database, and ElastiCache Redis instance.

## 🚀 Application Deployment (Docker Compose)

Once the infrastructure is provisioned, you can deploy the application using Docker Compose.

1.  **SSH into the EC2 Instance**:
    Use the EC2 instance's public IP address (from the Terraform output) to SSH into the server.

2.  **Clone the Repository**:
    ```bash
    git clone https://github.com/wshobson/agents.git
    cd agents/our-crm-ai
    ```

3.  **Configure Environment**:
    Create a `.env` file from the example and fill in the production values.
    ```bash
    cp .env.example .env
    nano .env
    ```
    Ensure you use the RDS and ElastiCache endpoints from the Terraform output.

4.  **Build and Run**:
    Use the production Docker Compose file to build and run the containers.
    ```bash
    docker-compose -f docker-compose.prod.yml up --build -d
    ```

## ✅ Post-Deployment Steps

1.  **DNS Configuration**:
    If you are not using Route53 to manage your domain, you will need to manually create an A record pointing your domain (`crm.zae.life`) to the public IP address of the EC2 instance.

2.  **Verify Deployment**:
    -   Open your browser and navigate to `https://crm.zae.life`. You should see the application's login page.
    -   Check the container logs for any errors: `docker-compose -f docker-compose.prod.yml logs -f`.

## 🔒 Security & SSL

-   **SSL**: The NGINX container is configured to automatically obtain and renew SSL certificates from Let's Encrypt.
-   **Security Groups**: The Terraform configuration creates security groups that restrict traffic to the necessary ports.
-   **Environment Variables**: All sensitive information, such as API keys and database credentials, should be stored in the `.env` file and not committed to version control.

## 📊 Monitoring

-   **AWS CloudWatch**: The Terraform configuration enables CloudWatch monitoring for the EC2 instance and RDS database.
-   **Health Checks**: The backend application provides `/health`, `/ready`, and `/live` endpoints for monitoring the application's status.

## 🔧 Troubleshooting

-   **Deployment Issues**: Check the Docker Compose logs for errors.
-   **Connection Issues**: Ensure that the security groups are configured correctly and that the application is running.
-   **SSL Issues**: Check the NGINX container logs for errors related to SSL certificate generation.
