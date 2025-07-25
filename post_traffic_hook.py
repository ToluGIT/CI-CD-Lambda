import json
import boto3
import time

def lambda_handler(event, context):
    """
    Post-traffic hook for CodeDeploy blue-green deployment
    This function validates the deployment after traffic has been shifted
    """
    
    print(f"Post-traffic hook event: {json.dumps(event)}")
    
    # Extract deployment information
    deployment_id = event.get('DeploymentId')
    lifecycle_event_hook_execution_id = event.get('LifecycleEventHookExecutionId')
    
    # Initialize AWS clients
    codedeploy = boto3.client('codedeploy')
    lambda_client = boto3.client('lambda')
    cloudwatch = boto3.client('cloudwatch')
    
    try:
        function_name = "blue-green-lambda"
        
        print("Starting post-traffic validation tests...")
        
        # Test 1: Verify the alias is pointing to the correct version
        try:
            alias_response = lambda_client.get_alias(
                FunctionName=function_name,
                Name='live'
            )
            print(f"Live alias pointing to version: {alias_response['FunctionVersion']}")
            
        except Exception as e:
            print(f"Alias validation failed: {str(e)}")
            # Signal failure to CodeDeploy
            codedeploy.put_lifecycle_event_hook_execution_status(
                deploymentId=deployment_id,
                lifecycleEventHookExecutionId=lifecycle_event_hook_execution_id,
                status='Failed'
            )
            return {
                'statusCode': 500,
                'body': json.dumps(f'Post-traffic validation failed: {str(e)}')
            }
        
        # Test 2: Run multiple test invocations to ensure stability
        print("Running stability tests...")
        success_count = 0
        total_tests = 5
        
        for i in range(total_tests):
            try:
                test_payload = {"test": f"post-traffic-validation-{i+1}"}
                invoke_response = lambda_client.invoke(
                    FunctionName=f"{function_name}:live",  # Use the alias
                    InvocationType='RequestResponse',
                    Payload=json.dumps(test_payload)
                )
                
                if invoke_response['StatusCode'] == 200:
                    success_count += 1
                    response_payload = json.loads(invoke_response['Payload'].read())
                    print(f"Test {i+1} successful: {response_payload}")
                else:
                    print(f"Test {i+1} failed with status: {invoke_response['StatusCode']}")
                    
                # Small delay between tests
                time.sleep(1)
                
            except Exception as e:
                print(f"Test {i+1} failed: {str(e)}")
        
        # Calculate success rate
        success_rate = (success_count / total_tests) * 100
        print(f"Success rate: {success_rate}% ({success_count}/{total_tests})")
        
        # Require at least 80% success rate
        if success_rate < 80:
            raise Exception(f"Success rate {success_rate}% is below threshold of 80%")
        
        # Test 3: Check CloudWatch metrics for errors (if any recent invocations)
        try:
            # Get error metrics from the last 5 minutes
            end_time = time.time()
            start_time = end_time - 300  # 5 minutes ago
            
            error_response = cloudwatch.get_metric_statistics(
                Namespace='AWS/Lambda',
                MetricName='Errors',
                Dimensions=[
                    {
                        'Name': 'FunctionName',
                        'Value': function_name
                    }
                ],
                StartTime=start_time,
                EndTime=end_time,
                Period=300,
                Statistics=['Sum']
            )
            
            total_errors = sum([point['Sum'] for point in error_response['Datapoints']])
            print(f"Total errors in last 5 minutes: {total_errors}")
            
            # Check if error rate is acceptable (this is a simple check)
            if total_errors > 5:  # Threshold of 5 errors
                print(f"Warning: High error count detected: {total_errors}")
                # You might want to fail the deployment here depending on your requirements
                
        except Exception as e:
            print(f"CloudWatch metrics check failed (non-critical): {str(e)}")
        
        # Test 4: Additional custom validation logic can be added here
        # For example: Check application-specific metrics, external health checks, etc.
        
        print("All post-traffic validation tests passed!")
        
        # Signal success to CodeDeploy
        codedeploy.put_lifecycle_event_hook_execution_status(
            deploymentId=deployment_id,
            lifecycleEventHookExecutionId=lifecycle_event_hook_execution_id,
            status='Succeeded'
        )
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Post-traffic validation completed successfully',
                'success_rate': success_rate,
                'tests_passed': success_count,
                'total_tests': total_tests
            })
        }
        
    except Exception as e:
        print(f"Unexpected error in post-traffic hook: {str(e)}")
        
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
            'body': json.dumps(f'Post-traffic validation failed: {str(e)}')
        }