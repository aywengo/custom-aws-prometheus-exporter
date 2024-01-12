import os
import boto3
from flask import Flask
from prometheus_client import Gauge, make_wsgi_app
from werkzeug.middleware.dispatcher import DispatcherMiddleware
from werkzeug.serving import run_simple
from threading import Thread
import time

# Initialize Flask app
app = Flask(__name__)

# Get region from environment variables
region = os.getenv('AWS_REGION', 'us-east-1')

# Initialize AWS Session
session = boto3.Session(
    region_name=region  # Use environment variable as region
)

# Get EC2 resource
ec2 = session.resource('ec2')

# Define Gauge Metric
g = Gauge('aws_vpc_subnet_free_ips', 'Free IPs in each VPC Subnet',
          ['vpc_id', 'subnet_id', 'cidr_block', 'subnet_name', 'availability_zone', 'total_ips'])


def update_metrics():
    while True:
        for vpc in ec2.vpcs.all():
            for subnet in vpc.subnets.all():
                total_ips = 2 ** (32 - int(subnet.cidr_block.split('/')[-1]))
                available_ips = subnet.available_ip_address_count

                subnet_name = None
                for tag in subnet.tags or []:
                    if tag['Key'] == 'Name':
                        subnet_name = tag['Value']
                        break

                # Set Gauge value for each subnet
                g.labels(vpc_id=vpc.id, subnet_id=subnet.id, cidr_block=subnet.cidr_block, subnet_name=subnet_name,
                         availability_zone=subnet.availability_zone, total_ips=total_ips).set(available_ips)
        time.sleep(60)  # Update every 60 seconds


@app.route("/")
def hello():
    return f"Exposing custom metrics for AWS VPC Subnets in {region} region."


if __name__ == "__main__":
    # Start a background thread for updating metrics
    Thread(target=update_metrics).start()

    # Add prometheus wsgi middleware to route /metrics requests
    app.wsgi_app = DispatcherMiddleware(app.wsgi_app, {
        '/metrics': make_wsgi_app()
    })

    app.run(host="0.0.0.0", port=9106)