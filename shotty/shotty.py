import boto3
import click

session = boto3.Session(profile_name='shotty')
ec2 = session.resource('ec2')

def filter_instances(product):
    instances = []

    if product:
        filters = [{'Name':'tag:product', 'Values':[product]}]
        instances = ec2.instances.filter(Filters=filters)
    else:
        instances = ec2.instances.all()

    return instances

@click.group()
def instances():
    """Commands for instances"""

@instances.command('list')
@click.option('--product', default=None,
    help="Only instances for project (tag Product:<name>)")
def list_instances(product):
    "List EC2 instances"
    instances = filter_instances(product)

    if product:
        filters = [{'Name':'tag:product', 'Values':[product]}]
        instances = ec2.instances.filter(Filters=filters)
    else:
        instances = ec2.instances.all()

    for i in instances:
        tags = { t['Key']: t['Value'] for t in i.tags or [] }
        print(', '.join((
            i.id,
            i.instance_type,
            i.placement['AvailabilityZone'],
            i.state['Name'],
            i.public_dns_name,
            tags.get('product', '<no product>')
            )))
    return

@instances.command('stop')
@click.option('--product', default=None,
    help="Only instances for project")
def stop_instances(product):
    "Stop EC2 instances"
    instances = filter_instances(product)

    for i in instances:
        print("Stopping {0}...".format(i.id))
        i.stop()

    return

@instances.command('start')
@click.option('--product', default=None,
    help="Only instances for project")
def stop_instances(product):
    "Starting EC2 instances"
    instances = filter_instances(product)

    for i in instances:
        print("Starting {0}...".format(i.id))
        i.start()

    return

if __name__ == '__main__':
    instances()
