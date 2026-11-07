# Installation & Setup Guide

Complete setup instructions for RFM-LDE Multiagent in development, staging, and production environments.

## Quick Start (5 minutes)

```bash
# Clone repository
git clone https://gitlab.com/olimpobet/data/machine-learning.git
cd machine-learning/tinka_ml/rfm_lde_multiagente

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env
# Edit .env with your AWS credentials

# Run tests
pytest -v

# Start local server
python src/lambdas/rfm_lde_multiagente/probar_local.py
```

Server will be available at `http://localhost:8000`

---

## Detailed Setup

### 1. Prerequisites

**System Requirements:**
- Python 3.8+
- pip or poetry
- AWS CLI v2
- Docker (optional, for containerized deployment)

**AWS Credentials:**
You need AWS credentials with permissions for:
- Athena (query execution)
- S3 (read dlk-olimpo bucket)
- Lambda (for deployment)

```bash
# Configure AWS credentials
aws configure --profile olimpobet-prd
```

### 2. Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate (Unix/Mac)
source venv/bin/activate

# Activate (Windows)
venv\Scripts\activate

# Verify
python --version  # Should be 3.8+
```

### 3. Install Dependencies

```bash
# Install package in development mode
pip install -e .

# Or install from requirements
pip install -r requirements.txt

# Verify installation
python -c "import langgraph; print(langgraph.__version__)"
```

### 4. Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit with your values
# IMPORTANT: Set these environment variables:
# - AWS_REGION=us-east-1
# - AWS_PROFILE=olimpobet-prd (or your profile name)
# - ANTHROPIC_API_KEY=sk-ant-...
# - ATHENA_DATABASE=dwh_raw_pe
```

**Environment Variables:**

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `AWS_REGION` | Yes | us-east-1 | AWS region |
| `AWS_PROFILE` | Yes | — | AWS CLI profile for credentials |
| `ANTHROPIC_API_KEY` | Yes | — | Claude API key from Anthropic |
| `ENVIRONMENT` | No | production | Set to 'development' for local testing |
| `DEBUG` | No | false | Enable debug logging |
| `ATHENA_DATABASE` | No | dwh_raw_pe | Athena database name |
| `LOG_LEVEL` | No | INFO | Logging level (DEBUG, INFO, WARNING, ERROR) |

### 5. Verify Setup

```bash
# Run unit tests
pytest tests/unit -v

# Run integration tests (requires AWS credentials)
pytest tests/integration -v

# Check code quality
make lint

# Generate coverage report
make test-cov
```

---

## Development Workflow

### Start Local Server

```bash
cd rfm_lde_multiagente
python src/lambdas/rfm_lde_multiagente/probar_local.py
```

### Make API Request

```bash
curl -X POST http://localhost:8000 \
  -H "Content-Type: application/json" \
  -d '{
    "historial": [{"role": "user", "content": "Tell me about cluster 0"}],
    "estado": {
      "grupo": {"cluster": 0, "quintil": null, "run_date": "2026-11-06"},
      "periodo": {"type": "relative", "value": "last_week"}
    }
  }'
```

### Format Code

```bash
# Auto-format all Python files
make format

# Run linters
make lint
```

### Run Tests

```bash
# Run all tests with coverage
make test-cov

# Run specific test file
pytest tests/unit/test_aadd_specialist.py -v

# Run with debug output
pytest tests/ -vv -s
```

---

## Docker Deployment

### Build Image

```bash
docker build -t rfm-lde-multiagent:latest .
```

### Run Container

```bash
docker run -p 8000:8000 \
  --env-file .env \
  --name rfm-lde \
  rfm-lde-multiagent:latest
```

### Push to ECR (AWS)

```bash
# Login to AWS ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 211125514336.dkr.ecr.us-east-1.amazonaws.com

# Tag image
docker tag rfm-lde-multiagent:latest 211125514336.dkr.ecr.us-east-1.amazonaws.com/rfm-lde-multiagent:latest

# Push
docker push 211125514336.dkr.ecr.us-east-1.amazonaws.com/rfm-lde-multiagent:latest
```

---

## Lambda Deployment

### Prerequisites

- AWS Lambda function created
- Function has IAM role with Athena/S3 permissions
- Python 3.11 runtime

### Deploy

```bash
# 1. Prepare deployment package
cd src/lambdas/rfm_lde_multiagente
pip install -r requirements.txt -t package/
cp -r ../../agents package/src/
cd package && zip -r ../lambda_function.zip .

# 2. Update Lambda function
aws lambda update-function-code \
  --function-name rfm-lde-multiagente-dev \
  --zip-file fileb://lambda_function.zip \
  --region us-east-1

# 3. Test
aws lambda invoke \
  --function-name rfm-lde-multiagente-dev \
  --payload '{"body": "{\"historial\": [{\"role\": \"user\", \"content\": \"Test\"}]}"}' \
  response.json
```

---

## Troubleshooting

### Issue: `ModuleNotFoundError: No module named 'langgraph'`

**Solution:**
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Issue: AWS credentials not found

**Solution:**
```bash
# Set up credentials
aws configure --profile olimpobet-prd

# Or set environment variables
export AWS_REGION=us-east-1
export AWS_PROFILE=olimpobet-prd
```

### Issue: Athena query timeout

**Solution:**
- Check network connectivity to AWS
- Verify ATHENA_OUTPUT_LOCATION S3 bucket exists
- Reduce query complexity or add partition filters

### Issue: Tests fail with "ANTHROPIC_API_KEY not set"

**Solution:**
```bash
export ANTHROPIC_API_KEY=sk-ant-...
pytest tests/
```

---

## Next Steps

1. **Read Documentation:**
   - API specification: `docs/API.md`
   - Architecture details: `docs/architecture/ARCHITECTURE.md`
   - Code examples: `data/samples/`

2. **Run Examples:**
   ```bash
   python scripts/example_query.py
   python scripts/example_export.py
   ```

3. **Deploy to Production:**
   - Follow Lambda deployment steps
   - Set up CloudWatch monitoring
   - Configure SNS alerts for failures

---

**Installation Version:** 2.0  
**Last Updated:** 2026-11-06  
**Support:** data-team@olimpobet.com
