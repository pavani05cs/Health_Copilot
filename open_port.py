import boto3
from create_ssh_keypair import load_env_file, get_ec2_client
from botocore.exceptions import ClientError

load_env_file()
client, region = get_ec2_client()

sg_id = "sg-02456dae4660ef896"

ports_to_open = [5173, 80, 3000]

for port in ports_to_open:
    try:
        client.authorize_security_group_ingress(
            GroupId=sg_id,
            IpPermissions=[
                {
                    "IpProtocol": "tcp",
                    "FromPort": port,
                    "ToPort": port,
                    "IpRanges": [{"CidrIp": "0.0.0.0/0", "Description": f"Allow inbound port {port}"}],
                }
            ],
        )
        print(f"[SUCCESS] Authorized inbound port {port} (0.0.0.0/0) on {sg_id}")
    except ClientError as e:
        if "InvalidPermission.Duplicate" in str(e):
            print(f"[INFO] Port {port} already authorized on {sg_id}")
        else:
            print(f"[ERROR] Failed to authorize port {port}: {e}")

# Verify current rules
sg = client.describe_security_groups(GroupIds=[sg_id])["SecurityGroups"][0]
print("\nCurrent Inbound Rules:")
for rule in sg.get("IpPermissions", []):
    proto = rule.get("IpProtocol")
    from_p = rule.get("FromPort")
    to_p = rule.get("ToPort")
    ranges = [r.get("CidrIp") for r in rule.get("IpRanges", [])]
    print(f"  {proto} {from_p}->{to_p}: {ranges}")
