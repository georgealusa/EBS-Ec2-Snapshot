

def lambda_handler(event, context):
    import boto3, time
    from botocore.exceptions import ClientError
    
    # Instances to be published to SNS topic
    buckedUpInstances = []
    localtime = time.asctime( time.localtime(time.time()) ) 
    client = boto3.client('ec2', region_name="sa-east-1") #Region you want backups to happen
    
    sns = boto3.client('sns',  region_name="ap-northeast-2") #Region where the sns topic resides
    instances = client.describe_instances()
    
    #Iterate through all instances in the specified region
    for reservation in instances["Reservations"]:
        for instance in reservation["Instances"]:
            instanceId = instance["InstanceId"]
    
            #Iterate through all snapshots owned by self 
            snapshots = client.describe_snapshots(OwnerIds=["self"])
            for snapshot in snapshots["Snapshots"]:
                try:
    
                    #Implementation of retention period.(time interval specified on cron tab represents retention period of snapshots)
                    #Snapshots created earlier are deleted each time the script runs and replaced with new once. 
                    if snapshot["Tags"][0]["Value"] == instanceId:
                        client.delete_snapshot(SnapshotId=snapshot["SnapshotId"])
                        print(snapshot["SnapshotId"], " For instance", instance["InstanceId"], "was replaced Replaced on ", localtime)
                #exception for untagged snapshots. It means they were not created by the script. (Not all tagged snapshots are created by the script either.)
                except KeyError:
                  pass
    
            # Create snapshots of all volumes attached to the above instances
            for volume in instance["BlockDeviceMappings"]:
                #crucial to identify all instances which have been backed up by the script.
                buckedUpInstances.append(instance["InstanceId"]) 
                snapshot = client.create_snapshot(
                    VolumeId=volume["Ebs"]["VolumeId"],
                    TagSpecifications=[
                        {
                            'ResourceType': 'snapshot',
                            'Tags': [
                                {
                                    'Key': 'Name',
                                    #To uniquely identify each snapshot, we use instance ids as values to name of snapshots. 
                                    'Value': instanceId 
                                }
                            ]
                        }
                    ]
                )
    
    ## send notification 
    snsMessage = "Back up complete for instances: {} was done on {}".format(str(buckedUpInstances), localtime) #initialize Message
    message = sns.publish(
        TargetArn='arn:aws:sns:ap-northeast-2:060629120335:backup', #Replace with your ARN
        Message=snsMessage
    )
