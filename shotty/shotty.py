import boto3
import botocore
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

def has_pending_snapshot(volume):
    snapshots = list(volume.snapshots.all())
    # Return either true or False
    # If there are snapshot, it will return the result of snapshot[0].state == 'pending'
    # If there isn't, it will return snapshots which is false or empty list
    return snapshots and snapshots[0].state == 'pending'

@click.group()
def cli():
    """Shotty manages snapshots"""

@cli.group('snapshots')
def snapshots():
    """Commands for snapshots"""

@snapshots.command('list')
@click.option('--product', default=None,
    help="Only instances for project (tag Product:<name>)")
# If --all is present, list_all is true
@click.option('--all', 'list_all', default=False, is_flag=True,
    help="List all snapshots for each volume, not just the most recent")
def list_snapshots(product, list_all):
    "List EC2 snapshots"
    instances = filter_instances(product)

    for i in instances:
        for v in i.volumes.all():
            for s in v.snapshots.all():
                print(", ".join((
                    s.id,
                    v.id,
                    i.id,
                    s.state,
                    s.progress,
                    s.start_time.strftime("%c")
                )))

                # Boto3 return the latest snapshot first. The following will
                # break after the latest. Unless list_all
                if s.state == 'completed' and not list_all: break

    return

@cli.group('volumes')
def volumes():
    """Commands for volumes"""

@volumes.command('list')
@click.option('--product', default=None,
    help="Only instances for project (tag Product:<name>)")
def list_volumes(product):
    "List EC2 volumes"
    instances = filter_instances(product)

    for i in instances:
        for v in i.volumes.all():
            print(", ".join((
            v.id,
            i.id,
            v.state,
            str(v.size) + "GiB",
            v.encrypted and "Encrypted" or "Not Encrypted"
        )))

    return

@cli.group('instances')
def instances():
    """Commands for instances"""

@instances.command('snapshot',
    help="Create snapshots of all volumes")
@click.option('--product', default=None,
    help="Only instances for project (tag Product:<name>)")
def create_snapshots(product):
    "Create snapshots for EC2 instances"
    instances = filter_instances(product)

    for i in instances:
        print("Stopping {0}...".format(i.id))

        i.stop()
        i.wait_until_stopped()

        for v in i.volumes.all():
            if has_pending_snapshot(v):
                print("  Skipping {0}, snapshot already in progress".format(v.id))
                continue

            print("  Creating snapshot of {0}".format(v.id))
            v.create_snapshot(Description="Created by Shotty")

        print("Starting {0}...".format(i.id))

        i.start()
        i.wait_until_running()

    print("Job's done!")

    return

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
        try:
            i.stop()
        except botocore.exceptions.ClientError as e:
            print(" Could not stop {0}. ".format(i.id) + str(e))
            continue

    return

@instances.command('start')
@click.option('--product', default=None,
    help="Only instances for project")
def stop_instances(product):
    "Starting EC2 instances"
    instances = filter_instances(product)

    for i in instances:
        print("Starting {0}...".format(i.id))
        try:
            i.start()
        except botocore.exceptions.ClientError as e:
            print(" Could not start {0}. ".format(i.id) + str(e))
            continue

    return

if __name__ == '__main__':
    cli()
