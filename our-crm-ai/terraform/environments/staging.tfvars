# Staging environment configuration
environment = "staging"
aws_region = "us-west-2"

# Domain configuration
domain_name = "staging.aicrm.example.com"

# Database configuration
database_instance_class = "db.t3.micro"

# Auto-scaling configuration
min_capacity = 1
max_capacity = 3

# Cost optimization settings
enable_deletion_protection = false