# custom-aws-prometheus-exporter
Utilize the boto3 library to retrieve and make accessible any Prometheus metric.

## Purpose
Sometimes [cloudwatch_exporter](https://github.com/prometheus/cloudwatch_exporter) or [yet-another-cloudwatch-exporter](https://github.com/nerdswords/yet-another-cloudwatch-exporter) do not expose a metric you might need. 

In this example, our custom exporter exposes `aws_vpc_subnet_free_ips` metric:

#### `GET /metrics`:
```
# HELP aws_vpc_subnet_free_ips Free IPs in each VPC Subnet
# TYPE aws_vpc_subnet_free_ips gauge
aws_vpc_subnet_free_ips{availability_zone="eu-west-1a",cidr_block="10.1.0.0/24",subnet_id="subnet-1",subnet_name="subnet-1",vpc_id="vpc-private"} 250.0
aws_vpc_subnet_free_ips{availability_zone="eu-west-1b",cidr_block="10.1.1.0/24",subnet_id="subnet-2",subnet_name="subnet-2",vpc_id="vpc-private"} 250.0
```

Here is an example of a Prometheus rule that can be used to alert on a VPC Subnet that has been running out of free IPs for more than 5m.
```
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
