# Hello World Flask Application with JSON Logging

A simple Python Flask application with JSON logging, designed for deployment on AWS Fargate.

## Features

- 🚀 Simple "Hello World" web application
- 📝 JSON structured logging using `python-json-logger`
- 🔍 Multiple endpoints (web, API, health check, info)
- 🐳 Docker containerized
- ☁️ Ready for AWS Fargate deployment
- 🎨 Beautiful, modern UI
- 📦 Uses popular Python libraries (Flask, requests, python-dotenv)

## Endpoints

- `/` - Main hello world page with beautiful UI
- `/api/hello` - JSON API endpoint
- `/health` - Health check endpoint (for AWS load balancer)
- `/info` - Application information endpoint

## Local Development

### Prerequisites

- Python 3.11+
- pip

### Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the application:
```bash
python app.py
```

3. Visit `http://localhost:8080` in your browser

### Docker Local Testing

1. Build the Docker image:
```bash
docker build -t hello-world-app .
```

2. Run the container:
```bash
docker run -p 8080:8080 hello-world-app
```

3. Visit `http://localhost:8080`

## AWS Fargate Deployment Guide (Using AWS Console UI)

### Step 1: Push Docker Image to Amazon ECR

1. **Create ECR Repository**:
   - Go to AWS Console → Amazon ECR
   - Click "Create repository"
   - Repository name: `hello-world-app`
   - Click "Create repository"

2. **Build and Push Image**:
   - Click on your repository name
   - Click "View push commands"
   - Follow the commands shown (example below):

```bash
# Authenticate Docker to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <YOUR_AWS_ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com

# Build your image
docker build -t hello-world-app .

# Tag your image
docker tag hello-world-app:latest <YOUR_AWS_ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/hello-world-app:latest

# Push to ECR
docker push <YOUR_AWS_ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/hello-world-app:latest
```

### Step 2: Create ECS Cluster

1. Go to AWS Console → Amazon ECS
2. Click "Clusters" → "Create cluster"
3. **Cluster configuration**:
   - Cluster name: `hello-world-cluster`
   - Infrastructure: Select "AWS Fargate (serverless)"
4. Click "Create"

### Step 3: Create Task Definition

1. In ECS Console, click "Task Definitions" → "Create new task definition"
2. **Task definition configuration**:
   - Task definition family: `hello-world-task`
   - Launch type: `AWS Fargate`
   - Operating system: `Linux`
   - Task size:
     - CPU: `0.25 vCPU` (256)
     - Memory: `0.5 GB` (512)
   
3. **Container configuration**:
   - Container name: `hello-world-container`
   - Image URI: `<YOUR_AWS_ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/hello-world-app:latest`
   - Port mappings:
     - Container port: `8080`
     - Protocol: `TCP`
     - App protocol: `HTTP`
   - Environment variables (optional):
     - Key: `ENVIRONMENT`, Value: `production`
   
4. **Log configuration**:
   - Enable "Use log collection"
   - Log driver: `awslogs`
   - This will automatically create a CloudWatch log group

5. Click "Create"

### Step 4: Create Application Load Balancer (ALB)

1. Go to AWS Console → EC2 → Load Balancers
2. Click "Create Load Balancer" → "Application Load Balancer"
3. **Basic configuration**:
   - Name: `hello-world-alb`
   - Scheme: `Internet-facing`
   - IP address type: `IPv4`
   
4. **Network mapping**:
   - VPC: Select your VPC
   - Availability Zones: Select at least 2 subnets in different AZs
   
5. **Security groups**:
   - Create new security group or select existing
   - Allow inbound HTTP (port 80) from anywhere (0.0.0.0/0)
   
6. **Listeners and routing**:
   - Protocol: `HTTP`, Port: `80`
   - Create new target group:
     - Target type: `IP addresses`
     - Target group name: `hello-world-tg`
     - Protocol: `HTTP`, Port: `8080`
     - VPC: Select your VPC
     - Health check path: `/health`
     - Click "Create target group"
   
7. Click "Create load balancer"

### Step 5: Create and Run ECS Service

1. Go to ECS Console → Clusters → `hello-world-cluster`
2. Click "Services" tab → "Create"
3. **Environment**:
   - Compute options: `Launch type`
   - Launch type: `FARGATE`
   
4. **Deployment configuration**:
   - Application type: `Service`
   - Task definition: `hello-world-task` (latest)
   - Service name: `hello-world-service`
   - Desired tasks: `2` (for high availability)
   
5. **Networking**:
   - VPC: Select your VPC
   - Subnets: Select at least 2 subnets
   - Security group:
     - Create new or use existing
     - Allow inbound traffic on port 8080 from ALB security group
   - Public IP: `Turned on`
   
6. **Load balancing**:
   - Load balancer type: `Application Load Balancer`
   - Select existing: `hello-world-alb`
   - Listener: Use existing `80:HTTP`
   - Target group: `hello-world-tg`
   - Health check grace period: `30` seconds
   
7. Click "Create"

### Step 6: Access Your Application

1. Wait 2-3 minutes for tasks to start and become healthy
2. Go to EC2 → Load Balancers → `hello-world-alb`
3. Copy the DNS name (e.g., `hello-world-alb-123456789.us-east-1.elb.amazonaws.com`)
4. Open in browser: `http://<ALB_DNS_NAME>`

### Step 7: View Logs

1. Go to CloudWatch → Log groups
2. Find log group: `/ecs/hello-world-task`
3. View JSON formatted logs from your application

## Security Group Configuration

### ALB Security Group
- **Inbound**: HTTP (80) from 0.0.0.0/0
- **Outbound**: All traffic to Fargate security group

### Fargate Security Group
- **Inbound**: Port 8080 from ALB security group
- **Outbound**: All traffic (for pulling images and external requests)

## Cost Optimization Tips

1. **Use Fargate Spot** for non-production workloads (up to 70% savings)
2. **Right-size tasks**: Start with 0.25 vCPU / 0.5 GB and adjust based on metrics
3. **Auto-scaling**: Configure based on CPU/memory utilization
4. **Delete resources** when not in use:
   - Delete ECS Service
   - Delete ECS Cluster
   - Delete Load Balancer
   - Delete Target Group
   - Delete ECR images

## Monitoring

- **CloudWatch Logs**: View JSON structured logs
- **ECS Metrics**: Monitor CPU, memory, task count
- **ALB Metrics**: Monitor request count, latency, errors
- **Container Insights**: Enable for detailed container metrics

## Troubleshooting

### Tasks not starting
- Check task definition has correct image URI
- Verify ECR permissions (task execution role)
- Check CloudWatch logs for errors

### Health checks failing
- Verify `/health` endpoint is accessible
- Check security group allows traffic on port 8080
- Increase health check grace period

### Cannot access application
- Verify ALB DNS name is correct
- Check ALB listener is configured for port 80
- Verify target group has healthy targets
- Check security groups allow traffic

## Environment Variables

- `PORT`: Application port (default: 8080)
- `ENVIRONMENT`: Environment name (development/production)

## Libraries Used

- **Flask**: Web framework
- **python-json-logger**: JSON structured logging
- **requests**: HTTP library (used in health checks)
- **python-dotenv**: Environment variable management
- **gunicorn**: Production WSGI server

## License

MIT License

