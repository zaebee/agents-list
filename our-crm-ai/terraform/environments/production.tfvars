# Production environment configuration
environment = "production"
aws_region = "us-west-2"

# Domain configuration
domain_name = "app.aicrm.com"

# Database configuration
database_instance_class = "db.t3.small"

# Auto-scaling configuration
min_capacity = 2
max_capacity = 10

# High availability and security settings
enable_deletion_protection = true