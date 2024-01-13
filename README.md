# custom-aws-prometheus-exporter
Utilize the boto3 library to retrieve and make accessible any Prometheus metric.

## Purpose
Sometimes [cloudwatch_exporter](https://github.com/prometheus/cloudwatch_exporter) or [yet-another-cloudwatch-exporter](https://github.com/nerdswords/yet-another-cloudwatch-exporter) do not expose a metric you might need. 

In this example, our custom exporter exposes `aws_vpc_subnet_free_ips` metric:

#### `GET /metrics`:
```
# HELP aws_vpc_subnet_free_ips Free IPs in each VPC Subnet
# TYPE aws_vpc_subnet_free_ips gauge
aws_vpc_subnet_free_ips{availability_zone="eu-west-1a",cidr_block="10.1.0.0/24",subnet_id="subnet-1",subnet_name="subnet-1",vpc_id="vpc-private",total_ips=250} 250.0
aws_vpc_subnet_free_ips{availability_zone="eu-west-1b",cidr_block="10.1.1.0/24",subnet_id="subnet-2",subnet_name="subnet-2",vpc_id="vpc-private",total_ips=250} 250.0
```

Here is an example of a Prometheus rule that can be used to alert on a VPC Subnet that has been running out of free IPs for more than 5m.
```yaml
groups:
- name: Subnet Free IPs
  rules:
  - alert: SubnetRunningOutOfFreeIps
    expr: aws_vpc_subnet_free_ips < 32
    for: 15m
    labels:
      severity: warning
    annotations:
      summary: Subnet {{$labels.vpc_id}}/{{$labels.subnet_name}} CIDR {{$labels.cidr_block}} in AZ {{$labels.availability_zone}} is running out free IPs. Only {{$value}} left to use, which is less than 32.
```

## Usage

- Clone this repository
- Change src/main.py to expose the metric you need
  - Tips for debugging:
    - `helm lint helm`
    - `helm template helm`
    - `helm install --dry-run --debug test helm`
    - `helm upgrade --dry-run --debug test helm`
- Change helm/values.yaml to match your needs
- Install the helm chart
  - `helm install aws-custom-exporter helm`
  - If you want in another namespace than `default`, use ` --set namespace=monitoring` or update `namespace` in values.yaml
  Make sure Prometheus is configured to discover Monitoring Services in the namespace you are deploying to.
  - If you want to deploy in different region than `eu-west-1`, use `--set aws.region=us-east-1` or update `aws.region` in values.yaml
  - If you want to authenticate with AWS key/secret, use `--set aws.accessKeyID=keyid --set aws.secretAccessKey=secretkey` or update `aws` section in values.yaml

## Security

The default configuration uses IAM roles to authenticate with AWS. This is the recommended way to authenticate with AWS.
Make sure IAM user has the following permissions:
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "Stmt1488491317000",
            "Effect": "Allow",
            "Action": [
                "ec2:DescribeSubnets"
            ],
            "Resource": [
                "*"
            ]
        }
    ]
}
```