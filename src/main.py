import os
import boto3
from flask import Flask
from prometheus_client import Gauge, make_wsgi_app
from werkzeug.middleware.dispatcher import DispatcherMiddleware
from threading import Thread
import time

# Initialize Flask app
app = Flask(__name__)

# Get region from environment variables
region = os.getenv('AWS_REGION', 'us-east-1')

# Initialize AWS Session
session_kwargs = {'region_name': region}
if 'AWS_ACCESS_KEY_ID' in os.environ and 'AWS_SECRET_ACCESS_KEY' in os.environ:
    session_kwargs.update(
        {
            'aws_access_key_id': os.environ['AWS_ACCESS_KEY_ID'],
            'aws_secret_access_key': os.environ['AWS_SECRET_ACCESS_KEY']
         })
session = boto3.Session(**session_kwargs)

# Get EC2 resource
ec2 = session.resource('ec2')

# Define Gauge Metric
gauge_free_ips = Gauge('aws_vpc_subnet_free_ips', 'Free IPs in each VPC Subnet',
                       ['vpc_id', 'subnet_id', 'cidr_block', 'subnet_name', 'availability_zone', 'total_ips'])

# Add more metrics if needed
# gauge_total_ips = Gauge('aws_vpc_subnet_total_ips', 'Total IPs in each VPC Subnet',
#                                 ['vpc_id', 'subnet_id', 'cidr_block', 'subnet_name', 'availability_zone'])


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
                gauge_free_ips.labels(vpc_id=vpc.id, subnet_id=subnet.id, cidr_block=subnet.cidr_block, subnet_name=subnet_name,
                                      availability_zone=subnet.availability_zone, total_ips=total_ips).set(available_ips)
                # Add more metrics if needed
                # gauge_total_ips.labels(vpc_id=vpc.id, subnet_id=subnet.id, cidr_block=subnet.cidr_block, subnet_name=subnet_name,
                #                        availability_zone=subnet.availability_zone).set(total_ips)
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
