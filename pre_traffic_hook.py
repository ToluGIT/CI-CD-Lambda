import json
import boto3
import time

def lambda_handler(event, context):
    """
    Pre-traffic hook for CodeDeploy blue-green deployment
    This function validates the new Lambda version before allowing traffic
    """
    
    print(f"Pre-traffic hook event: {json.dumps(event)}")
    
    # Extract deployment information
    deployment_id = event.get('DeploymentId')
    lifecycle_event_hook_execution_id = event.get('LifecycleEventHookExecutionId')
    
    # Initialize CodeDeploy client
    codedeploy = boto3.client('codedeploy')
    lambda_client = boto3.client('lambda')
    
    try:
        # Get the new Lambda function version from the deployment
        function_name = "blue-green-lambda"
        
        # Perform validation tests on the new version
        print("Starting pre-traffic validation tests...")
        
        # Test 1: Check if the new function version exists and is active
        try:
            response = lambda_client.get_function(FunctionName=function_name)
            print(f"Function state: {response['Configuration']['State']}")
            
            if response['Configuration']['State'] != 'Active':
                raise Exception("Lambda function is not in Active state")
                
        except Exception as e:
            print(f"Function validation failed: {str(e)}")
            # Signal failure to CodeDeploy
            codedeploy.put_lifecycle_event_hook_execution_status(
                deploymentId=deployment_id,
                lifecycleEventHookExecutionId=lifecycle_event_hook_execution_id,
                status='Failed'
            )
            return {
                'statusCode': 500,
                'body': json.dumps(f'Pre-traffic validation failed: {str(e)}')
            }
        
        # Test 2: Invoke the new function to ensure it's working
        try:
            test_payload = {"test": "pre-traffic-validation"}
            invoke_response = lambda_client.invoke(
                FunctionName=function_name,
                InvocationType='RequestResponse',
                Payload=json.dumps(test_payload)
            )
            
            if invoke_response['StatusCode'] != 200:
                raise Exception(f"Function invocation failed with status: {invoke_response['StatusCode']}")
                
            # Parse the response
            response_payload = json.loads(invoke_response['Payload'].read())
            print(f"Test invocation successful: {response_payload}")
            
        except Exception as e:
            print(f"Function invocation test failed: {str(e)}")
            # Signal failure to CodeDeploy
            codedeploy.put_lifecycle_event_hook_execution_status(
                deploymentId=deployment_id,
                lifecycleEventHookExecutionId=lifecycle_event_hook_execution_id,
                status='Failed'
            )
            return {
                'statusCode': 500,
                'body': json.dumps(f'Pre-traffic validation failed: {str(e)}')
            }
        
        # Test 3: Additional custom validation logic can be added here
        # For example: database connectivity, external API checks, etc.
        
        print("All pre-traffic validation tests passed!")
        
        # Signal success to CodeDeploy
        codedeploy.put_lifecycle_event_hook_execution_status(
            deploymentId=deployment_id,
            lifecycleEventHookExecutionId=lifecycle_event_hook_execution_id,
            status='Succeeded'
        )
        
        return {
            'statusCode': 200,
            'body': json.dumps('Pre-traffic validation completed successfully')
        }
        
    except Exception as e:
        print(f"Unexpected error in pre-traffic hook: {str(e)}")
        
        # Signal failure to CodeDeploy
        try:
            codedeploy.put_lifecycle_event_hook_execution_status(
                deploymentId=deployment_id,
                lifecycleEventHookExecutionId=lifecycle_event_hook_execution_id,
                status='Failed'
            )
        except Exception as codedeploy_error:
            print(f"Failed to signal CodeDeploy: {str(codedeploy_error)}")
        
        return {
            'statusCode': 500,
            'body': json.dumps(f'Pre-traffic validation failed: {str(e)}')
        }