"""
Configure AWS Security Group and SSH Access for a Specific IP Address
Author: Health Copilot Automation
"""

import os
import sys
import argparse
from pathlib import Path
import boto3
from botocore.exceptions import ClientError
from create_ssh_keypair import load_env_file, get_ec2_client


def configure_security_group_for_ip(ec2_client, ip_address: str, group_name="ssh-access-sg", lock_down=False):
    """
    Whitelists the given IP address in the EC2 Security Group for inbound SSH (Port 22).
    If lock_down is True, removes 0.0.0.0/0 (open to the world) to strictly enforce only this IP.
    """
    cidr_ip = f"{ip_address}/32" if "/" not in ip_address else ip_address
    print(f"[INFO] Configuring Security Group '{group_name}' for IP: {cidr_ip}...")

    # Fetch Security Group
    try:
        sgs = ec2_client.describe_security_groups(
            Filters=[{"Name": "group-name", "Values": [group_name]}]
        )["SecurityGroups"]
    except ClientError as e:
        print(f"[ERROR] Could not fetch security group: {e}")
        return None

    if not sgs:
        print(f"[ERROR] Security group '{group_name}' not found. Run create_ssh_keypair.py first.")
        return None

    sg = sgs[0]
    sg_id = sg["GroupId"]
    print(f"[INFO] Target Security Group ID: {sg_id}")

    # Check existing rules
    existing_cidrs = set()
    for perm in sg.get("IpPermissions", []):
        if perm.get("FromPort") == 22 and perm.get("ToPort") == 22:
            for ip_range in perm.get("IpRanges", []):
                existing_cidrs.add(ip_range.get("CidrIp"))

    # Authorize target IP if not already authorized
    if cidr_ip in existing_cidrs:
        print(f"[OK] Inbound SSH (Port 22) is already whitelisted for {cidr_ip}.")
    else:
        try:
            ec2_client.authorize_security_group_ingress(
                GroupId=sg_id,
                IpPermissions=[
                    {
                        "IpProtocol": "tcp",
                        "FromPort": 22,
                        "ToPort": 22,
                        "IpRanges": [
                            {
                                "CidrIp": cidr_ip,
                                "Description": f"Allow SSH from {ip_address}",
                            }
                        ],
                    }
                ],
            )
            print(f"[SUCCESS] Whitelisted {cidr_ip} on Port 22 in Security Group {sg_id}.")
        except ClientError as e:
            if "InvalidPermission.Duplicate" in str(e):
                print(f"[OK] Rule already exists.")
            else:
                raise

    # Optionally remove 0.0.0.0/0 for hardened security
    if lock_down and "0.0.0.0/0" in existing_cidrs:
        print("[INFO] Hardening security: Removing open-to-the-world (0.0.0.0/0) rule...")
        try:
            ec2_client.revoke_security_group_ingress(
                GroupId=sg_id,
                IpPermissions=[
                    {
                        "IpProtocol": "tcp",
                        "FromPort": 22,
                        "ToPort": 22,
                        "IpRanges": [{"CidrIp": "0.0.0.0/0"}],
                    }
                ],
            )
            print("[SUCCESS] Revoked 0.0.0.0/0 rule. Port 22 is now accessible ONLY from whitelisted IPs.")
        except ClientError as e:
            print(f"[WARN] Could not revoke 0.0.0.0/0: {e}")

    # Display active ingress rules
    updated_sg = ec2_client.describe_security_groups(GroupIds=[sg_id])["SecurityGroups"][0]
    print("\n--- Current Active Inbound SSH (Port 22) Rules ---")
    for perm in updated_sg.get("IpPermissions", []):
        if perm.get("FromPort") == 22:
            for r in perm.get("IpRanges", []):
                print(f"  -> Allowed: {r.get('CidrIp')} ({r.get('Description', 'No description')})")

    return sg_id


def generate_ssh_client_config(ip_address: str, key_path: str = "health-copilot-ssh.pem"):
    """
    Generates ready-to-use SSH commands and an optional ~/.ssh/config entry.
    """
    resolved_key = Path(key_path).resolve()
    
    config_entry = f"""
# Added for Health Copilot
Host ec2-host-{ip_address.replace('.', '-')}
    HostName {ip_address}
    User ec2-user
    IdentityFile "{resolved_key}"
    StrictHostKeyChecking accept-new
"""

    print("\n" + "=" * 65)
    print(f" SSH Commands to Connect (Target IP: {ip_address})")
    print("=" * 65)
    print("Direct Terminal Command:")
    print(f'  ssh -i "{key_path}" ec2-user@{ip_address}')
    print(f'  ssh -i "{key_path}" ubuntu@{ip_address}      # (For Ubuntu instances)')
    print(f'  ssh -i "{key_path}" admin@{ip_address}       # (For Debian instances)')
    print("\nOr using SSH Config (optional):")
    print(config_entry.strip())
    print("=" * 65)


def main():
    parser = argparse.ArgumentParser(description="Prepare SSH access based on an IP address")
    parser.add_argument("--ip", default="223.185.46.214", help="IP address to configure (default: 223.185.46.214)")
    parser.add_argument("--key", default="health-copilot-ssh.pem", help="Path to PEM key file")
    parser.add_argument("--lock-down", action="store_true", help="Remove 0.0.0.0/0 to restrict access exclusively to this IP")
    args = parser.parse_args()

    load_env_file()
    ec2_client, region = get_ec2_client()

    print("=" * 65)
    print(f" Preparing SSH Access for IP: {args.ip}")
    print(f" AWS Region: {region}")
    print("=" * 65)

    # 1. Update AWS Security Group Ingress
    configure_security_group_for_ip(ec2_client, args.ip, lock_down=args.lock_down)

    # 2. Output SSH Client Connection Commands
    generate_ssh_client_config(args.ip, args.key)


if __name__ == "__main__":
    main()
