"""
Launch an EC2 Instance with the SSH Key Pair and Security Group using Boto3
"""

import os
import sys
import boto3
from botocore.exceptions import ClientError
from create_ssh_keypair import load_env_file, get_ec2_client


def get_latest_amazon_linux_ami(ec2_client):
    """Retrieves the latest Amazon Linux 2023 AMI ID."""
    response = ec2_client.describe_images(
        Owners=["amazon"],
        Filters=[
            {"Name": "name", "Values": ["al2023-ami-2023*-kernel-6.1-x86_64"]},
            {"Name": "state", "Values": ["available"]},
        ],
    )
    images = response.get("Images", [])
    if not images:
        raise RuntimeError("No suitable Amazon Linux AMI found.")
    # Sort by creation date descending
    images.sort(key=lambda x: x["CreationDate"], reverse=True)
    return images[0]["ImageId"], images[0]["Name"]


def launch_instance(key_name="health-copilot-ssh", sg_name="ssh-access-sg", instance_type="t2.micro"):
    load_env_file()
    ec2_client, region = get_ec2_client()

    # Get SG ID
    sgs = ec2_client.describe_security_groups(
        Filters=[{"Name": "group-name", "Values": [sg_name]}]
    )["SecurityGroups"]
    if not sgs:
        print(f"[ERROR] Security group '{sg_name}' not found. Run create_ssh_keypair.py first.")
        return
    sg_id = sgs[0]["GroupId"]

    ami_id, ami_name = get_latest_amazon_linux_ami(ec2_client)
    print(f"[INFO] Using AMI: {ami_id} ({ami_name})")
    print(f"[INFO] Launching instance type '{instance_type}' in region '{region}'...")

    try:
        response = ec2_client.run_instances(
            ImageId=ami_id,
            InstanceType=instance_type,
            KeyName=key_name,
            SecurityGroupIds=[sg_id],
            MinCount=1,
            MaxCount=1,
            TagSpecifications=[
                {
                    "ResourceType": "instance",
                    "Tags": [{"Key": "Name", "Value": "SSH-Test-Instance"}],
                }
            ],
        )
        instance_id = response["Instances"][0]["InstanceId"]
        print(f"[SUCCESS] Instance launched! Instance ID: {instance_id}")
        print(f"[INFO] Waiting for instance to enter 'running' state...")

        waiter = ec2_client.get_waiter("instance_running")
        waiter.wait(InstanceIds=[instance_id])

        # Retrieve public IP
        desc = ec2_client.describe_instances(InstanceIds=[instance_id])
        instance_info = desc["Reservations"][0]["Instances"][0]
        public_ip = instance_info.get("PublicIpAddress", "N/A")

        print("\n" + "=" * 60)
        print(" INSTANCE READY FOR SSH CONNECTION")
        print("=" * 60)
        print(f"Instance ID: {instance_id}")
        print(f"Public IP  : {public_ip}")
        print(f"\nConnect command:")
        print(f"ssh -i \"{key_name}.pem\" ec2-user@{public_ip}")
        print("=" * 60)
        return instance_id

    except ClientError as e:
        print(f"[AWS ERROR] Failed to launch instance: {e}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Launch an EC2 instance with SSH access")
    parser.add_argument("--key-name", default="health-copilot-ssh", help="Key Pair Name")
    parser.add_argument("--instance-type", default="t2.micro", help="Instance type (default: t2.micro or t3.micro)")
    args = parser.parse_args()

    launch_instance(key_name=args.key_name, instance_type=args.instance_type)
