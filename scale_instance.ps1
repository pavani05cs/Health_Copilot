$aws = "aws"
if (Test-Path "C:\Program Files\Amazon\AWSCLI\bin\aws.exe") {
    $aws = "C:\Program Files\Amazon\AWSCLI\bin\aws.exe"
}

# Ensure AWS credentials are set from environment or AWS CLI profile
if (-not $env:AWS_DEFAULT_REGION) {
    $env:AWS_DEFAULT_REGION = "ap-southeast-2"
}

$instanceId = "i-06a53501cc65cb448"
$targetType = "t3.large"
$region = $env:AWS_DEFAULT_REGION

Write-Host "=========================================================="
Write-Host "     VERTICALLY SCALING EC2 INSTANCE TO $targetType"
Write-Host "=========================================================="

Write-Host "`n[1/4] Stopping EC2 instance $instanceId..."
& $aws ec2 stop-instances --instance-ids $instanceId --region $region | Out-Null

Write-Host "      Waiting for instance to enter 'stopped' state..."
& $aws ec2 wait instance-stopped --instance-ids $instanceId --region $region
Write-Host "      Instance successfully stopped!"

Write-Host "`n[2/4] Modifying instance type to $targetType..."
& $aws ec2 modify-instance-attribute --instance-id $instanceId --instance-type "{\`"Value\`": \`"$targetType\`"}" --region $region
Write-Host "      Instance type successfully set to $targetType!"

Write-Host "`n[3/4] Starting instance $instanceId..."
& $aws ec2 start-instances --instance-ids $instanceId --region $region | Out-Null

Write-Host "      Waiting for instance to enter 'running' state..."
& $aws ec2 wait instance-running --instance-ids $instanceId --region $region
Write-Host "      Instance is now running!"

Write-Host "`n[4/4] Retrieving updated instance metadata..."
$newIp = (& $aws ec2 describe-instances --instance-ids $instanceId --region $region --query "Reservations[0].Instances[0].PublicIpAddress" --output text).Trim()
$actualType = (& $aws ec2 describe-instances --instance-ids $instanceId --region $region --query "Reservations[0].Instances[0].InstanceType" --output text).Trim()

Write-Host "`n=========================================================="
Write-Host "      VERTICAL SCALING COMPLETE!"
Write-Host "=========================================================="
Write-Host "Instance ID  : $instanceId"
Write-Host "Current Type : $actualType (2 vCPUs, 8 GiB RAM)"
Write-Host "New Public IP: $newIp"
Write-Host "SSH Command  : ssh -i health-copilot-ssh.pem ubuntu@$newIp"
Write-Host "=========================================================="

# Save new IP to a local file for subsequent steps
$newIp | Out-File -FilePath "latest_ec2_ip.txt" -Encoding utf8
