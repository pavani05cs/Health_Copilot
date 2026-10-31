"""
Vertically Scale AWS EC2 Instance to t3.large
Safely stops the instance, modifies instance type, starts it, and retrieves the new public IP.
"""

import os
import sys
import time
import boto3
from botocore.exceptions import ClientError
from create_ssh_keypair import load_env_file

INSTANCE_ID = "i-06a53501cc65cb448"
TARGET_TYPE = "t3.large"
REGION = "ap-southeast-2"

def scale_instance():
    load_env_file()
    
    ec2 = boto3.client(
        "ec2",
        region_name=REGION,
        aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
    )
    
    print(f"[INFO] Inspecting instance {INSTANCE_ID} in {REGION}...")
    desc = ec2.describe_instances(InstanceIds=[INSTANCE_ID])
    inst = desc["Reservations"][0]["Instances"][0]
    current_type = inst.get("InstanceType")
    current_state = inst["State"]["Name"]
    old_ip = inst.get("PublicIpAddress", "N/A")
    
    print(f"[INFO] Current Instance Type: {current_type}")
    print(f"[INFO] Current State: {current_state}")
    print(f"[INFO] Current Public IP: {old_ip}")
    
    if current_type == TARGET_TYPE and current_state == "running":
        print(f"[SUCCESS] Instance is already running as {TARGET_TYPE}!")
        return old_ip

    # 1. Stop instance if running
    if current_state != "stopped":
        print(f"[INFO] Stopping instance {INSTANCE_ID}...")
        ec2.stop_instances(InstanceIds=[INSTANCE_ID])
        print("[INFO] Waiting for instance to stop...")
        waiter = ec2.get_waiter("instance_stopped")
        waiter.wait(InstanceIds=[INSTANCE_ID])
        print("[SUCCESS] Instance stopped.")
    
    # 2. Modify instance attribute
    print(f"[INFO] Modifying instance type to '{TARGET_TYPE}'...")
    ec2.modify_instance_attribute(
        InstanceId=INSTANCE_ID,
        InstanceType={"Value": TARGET_TYPE}
    )
    print(f"[SUCCESS] Instance type modified to {TARGET_TYPE}.")

    # 3. Start instance
    print(f"[INFO] Starting instance {INSTANCE_ID}...")
    ec2.start_instances(InstanceIds=[INSTANCE_ID])
    print("[INFO] Waiting for instance to enter 'running' state...")
    waiter = ec2.get_waiter("instance_running")
    waiter.wait(InstanceIds=[INSTANCE_ID])
    
    # 4. Get new IP
    desc_new = ec2.describe_instances(InstanceIds=[INSTANCE_ID])
    inst_new = desc_new["Reservations"][0]["Instances"][0]
    new_ip = inst_new.get("PublicIpAddress", "N/A")
    
    print("\n" + "=" * 65)
    print(" VERTICAL SCALING COMPLETED SUCCESSFULLY!")
    print("=" * 65)
    print(f"Instance ID : {INSTANCE_ID}")
    print(f"New Type    : {TARGET_TYPE} (2 vCPUs, 8 GiB RAM)")
    print(f"Old IP      : {old_ip}")
    print(f"New IP      : {new_ip}")
    print(f"SSH Command : ssh -i health-copilot-ssh.pem ubuntu@{new_ip}")
    print("=" * 65)
    
    return new_ip

if __name__ == "__main__":
    scale_instance()
