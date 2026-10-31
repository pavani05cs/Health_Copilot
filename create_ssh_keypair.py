"""
AWS EC2 SSH Key Pair & Security Group Creator using Boto3
Author: Health Copilot Automation
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path
import boto3
from botocore.exceptions import ClientError


def load_env_file(filepath=".env"):
    """Simple parser to load key=value pairs from a .env file into os.environ."""
    env_path = Path(filepath)
    if not env_path.exists():
        return
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                k, v = line.split("=", 1)
                k = k.strip()
                v = v.strip().strip("'\"")
                if k not in os.environ:
                    os.environ[k] = v


def set_secure_permissions(file_path: Path):
    """
    Set restricted permissions on the private key file.
    SSH clients require that private keys are only readable by the file owner.
    """
    str_path = str(file_path.resolve())
    if sys.platform == "win32":
        try:
            # In Windows, use icacls to reset inheritance and grant Read permission only to current user
            username = os.environ.get("USERNAME") or os.getlogin()
            cmd = f'icacls "{str_path}" /inheritance:r /grant:r "{username}:(R)"'
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                print(f"[OK] Applied restricted Windows permissions to: {file_path.name}")
            else:
                print(f"[WARN] Failed to set permissions via icacls: {result.stderr.strip()}")
        except Exception as e:
            print(f"[WARN] Could not adjust Windows ACLs: {e}")
    else:
        # Linux / macOS (read-only by owner)
        try:
            os.chmod(file_path, 0o400)
            print(f"[OK] Applied chmod 400 to: {file_path.name}")
        except Exception as e:
            print(f"[WARN] Could not set chmod 400: {e}")


def get_ec2_client(region: str = None):
    """Initializes and returns a Boto3 EC2 client using env credentials or AWS profile."""
    load_env_file()
    
    region_name = (
        region
        or os.environ.get("AWS_DEFAULT_REGION")
        or os.environ.get("AWS_REGION")
        or "ap-southeast-2"
    )
    
    # boto3 will automatically pick up AWS_ACCESS_KEY_ID & AWS_SECRET_ACCESS_KEY from os.environ
    client = boto3.client("ec2", region_name=region_name)
    return client, region_name


def create_ssh_key_pair(ec2_client, key_name: str, output_dir: Path = Path(".")):
    """
    Creates an EC2 Key Pair and writes the private key to a .pem file.
    """
    pem_file = output_dir / f"{key_name}.pem"

    # Check if key pair already exists on AWS
    try:
        existing = ec2_client.describe_key_pairs(KeyNames=[key_name])
        print(f"[INFO] Key pair '{key_name}' already exists in AWS.")
        if pem_file.exists():
            print(f"[INFO] Local private key file '{pem_file}' already exists.")
            return pem_file
        else:
            print(
                f"[WARN] Key pair exists in AWS, but local file '{pem_file}' is missing.\n"
                f"       AWS does NOT store private keys after creation.\n"
                f"       If you lost the .pem file, delete the key pair in AWS and recreate it."
            )
            return None
    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code != "InvalidKeyPair.NotFound":
            raise

    # Create new key pair
    print(f"[INFO] Creating new SSH Key Pair '{key_name}'...")
    response = ec2_client.create_key_pair(
        KeyName=key_name,
        KeyType="rsa",       # 'rsa' or 'ed25519'
        KeyFormat="pem"      # 'pem' for OpenSSH or 'ppk' for PuTTY
    )

    private_key_material = response["KeyMaterial"]
    
    # Write to local .pem file
    with open(pem_file, "w", encoding="utf-8") as f:
        f.write(private_key_material)
    
    print(f"[SUCCESS] Saved private key to: {pem_file.resolve()}")

    # Apply secure permissions (mandatory for OpenSSH)
    set_secure_permissions(pem_file)

    return pem_file


def create_ssh_security_group(ec2_client, group_name="ssh-access-sg"):
    """
    Creates or retrieves an EC2 Security Group allowing inbound SSH (port 22).
    """
    try:
        # Check if group already exists
        sgs = ec2_client.describe_security_groups(
            Filters=[{"Name": "group-name", "Values": [group_name]}]
        )
        if sgs["SecurityGroups"]:
            sg_id = sgs["SecurityGroups"][0]["GroupId"]
            print(f"[INFO] Found existing Security Group: {group_name} ({sg_id})")
            return sg_id
    except ClientError:
        pass

    # Find default VPC
    vpcs = ec2_client.describe_vpcs(
        Filters=[{"Name": "is-default", "Values": ["true"]}]
    )["Vpcs"]
    
    if not vpcs:
        vpcs = ec2_client.describe_vpcs()["Vpcs"]
    
    if not vpcs:
        print("[WARN] No VPC found to associate security group with.")
        return None

    vpc_id = vpcs[0]["VpcId"]
    print(f"[INFO] Creating Security Group '{group_name}' in VPC {vpc_id}...")

    sg_res = ec2_client.create_security_group(
        GroupName=group_name,
        Description="Allow SSH inbound traffic on Port 22",
        VpcId=vpc_id,
    )
    sg_id = sg_res["GroupId"]

    # Authorize Port 22 inbound
    ec2_client.authorize_security_group_ingress(
        GroupId=sg_id,
        IpPermissions=[
            {
                "IpProtocol": "tcp",
                "FromPort": 22,
                "ToPort": 22,
                "IpRanges": [{"CidrIp": "0.0.0.0/0", "Description": "Allow SSH from anywhere"}],
            }
        ],
    )
    print(f"[SUCCESS] Created Security Group {sg_id} with inbound SSH (port 22) rule enabled.")
    return sg_id


def main():
    parser = argparse.ArgumentParser(description="Create AWS EC2 SSH Key Pair using Boto3")
    parser.add_argument("--key-name", default="my-ec2-key", help="Name of the key pair to create (default: my-ec2-key)")
    parser.add_argument("--region", default=None, help="AWS Region (default: from .env or ap-southeast-2)")
    parser.add_argument("--with-sg", action="store_true", default=True, help="Also create/verify an SSH Security Group (Port 22)")
    args = parser.parse_args()

    print("=" * 60)
    print(" AWS EC2 SSH Configuration with Boto3")
    print("=" * 60)

    try:
        client, region = get_ec2_client(args.region)
        print(f"[INFO] Connected to AWS EC2 in region: {region}")

        # 1. Create Key Pair
        pem_path = create_ssh_key_pair(client, args.key_name)

        # 2. Security Group for SSH
        sg_id = None
        if args.with_sg:
            sg_id = create_ssh_security_group(client)

        print("\n" + "=" * 60)
        print(" SSH Connection Instructions")
        print("=" * 60)
        if pem_path:
            print(f"1. Your private SSH key is stored at:")
            print(f"   {pem_path.resolve()}\n")
            print("2. When launching an EC2 instance, specify:")
            print(f"   - Key Pair: {args.key_name}")
            if sg_id:
                print(f"   - Security Group: {sg_id} (allows Port 22)")
            print("\n3. To connect to an EC2 instance via SSH in terminal:")
            print(f"   ssh -i \"{pem_path.name}\" ec2-user@<INSTANCE_PUBLIC_IP>")
            print(f"   (or 'ubuntu@<IP>' for Ubuntu, 'admin@<IP>' for Debian)\n")
        print("=" * 60)

    except ClientError as e:
        print(f"\n[AWS ERROR] {e.response['Error']['Message']} ({e.response['Error']['Code']})")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
