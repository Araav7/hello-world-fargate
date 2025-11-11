# 🐶 Datadog APM Integration Guide

This guide explains how to send **APM traces only** from your Flask application to Datadog.

## 📋 Table of Contents
- [What's Been Configured](#whats-been-configured)
- [How It Works](#how-it-works)
- [Local Testing](#local-testing)
- [AWS Fargate Deployment](#aws-fargate-deployment)
- [Viewing Traces in Datadog](#viewing-traces-in-datadog)
- [Troubleshooting](#troubleshooting)

---

## ✅ What's Been Configured

### 1. **Dependencies Added** (`requirements.txt`)
```
ddtrace>=2.14.0
```
This is the Datadog APM tracing library for Python.

### 2. **Application Instrumented** (`app.py`)
```python
from ddtrace import tracer, patch_all

# Initialize Datadog APM - patches Flask automatically
patch_all()

# Configure Datadog tracer
tracer.configure(
    hostname=os.getenv("DD_AGENT_HOST", "localhost"),
    port=int(os.getenv("DD_TRACE_AGENT_PORT", "8126")),
)
```

### 3. **Dockerfile Updated**
- Added environment variables for Datadog
- Changed CMD to use `ddtrace-run` wrapper

---

## 🔍 How It Works

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│  Your Flask Application (Fargate Task)                      │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │  Flask App (app.py)                                │    │
│  │  - Instrumented with ddtrace                       │    │
│  │  - Automatically captures:                         │    │
│  │    • HTTP requests                                 │    │
│  │    • Response times                                │    │
│  │    • Status codes                                  │    │
│  │    • Errors                                        │    │
│  └────────────────────┬───────────────────────────────┘    │
│                       │                                     │
│                       │ Sends traces via HTTP               │
│                       ▼                                     │
│  ┌────────────────────────────────────────────────────┐    │
│  │  Datadog Agent (Sidecar Container)                 │    │
│  │  - Receives traces on port 8126                    │    │
│  │  - Buffers and batches traces                      │    │
│  │  - Sends to Datadog backend                        │    │
│  └────────────────────────────────────────────────────┘    │
└─────────────────────────────┬───────────────────────────────┘
                              │
                              │ HTTPS
                              ▼
                    ┌─────────────────────┐
                    │  Datadog Backend    │
                    │  (intake.datadoghq) │
                    │  - Stores traces    │
                    │  - Processes data   │
                    │  - Shows in UI      │
                    └─────────────────────┘
```

### What Gets Traced Automatically

With `patch_all()`, ddtrace automatically instruments:
- ✅ **Flask** - All HTTP requests
- ✅ **Requests** library - External HTTP calls
- ✅ **Database queries** (if you add a DB)
- ✅ **Error tracking**

### Trace Data Captured

For each request, Datadog captures:
- **Span name**: `flask.request`
- **Resource**: `GET /`, `POST /api/hello`, etc.
- **Duration**: How long the request took
- **Status code**: 200, 404, 500, etc.
- **Tags**: service, env, version
- **Errors**: If any exceptions occurred

---

## 🧪 Local Testing

### Option 1: Using Datadog Agent Container (Recommended)

1. **Get your Datadog API Key**:
   - Go to https://app.datadoghq.com/organization-settings/api-keys
   - Copy your API key

2. **Run Datadog Agent**:
```bash
docker run -d \
  --name datadog-agent \
  -e DD_API_KEY=<YOUR_API_KEY> \
  -e DD_APM_ENABLED=true \
  -e DD_APM_NON_LOCAL_TRAFFIC=true \
  -e DD_SITE=datadoghq.com \
  -p 8126:8126 \
  gcr.io/datadoghq/agent:latest
```

3. **Run your Flask app**:
```bash
cd /Users/araavind.senthil/helloworld
source venv/bin/activate

# Set environment variables
export DD_AGENT_HOST=localhost
export DD_TRACE_AGENT_PORT=8126
export DD_SERVICE=hello-world-flask-app
export DD_ENV=local
export DD_VERSION=1.0.0

# Run the app
ddtrace-run python app.py
```

4. **Generate some traffic**:
```bash
# Make some requests
curl http://localhost:8080/
curl http://localhost:8080/api/hello
curl http://localhost:8080/health
curl http://localhost:8080/info
```

5. **View traces in Datadog**:
   - Go to https://app.datadoghq.com/apm/traces
   - You should see traces appearing within 1-2 minutes

### Option 2: Using Docker Compose (Easiest)

Create `docker-compose.yml`:
```yaml
version: '3.8'

services:
  datadog-agent:
    image: gcr.io/datadoghq/agent:latest
    environment:
      - DD_API_KEY=${DD_API_KEY}
      - DD_APM_ENABLED=true
      - DD_APM_NON_LOCAL_TRAFFIC=true
      - DD_SITE=datadoghq.com
    ports:
      - "8126:8126"
  
  flask-app:
    build: .
    ports:
      - "8080:8080"
    environment:
      - DD_AGENT_HOST=datadog-agent
      - DD_TRACE_AGENT_PORT=8126
      - DD_SERVICE=hello-world-flask-app
      - DD_ENV=local
      - DD_VERSION=1.0.0
    depends_on:
      - datadog-agent
```

Run:
```bash
export DD_API_KEY=<YOUR_API_KEY>
docker-compose up
```

---

## ☁️ AWS Fargate Deployment

### Architecture on Fargate

```
┌─────────────────────────────────────────────────────┐
│  ECS Task Definition                                 │
│                                                      │
│  ┌──────────────────────┐  ┌──────────────────────┐│
│  │ Container 1:         │  │ Container 2:         ││
│  │ Flask App            │  │ Datadog Agent        ││
│  │ (Port 8080)          │  │ (Port 8126)          ││
│  │                      │  │                      ││
│  │ Sends traces ────────┼──▶ Receives traces     ││
│  │ to localhost:8126    │  │ Sends to Datadog    ││
│  └──────────────────────┘  └──────────────────────┘│
│                                                      │
│  Shared network namespace (localhost works!)        │
└─────────────────────────────────────────────────────┘
```

### Step 1: Store Datadog API Key in AWS Secrets Manager

1. **Go to AWS Secrets Manager**:
   - Navigate to: https://console.aws.amazon.com/secretsmanager/

2. **Create Secret**:
   - Click "Store a new secret"
   - Secret type: "Other type of secret"
   - Key/value pairs:
     - Key: `DD_API_KEY`
     - Value: `<YOUR_DATADOG_API_KEY>`
   - Secret name: `datadog-api-key`
   - Click "Next" → "Next" → "Store"

3. **Copy the Secret ARN** (you'll need this):
   - Example: `arn:aws:secretsmanager:us-east-1:123456789:secret:datadog-api-key-AbCdEf`

### Step 2: Update ECS Task Definition

1. **Go to ECS Console** → Task Definitions → Your task → "Create new revision"

2. **Add Datadog Agent Container**:
   - Click "Add container"
   - Container name: `datadog-agent`
   - Image: `gcr.io/datadoghq/agent:latest`
   - Memory: `256` (soft limit)
   - Port mappings: `8126` (container port)
   - Environment variables:
     - `DD_APM_ENABLED` = `true`
     - `DD_APM_NON_LOCAL_TRAFFIC` = `true`
     - `DD_SITE` = `datadoghq.com`
     - `DD_ECS_FARGATE` = `true`
   - Secrets (from AWS Secrets Manager):
     - Name: `DD_API_KEY`
     - Value from: Select your secret ARN
     - Key: `DD_API_KEY`
   - Click "Add"

3. **Update Flask App Container**:
   - Select your existing Flask container
   - Add environment variables:
     - `DD_AGENT_HOST` = `localhost`
     - `DD_TRACE_AGENT_PORT` = `8126`
     - `DD_SERVICE` = `hello-world-flask-app`
     - `DD_ENV` = `production`
     - `DD_VERSION` = `1.0.0`

4. **Update Task Execution Role**:
   - Scroll to "Task execution role"
   - The role needs permission to read secrets
   - Add this policy to the role:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue"
      ],
      "Resource": "arn:aws:secretsmanager:us-east-1:123456789:secret:datadog-api-key-*"
    }
  ]
}
```

5. **Create the new revision**

### Step 3: Update ECS Service

1. Go to your ECS Service
2. Click "Update service"
3. Select the new task definition revision
4. Check "Force new deployment"
5. Click "Update"

### Step 4: Rebuild and Push Docker Image

```bash
cd /Users/araavind.senthil/helloworld

# Build for ARM64 (if using Graviton)
docker build --platform linux/arm64 -t hello-world-app .

# Or build for AMD64
docker build --platform linux/amd64 -t hello-world-app .

# Tag for ECR
docker tag hello-world-app:latest <ACCOUNT_ID>.dkr.ecr.<REGION>.amazonaws.com/hello-world-app:latest

# Push to ECR
docker push <ACCOUNT_ID>.dkr.ecr.<REGION>.amazonaws.com/hello-world-app:latest
```

---

## 📊 Viewing Traces in Datadog

### 1. **APM Traces View**
- Go to: https://app.datadoghq.com/apm/traces
- Filter by service: `hello-world-flask-app`
- You'll see all HTTP requests as traces

### 2. **Service Map**
- Go to: https://app.datadoghq.com/apm/map
- Visual representation of your services and dependencies

### 3. **Service Performance**
- Go to: https://app.datadoghq.com/apm/services
- Click on `hello-world-flask-app`
- See metrics like:
  - Requests per second
  - Average latency
  - Error rate
  - P50, P75, P95, P99 latencies

### 4. **Individual Traces**
Click on any trace to see:
- **Flame graph**: Visual timeline of the request
- **Spans**: Each operation (Flask request, external calls, etc.)
- **Tags**: Service, environment, version, HTTP method, status code
- **Logs**: If you enable log correlation (optional)

---

## 🎯 What You'll See in Datadog

### Example Trace Structure

```
Trace: GET /api/hello (45ms)
├─ flask.request (45ms)
│  ├─ Resource: GET /api/hello
│  ├─ Service: hello-world-flask-app
│  ├─ Status: 200
│  ├─ Tags:
│  │  ├─ env: production
│  │  ├─ version: 1.0.0
│  │  ├─ http.method: GET
│  │  ├─ http.status_code: 200
│  │  └─ http.url: /api/hello
│  └─ Duration: 45ms
```

### Automatic Metrics Available

- **Requests**: Total count of requests
- **Errors**: Count and rate of errors (5xx)
- **Latency**: P50, P75, P95, P99, Max
- **Throughput**: Requests per second
- **Apdex Score**: Application performance index

---

## 🔧 Configuration Options

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `DD_AGENT_HOST` | Datadog Agent hostname | `localhost` | Yes |
| `DD_TRACE_AGENT_PORT` | Datadog Agent port | `8126` | Yes |
| `DD_SERVICE` | Service name in Datadog | `hello-world-flask-app` | Yes |
| `DD_ENV` | Environment (dev/staging/prod) | - | Recommended |
| `DD_VERSION` | Application version | - | Recommended |
| `DD_TRACE_ENABLED` | Enable/disable tracing | `true` | No |
| `DD_TRACE_SAMPLE_RATE` | Sample rate (0.0-1.0) | `1.0` | No |

### Sampling

To reduce costs, you can sample traces:

```python
# In app.py
tracer.configure(
    hostname=os.getenv("DD_AGENT_HOST", "localhost"),
    port=int(os.getenv("DD_TRACE_AGENT_PORT", "8126")),
    sampler=DatadogSampler(default_sample_rate=0.5)  # 50% sampling
)
```

Or via environment variable:
```bash
DD_TRACE_SAMPLE_RATE=0.5  # Sample 50% of traces
```

---

## 🐛 Troubleshooting

### No Traces Appearing in Datadog

**Check 1: Is the Datadog Agent running?**
```bash
# In Fargate, check CloudWatch logs for datadog-agent container
# Look for: "Datadog Agent is running"
```

**Check 2: Can Flask app reach the agent?**
```bash
# Add this to your Flask app temporarily
import socket
try:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('localhost', 8126))
    if result == 0:
        print("✅ Can reach Datadog Agent on port 8126")
    else:
        print("❌ Cannot reach Datadog Agent on port 8126")
    sock.close()
except Exception as e:
    print(f"❌ Error: {e}")
```

**Check 3: Is ddtrace installed?**
```bash
pip list | grep ddtrace
```

**Check 4: Is ddtrace-run being used?**
```bash
# Check your Dockerfile CMD line
CMD ["ddtrace-run", "gunicorn", ...]
```

**Check 5: Check Datadog Agent logs**
- Go to CloudWatch Logs
- Find log group for datadog-agent container
- Look for errors like:
  - "Invalid API key"
  - "Connection refused"
  - "Rate limited"

### Traces Not Showing Correct Service Name

Make sure environment variables are set:
```bash
DD_SERVICE=hello-world-flask-app
DD_ENV=production
DD_VERSION=1.0.0
```

### High Latency in Traces

If you see high latency, check:
- Network latency to Datadog Agent
- Agent buffer size
- Application performance (not tracing overhead)

### Agent Container Failing in Fargate

Common issues:
1. **Invalid API key**: Check Secrets Manager
2. **Insufficient memory**: Increase agent container memory to 512MB
3. **Network issues**: Ensure task has internet access (public IP or NAT gateway)

---

## 💰 Cost Considerations

### Datadog APM Pricing

- **Ingested Spans**: $1.70 per million spans
- **Indexed Spans**: $1.70 per million spans
- **APM Host**: $31/host/month (Fargate tasks count as hosts)

### Cost Optimization

1. **Use Sampling**:
   ```bash
   DD_TRACE_SAMPLE_RATE=0.1  # Only trace 10% of requests
   ```

2. **Filter Out Health Checks**:
   ```python
   from ddtrace.filters import FilterRequestsOnUrl
   
   tracer.configure(
       settings={
           'FILTERS': [
               FilterRequestsOnUrl(r'http://.*/health$'),
           ]
       }
   )
   ```

3. **Use Fargate Spot** for non-production environments

---

## 🎓 Understanding APM Concepts

### What is a Trace?
A **trace** represents a single request through your system. It contains one or more **spans**.

### What is a Span?
A **span** represents a single operation (e.g., HTTP request, database query, external API call).

### Trace Example
```
Request: GET /api/hello
├─ Span 1: flask.request (50ms)
│  └─ Span 2: requests.get (external API) (30ms)
```

### Tags
**Tags** add metadata to traces for filtering and grouping:
- `env:production`
- `service:hello-world-flask-app`
- `version:1.0.0`
- `http.method:GET`
- `http.status_code:200`

---

## 📚 Additional Resources

- [Datadog APM Python Documentation](https://docs.datadoghq.com/tracing/setup_overview/setup/python/)
- [ddtrace Library](https://ddtrace.readthedocs.io/)
- [Datadog Agent on Fargate](https://docs.datadoghq.com/integrations/ecs_fargate/)
- [APM Best Practices](https://docs.datadoghq.com/tracing/guide/apm_best_practices/)

---

## ✅ Checklist

Before deploying to production:

- [ ] Datadog API key stored in AWS Secrets Manager
- [ ] Task execution role has permission to read secrets
- [ ] Task definition includes both Flask and Datadog Agent containers
- [ ] Environment variables configured correctly
- [ ] Docker image rebuilt and pushed to ECR
- [ ] ECS service updated with new task definition
- [ ] Traces appearing in Datadog UI
- [ ] Service map showing your service
- [ ] No errors in CloudWatch logs

---

**You're all set!** 🎉 Your Flask application is now sending APM traces to Datadog!


