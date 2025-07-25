# Jenkins Server Setup Guide for AWS Lambda Blue-Green Deployment

This guide will help you set up a Jenkins server to run the blue-green deployment pipeline for AWS Lambda.

## Option 1: Local Jenkins Setup (Development/Testing)

### 1. Install Jenkins Locally

**On macOS:**
```bash
brew install jenkins-lts
brew services start jenkins-lts
```

**On Ubuntu/Debian:**
```bash
wget -q -O - https://pkg.jenkins.io/debian/jenkins.io.key | sudo apt-key add -
sudo sh -c 'echo deb http://pkg.jenkins.io/debian-stable binary/ > /etc/apt/sources.list.d/jenkins.list'
sudo apt update
sudo apt install jenkins
sudo systemctl start jenkins
sudo systemctl enable jenkins
```

**On RHEL/CentOS:**
```bash
sudo wget -O /etc/yum.repos.d/jenkins.repo https://pkg.jenkins.io/redhat-stable/jenkins.repo
sudo rpm --import https://pkg.jenkins.io/redhat-stable/jenkins.io.key
sudo yum install jenkins
sudo systemctl start jenkins
sudo systemctl enable jenkins
```

### 2. Access Jenkins
- Open your browser and go to `http://localhost:8080`
- Get the initial admin password: `sudo cat /var/lib/jenkins/secrets/initialAdminPassword`
- Complete the setup wizard and install suggested plugins

## Option 2: AWS EC2 Jenkins Setup (Recommended for Production)

### 1. Launch EC2 Instance

Create an EC2 instance with the following specifications:
- **Instance Type**: t3.medium or larger
- **AMI**: Amazon Linux 2023 or Ubuntu 22.04
- **Security Group**: Allow inbound traffic on port 8080 (Jenkins UI) and 22 (SSH)
- **IAM Role**: Create an IAM role with necessary AWS permissions (see IAM section below)

### 2. Install Jenkins on EC2

**For Amazon Linux 2023:**
```bash
# Connect to your EC2 instance
ssh -i your-key.pem ec2-user@your-ec2-public-ip

# Update system
sudo dnf update -y

# Install Java 17
sudo dnf install java-17-amazon-corretto-headless -y

# Add Jenkins repository
sudo wget -O /etc/yum.repos.d/jenkins.repo https://pkg.jenkins.io/redhat-stable/jenkins.repo
sudo rpm --import https://pkg.jenkins.io/redhat-stable/jenkins.io.key

# Install Jenkins
sudo dnf install jenkins -y

# Start and enable Jenkins
sudo systemctl start jenkins
sudo systemctl enable jenkins

# Install Git (if not already installed)
sudo dnf install git -y
```

**For Ubuntu:**
```bash
# Connect to your EC2 instance
ssh -i your-key.pem ubuntu@your-ec2-public-ip

# Update system
sudo apt update -y

# Install Java 17
sudo apt install openjdk-17-jre-headless -y

# Add Jenkins repository
wget -q -O - https://pkg.jenkins.io/debian/jenkins.io.key | sudo apt-key add -
sudo sh -c 'echo deb https://pkg.jenkins.io/debian-stable binary/ > /etc/apt/sources.list.d/jenkins.list'

# Install Jenkins
sudo apt update
sudo apt install jenkins -y

# Start and enable Jenkins
sudo systemctl start jenkins
sudo systemctl enable jenkins

# Install Git
sudo apt install git -y
```

### 3. Access Jenkins on EC2
- Open your browser and go to `http://your-ec2-public-ip:8080`
- Get the initial admin password: `sudo cat /var/lib/jenkins/secrets/initialAdminPassword`

## Required Jenkins Plugins Installation

After Jenkins is running, install these required plugins:

1. Go to **Jenkins Dashboard** → **Manage Jenkins** → **Manage Plugins**
2. Go to **Available** tab and search for these plugins:
   - **AWS Steps Plugin**
   - **AWS Credentials Plugin**
   - **Git Plugin** (usually pre-installed)
   - **Pipeline: AWS Steps**
   - **Pipeline: Stage View Plugin**
   - **Blue Ocean** (optional, for better UI)

3. Select all plugins and click **Install without restart**

## Required Tools Installation on Jenkins Node

Install these security scanning tools on your Jenkins server/agents:

### 1. Install Python and pip
```bash
# Amazon Linux 2023
sudo dnf install python3 python3-pip -y

# Ubuntu
sudo apt install python3 python3-pip -y
```

### 2. Install Bandit (Python security scanner)
```bash
sudo pip3 install bandit
```

### 3. Install cfn-nag (CloudFormation security scanner)
```bash
# Install Ruby first
# Amazon Linux 2023
sudo dnf install ruby ruby-devel gcc make -y

# Ubuntu
sudo apt install ruby ruby-dev build-essential -y

# Install cfn-nag
sudo gem install cfn-nag
```

### 4. Install AWS CLI
```bash
# Download and install AWS CLI v2
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# Verify installation
aws --version
```

## AWS IAM Configuration

### 1. Create IAM Role for Jenkins EC2 Instance (Recommended)

Create an IAM role with these permissions and attach it to your Jenkins EC2 instance:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:PutObject",
                "s3:DeleteObject",
                "s3:ListBucket"
            ],
            "Resource": [
                "arn:aws:s3:::s3-jenkins-lambda",
                "arn:aws:s3:::s3-jenkins-lambda/*"
            ]
        },
        {
            "Effect": "Allow",
            "Action": [
                "lambda:CreateFunction",
                "lambda:UpdateFunctionCode",
                "lambda:UpdateFunctionConfiguration",
                "lambda:PublishVersion",
                "lambda:CreateAlias",
                "lambda:UpdateAlias",
                "lambda:GetFunction",
                "lambda:GetAlias",
                "lambda:InvokeFunction",
                "lambda:ListVersionsByFunction"
            ],
            "Resource": "arn:aws:lambda:*:*:function:blue-green-lambda*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "codedeploy:CreateApplication",
                "codedeploy:CreateDeployment",
                "codedeploy:CreateDeploymentGroup",
                "codedeploy:GetApplication",
                "codedeploy:GetDeployment",
                "codedeploy:GetDeploymentConfig",
                "codedeploy:GetDeploymentGroup",
                "codedeploy:ListApplications",
                "codedeploy:ListDeploymentGroups",
                "codedeploy:ListDeployments",
                "codedeploy:StopDeployment",
                "codedeploy:GetApplicationRevision",
                "codedeploy:RegisterApplicationRevision",
                "codedeploy:PutLifecycleEventHookExecutionStatus"
            ],
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "cloudformation:CreateStack",
                "cloudformation:UpdateStack",
                "cloudformation:DescribeStacks",
                "cloudformation:DescribeStackResources",
                "cloudformation:GetTemplate",
                "cloudformation:ListStacks",
                "cloudformation:ValidateTemplate"
            ],
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "sns:Publish"
            ],
            "Resource": "arn:aws:sns:*:*:*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "iam:PassRole"
            ],
            "Resource": [
                "arn:aws:iam::*:role/LambdaExecutionRole",
                "arn:aws:iam::*:role/CodeDeployServiceRole"
            ]
        },
        {
            "Effect": "Allow",
            "Action": [
                "cloudwatch:GetMetricStatistics",
                "cloudwatch:ListMetrics"
            ],
            "Resource": "*"
        }
    ]
}
```

### 2. Alternative: Create IAM User (Less Secure)

If you can't use IAM roles, create an IAM user with the above permissions and configure AWS credentials in Jenkins.

### 3. Create Required IAM Service Roles

**Lambda Execution Role:**
```bash
aws iam create-role \
    --role-name LambdaExecutionRole \
    --assume-role-policy-document '{
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {
                    "Service": "lambda.amazonaws.com"
                },
                "Action": "sts:AssumeRole"
            }
        ]
    }'

aws iam attach-role-policy \
    --role-name LambdaExecutionRole \
    --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole

aws iam attach-role-policy \
    --role-name LambdaExecutionRole \
    --policy-arn arn:aws:iam::aws:policy/AWSCodeDeployRoleForLambda
```

**CodeDeploy Service Role:**
```bash
aws iam create-role \
    --role-name CodeDeployServiceRole \
    --assume-role-policy-document '{
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {
                    "Service": "codedeploy.amazonaws.com"
                },
                "Action": "sts:AssumeRole"
            }
        ]
    }'

aws iam attach-role-policy \
    --role-name CodeDeployServiceRole \
    --policy-arn arn:aws:iam::aws:policy/service-role/AWSCodeDeployRoleForLambda
```

## Jenkins Credentials Configuration

1. Go to **Jenkins Dashboard** → **Manage Jenkins** → **Manage Credentials**
2. Click on **System** → **Global credentials (unrestricted)**
3. Add the following credentials:

### If Using IAM User (Alternative to IAM Role):
- **Kind**: AWS Credentials
- **ID**: `aws`
- **Access Key ID**: Your AWS access key
- **Secret Access Key**: Your AWS secret key

### Required Secret Text Credentials:
- **Kind**: Secret text
- **ID**: `lambda-execution-role-arn`
- **Secret**: `arn:aws:iam::YOUR_ACCOUNT_ID:role/LambdaExecutionRole`

- **Kind**: Secret text
- **ID**: `codedeploy-service-role-arn`
- **Secret**: `arn:aws:iam::YOUR_ACCOUNT_ID:role/CodeDeployServiceRole`

- **Kind**: Secret text
- **ID**: `sns-topic-arn`
- **Secret**: `arn:aws:sns:us-east-1:YOUR_ACCOUNT_ID:your-topic-name`

## Create S3 Bucket

Create the S3 bucket for storing Lambda deployment packages:

```bash
aws s3 mb s3://s3-jenkins-lambda --region us-east-1
```

## Create SNS Topic (Optional)

Create an SNS topic for deployment notifications:

```bash
aws sns create-topic --name lambda-deployment-notifications --region us-east-1
```

Subscribe to the topic to receive notifications:
```bash
aws sns subscribe \
    --topic-arn arn:aws:sns:us-east-1:YOUR_ACCOUNT_ID:lambda-deployment-notifications \
    --protocol email \
    --notification-endpoint your-email@example.com
```

## Create Jenkins Pipeline Job

1. Go to **Jenkins Dashboard** → **New Item**
2. Enter item name: `lambda-blue-green-deployment`
3. Select **Pipeline** and click **OK**
4. In the pipeline configuration:
   - **Definition**: Pipeline script from SCM
   - **SCM**: Git
   - **Repository URL**: `https://github.com/ToluGIT/CI-CD-Lambda.git`
   - **Branch Specifier**: `*/main`
   - **Script Path**: `jenkinsfile`
5. Click **Save**

## Test the Pipeline

1. Make sure all your AWS resources (IAM roles, S3 bucket, SNS topic) are created
2. Update the repository URL in the Jenkinsfile to point to your repository
3. Push your code changes to the main branch
4. Go to your Jenkins job and click **Build Now**
5. Monitor the build progress and check each stage

## Troubleshooting Tips

### Common Issues:

1. **AWS Credentials Error**: Ensure IAM role/user has correct permissions
2. **Tool Not Found Error**: Make sure all required tools (bandit, cfn-nag, aws cli) are installed
3. **Permission Denied**: Check that Jenkins user has necessary file system permissions
4. **CloudFormation Stack Exists**: Delete existing stack if you need to start fresh
5. **Lambda Function Timeout**: Increase timeout values if needed

### Useful Commands for Debugging:

```bash
# Check Jenkins logs
sudo tail -f /var/log/jenkins/jenkins.log

# Check if tools are installed
bandit --version
cfn_nag --version
aws --version

# Test AWS credentials
aws sts get-caller-identity

# Check Jenkins service status
sudo systemctl status jenkins
```

## Security Considerations

1. **Network Security**: Restrict Jenkins access to specific IP ranges
2. **HTTPS**: Configure SSL/TLS for Jenkins UI in production
3. **Regular Updates**: Keep Jenkins and plugins updated
4. **Backup**: Regular backup of Jenkins configuration and jobs
5. **Least Privilege**: Use minimal required AWS permissions
6. **Secret Management**: Use Jenkins credentials store for sensitive data

## Scaling Considerations

For production environments, consider:
- Using Jenkins agents/slaves for distributed builds
- Implementing Jenkins behind a load balancer
- Using persistent storage for Jenkins data
- Setting up Jenkins in a high-availability configuration
- Using container-based Jenkins deployment (Docker/Kubernetes)

## Monitoring and Alerting

Set up monitoring for:
- Jenkins build success/failure rates
- Deployment times and frequency
- AWS Lambda function metrics
- Security scan results trends
- Infrastructure costs

This completes the Jenkins setup guide for your AWS Lambda blue-green deployment pipeline!