# AWS Lambda Blue-Green Deployment using Jenkins and AWS CodeDeploy

This project demonstrates how to set up a CI/CD pipeline using Jenkins to deploy an AWS Lambda function with **true blue-green deployment** strategy managed by AWS CodeDeploy. The pipeline automates the process of packaging, uploading, and deploying the Lambda function with **zero downtime** and **gradual traffic shifting**. It integrates with multiple AWS services such as **S3, Lambda, CloudFormation, CodeDeploy, and SNS**, includes comprehensive security scanning with **Bandit** and **cfn-nag**, and implements **pre/post traffic validation hooks** for enhanced deployment safety.

---

## Prerequisites

1. **AWS EC2 Instance** with IAM role or **AWS Credentials** with access to:
   - S3  
   - Lambda  
   - CloudFormation  
   - CodeDeploy  
   - SNS  
   - CloudWatch (for monitoring)

2. **Jenkins Server** with the following tools and plugins installed:
   - **Required Tools**: Python 3.11+, Bandit, cfn-nag, AWS CLI v2
   - **Jenkins Plugins**: Git Plugin, Pipeline: AWS Steps plugin
   - **Optional**: Blue Ocean plugin for better UI

3. **S3 Bucket** to store the Lambda deployment packages.

4. **IAM Roles**: LambdaExecutionRole and CodeDeployServiceRole (creation scripts provided).
   
---

## Blue-Green Deployment Pipeline Workflow

### Security & Validation Phase
1.  **Checkout Code**
    *   Pulls latest code from the **main branch** of the GitHub repository
      
2.  **Security Scans**
    *   **Static Code Analysis with Bandit:** Scans Python code for security vulnerabilities
    *   **Infrastructure as Code Scanning with cfn-nag:** Analyzes CloudFormation templates for security issues
      
3.  **Evaluate Security Reports**
    *   Evaluates results from security scans
    *   **Blocks deployment** if critical vulnerabilities are found

### Build & Upload Phase  
4.  **Build Lambda Package**
    *   Packages main function, AppSpec file, and validation hooks into a **ZIP file**
    
5.  **Upload to S3**
    *   Uploads the deployment package to the specified **S3 bucket**

### Deployment Phase
6.  **Deploy to Lambda** (Intelligent Bootstrap/Update)
    *   **First Run**: Creates everything via CloudFormation (function, aliases, hooks, CodeDeploy resources)
    *   **Updates**: Updates main function code and validation hook functions
    
7.  **Update AppSpec File** (Updates Only)
    *   Updates AppSpec with **current and target Lambda function versions**
    *   Repackages and re-uploads with version information

### Blue-Green Deployment Phase
8.  **Blue-Green Traffic Shift** (Canary Deployment)
    *   **Phase 1**: Pre-traffic hook validates new version
    *   **Phase 2**: Shifts **10% traffic** to new version for **5 minutes**
    *   **Phase 3**: Monitors for errors during canary period
    *   **Phase 4**: Post-traffic hook validates with real traffic
    *   **Phase 5**: Shifts remaining **90% traffic** to new version
    *   **Auto-Rollback**: Automatically rolls back if any phase fails

### Validation & Notification Phase
9.  **Post-Deployment Smoke Tests**
    *   Invokes the live alias to verify functionality
    *   Validates the alias is pointing to correct version
    
10. **Notifications**
    *   Sends success notification via **SNS** upon successful deployment
---

## Blue-Green Deployment Features

### **What Makes This True Blue-Green?**

Unlike traditional "all-at-once" deployments that instantly switch all traffic, this implementation provides:

- **Gradual Traffic Shifting**: 10% → 100% over time instead of instant cutover
- **Pre-Traffic Validation**: Tests new version before any traffic is shifted
- **Real-Traffic Monitoring**: Validates performance with actual user traffic during canary phase
- **Automatic Rollback**: Instantly reverts if validation fails at any stage
- **Zero Downtime**: Users never experience service interruption
- **Risk Mitigation**: Catches issues before they impact all users

### **Validation Hooks Explained**

**Pre-Traffic Hook (`pre_traffic_hook.py`):**
- Runs **before** any traffic is shifted to the new version
- Tests function existence, invocation, and basic functionality
- **Blocks deployment** if new version has issues

**Post-Traffic Hook (`post_traffic_hook.py`):**
- Runs **after** 10% traffic shift, **before** full deployment
- Performs multiple invocations to test stability
- Monitors CloudWatch metrics for errors
- **Triggers rollback** if issues detected with real traffic

---

## Security Enhancements
    
This project incorporates **DevSecOps practices** by integrating security checks into the CI/CD pipeline to ensure that only secure and compliant code is deployed.
 
### **1\. Static Code Analysis with Bandit**

  *   **Tool Used:** [Bandit](https://bandit.readthedocs.io/en/latest/)
  *   **Purpose:** Scans the Python code (`lambda_function.py`) for security issues like hardcoded credentials, weak cryptography, and injection vulnerabilities.
  *   **Integration:** Added as a pipeline stage called **"Security: Static Code Analysis"**.
    
    

    
### **2\. Infrastructure as Code Scanning with cfn-nag**
    
   *   **Tool Used:** [cfn-nag](https://github.com/stelligent/cfn_nag)
   *   **Purpose:** Analyzes the CloudFormation template (`deployment_production.yaml`) for security vulnerabilities, such as insecure configurations and permissive policies.
   *   **Integration:** Added as a pipeline stage called **"Security: Infrastructure Scan"**.

### **3\. Security Report Evaluation**
    
 *   **Purpose:** Parses the reports generated by the security tools.
 *   **Integration:** Added as a pipeline stage called **"Security: Evaluate Reports"**.
 *   **Behavior:** If critical vulnerabilities are found, the pipeline fails to prevent insecure code from being deployed.

### **4\. Credentials and Secrets Management**
  
  *   **IAM Roles:** Uses EC2 instance IAM roles for secure AWS access (recommended)
  *   **Alternative:** AWS credentials stored securely in Jenkins using the **Credentials Plugin**
  *   **Secrets:** ARN values managed through Jenkins credentials and injected as environment variables

### **5\. IAM Roles and Permissions**
    
 *   **Principle of Least Privilege:** IAM roles (`LambdaExecutionRole` and `CodeDeployServiceRole`) are configured with minimal required permissions.
 *   **Policy Validation:** IAM policies are reviewed to ensure they do not grant excessive permissions.
    
### **6\. Secure Storage and Transmission**
    
  *   **S3 Bucket Security:** The S3 bucket used for storing the Lambda package is secured with proper access controls and encryption at rest.
  *   **Encryption:** Data in transit is secured using HTTPS when uploading to S3.

### **7\. Logging and Monitoring**
    
   *   **Pipeline Logs:** Jenkins pipeline logs are maintained for audit purposes.
   *   **AWS CloudWatch:** Used for monitoring Lambda function execution and logging.


## Quick Start Guide

### 1\. Clone the Repository
   
```bash
git clone https://github.com/ToluGIT/CI-CD-Lambda.git
cd CI-CD-Lambda
```

### 2\. Set Up Jenkins Server

**For detailed setup instructions, see [JENKINS_SETUP.md](JENKINS_SETUP.md)**

**Quick Setup:**
- Launch EC2 instance with appropriate IAM role
- Install Jenkins, Python 3.11+, AWS CLI v2
- Install security tools: `pip install bandit` and `gem install cfn-nag`
- Configure Jenkins with required plugins

### 3\. Configure AWS Resources

#### Create IAM Roles

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

#### Create S3 Bucket
```bash
aws s3 mb s3://s3-jenkins-lambda --region us-east-1
```

#### Create SNS Topic (Optional)
```bash
aws sns create-topic --name lambda-deployment-notifications --region us-east-1
```

### 4\. Configure Jenkins Credentials

1. **Go to** Jenkins Dashboard → Manage Jenkins → Manage Credentials
2. **Add the following Secret Text credentials:**

   ```
   ID: lambda-execution-role-arn
   Secret: arn:aws:iam::YOUR_ACCOUNT_ID:role/LambdaExecutionRole
   
   ID: codedeploy-service-role-arn
   Secret: arn:aws:iam::YOUR_ACCOUNT_ID:role/CodeDeployServiceRole
   
   ID: sns-topic-arn
   Secret: arn:aws:sns:us-east-1:YOUR_ACCOUNT_ID:lambda-deployment-notifications
   ```

### 5\. Create Jenkins Pipeline Job

1. **Go to** Jenkins Dashboard → New Item
2. **Enter name:** `lambda-blue-green-deployment`
3. **Select:** Pipeline → OK
4. **Configure:**
   - **Definition**: Pipeline script from SCM
   - **SCM**: Git
   - **Repository URL**: `https://github.com/ToluGIT/CI-CD-Lambda.git`
   - **Branch**: `*/main`
   - **Script Path**: `jenkinsfile`
5. **Save**

### 6\. Run Your First Deployment

1. **Click** "Build Now" to start the pipeline
2. **First Run**: Creates all AWS resources automatically (bootstrap)
3. **Subsequent Runs**: Performs true blue-green deployments
4. **Monitor**: Watch the blue-green traffic shifting in AWS CodeDeploy console

**Note**: Replace `YOUR_ACCOUNT_ID` with your actual AWS account ID.

---

## Testing the Deployment

### 1. **Test the Lambda Function**  
```bash
# Invoke the live alias
aws lambda invoke --function-name blue-green-lambda:live output.json
cat output.json

# Expected output:
# {
#   "statusCode": 200,
#   "body": "\"Blue-green deployment update successful - v2\""
# }
```

### 2. **Verify Blue-Green Deployment**  
```bash
# Check which version the live alias points to
aws lambda get-alias --function-name blue-green-lambda --name live

# List all function versions
aws lambda list-versions-by-function --function-name blue-green-lambda
```

### 3. **Monitor CodeDeploy Deployments**  
- **AWS Console**: Navigate to **CodeDeploy** → **Applications** → **blue-green-lambda**
- **CLI**: `aws deploy list-deployments --application-name blue-green-lambda`
- **Watch**: Traffic shifting from old version to new version during deployment

### 4. **Test Blue-Green Behavior**
1. **Make a code change** in `lambda_function.py` (e.g., change the return message)
2. **Commit and push** to trigger the pipeline
3. **Watch the deployment** in CodeDeploy console:
   - Pre-traffic validation runs
   - 10% traffic shifts to new version
   - 5-minute canary period
   - Post-traffic validation runs
   - Remaining 90% traffic shifts
---

### Cleanup

1.  **Delete the CloudFormation Stack**

        aws cloudformation delete-stack --stack-name lambda-blue-green-stack

2.  **Delete the S3 Bucket and Objects**

         aws s3 rm s3://s3-jenkins-lambda --recursive
         aws s3 rb s3://s3-jenkins-lambda
    
3.   **Delete IAM Roles**  
    Remove **LambdaExecutionRole** and **CodeDeployServiceRole** from the IAM console.
    
4.   **Delete Jenkins Job**  
    Remove the pipeline job from Jenkins.

---


## Key Benefits Achieved

This implementation delivers several critical advantages over traditional deployment approaches:

### **True Blue-Green Deployment**
- **Gradual Traffic Shifting**: 10% canary → 100% deployment instead of risky all-at-once
- **Zero Downtime**: Users never experience service interruptions
- **Automatic Rollback**: Instant reversion if issues are detected

### **Enhanced Safety**
- **Pre-Traffic Validation**: Tests new versions before any traffic exposure
- **Real-Traffic Monitoring**: Validates with actual user traffic during canary phase
- **Post-Deployment Verification**: Confirms deployment success with comprehensive smoke tests

### **DevSecOps Integration**
- **Security-First**: Blocks deployments with critical vulnerabilities
- **Compliance**: Maintains audit trails and security scan reports
- **Best Practices**: Uses IAM roles, least privilege principles, and secure credential management

### **Operational Excellence**
- **Smart Bootstrap**: Automatically creates or updates infrastructure as needed
- **Comprehensive Monitoring**: Integration with CloudWatch for metrics and logging
- **Notification Systems**: SNS alerts for deployment status updates

---

## Additional Resources

- **[JENKINS_SETUP.md](JENKINS_SETUP.md)**: Complete Jenkins server setup guide
- **AWS CodeDeploy Documentation**: [Blue/Green Deployments for Lambda](https://docs.aws.amazon.com/codedeploy/latest/userguide/applications-create-lambda.html)
- **Security Tools**: [Bandit](https://bandit.readthedocs.io/en/latest/) | [cfn-nag](https://github.com/stelligent/cfn_nag)



