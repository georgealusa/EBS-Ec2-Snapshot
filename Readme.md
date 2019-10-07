
## Automating EC2 Backup

#### Backup decision flowchart.
The diagram below is a decision flowchart to guide when to consider the options provided:

![flowchart](https://github.com/enquizit/DDD-EQ-Tasks/blob/development/Task%2013/files/Backup%20decision%20flowchat.png)

## Disk Mirroring(RAID 1)
This solution provides the replication of data between two or more disks. 
Though not a good solution when cost is a determinant factor, it should be considered for auto recovery due to the fact that data is replicated to the secondary disk in real-time. 
### Pros
1. Offers real-time security by duplicating data across multiple disks.
2. Offers good read and write speeds compared to that of a single drive.
3. Incase of failure, data is copied to the replacement drive without human intervention

### Cones
1. The effective storage capacity is only half of the total drive capacity because all data get written twice.

## Snapshots
This solution takes a copy of ebs volumes in current time and stores it in s3.
### Pros 
1. Cost effective
2. Provides block-level incremental backup that saves storage space

### Cones
1. Takes time to recover from a snapshot.
2. Incase of failure, a huge amount of data might be lost between snapshots.

# How to Automating the backup process of EC2 Instances

# Option 1
To automate the EC2 Backup, you will need to write a script using AWS’ API.
Below is a step by step process which should be followed in the script:
- Connect to AWS through API(Boto3)
- Get the list of instances.
- Create snapshot of EBS volumes attached to the instances 
- The retention period to the snapshot will be determined by the time interval specified.
- Delete the snapshot if it is older than the retention period.(Automatically deleted every time the script is executed)

The function takes incremental snapshots of all volumes attached to each instance in your specified region and tags the snapshots created with respective instance IDs

#### Instructions
1. [Create an SNS topic](https://docs.aws.amazon.com/sns/latest/dg/CreateTopic.html) and [subscribe for notifications](https://docs.aws.amazon.com/sns/latest/dg/SubscribeTopic.html)   
 
2. Create a role that allows lambda to execute code on your behalf.
    [How to create lambda function role](https://docs.aws.amazon.com/lambda/latest/dg/with-s3-example-create-iam-role.html)
3. Navigate to lambda on AWS and Create a new lambda function.

  - On Name, type the name of your function
  - On Runtime, Select Python 3.6
  - On Role select Choose an existing role
  - Select the role created on step 2 on existing role field
  - Click on Create Function
  - Navigate to Function code and select Edit Code inline on Code entry type
  - Clear the contents of the window and paste the contents code.py
  - Navigate to Basic settings and increase memory and timeout options.
  - Select on save followed by test and type in a name of your choice on event name
  - Select Create
      
4. On CloudWatch, create a rule to trigger the function. The rule contains the schedule under which the script should be running. 
     [How to create CloudWatch rule](https://docs.aws.amazon.com/AmazonCloudWatch/latest/events/Create-CloudWatch-Events-Rule.html)
     
  - Select create Rule on Rules
  - On Event Source check Schedule then Cron expression. For a schedule of every midnight in 2018 the cron expression will be:  ``00 00 * * ? 2018``
  - On Targets Select Lambda Function and select the function created in step 2
  - Select Configure Function

## NOTE:
On the script, change to your region, and use your ARN for the script to run. i.e :
```
    client = boto3.client('ec2', region_name="sa-east-1") #Region you want backups to happen

    sns = boto3.client('sns',  region_name="ap-northeast-2") #Region where the sns topic resides

    TargetArn='arn:aws:sns:ap-northeast-2:060629120335:backup', #Replace with your ARN
```

Find the script [here](https://github.com/enquizit/DDD-EQ-Tasks/blob/development/Task%2013/code.py)


# Option 2

# Automated Backup using AWS Ops Automator
This option implements snapshots as a backup solution. Snapshots take incremental backups of your data, which means only the portion of the disk containing data is backed up. For this reason, it is a solution to consider when cost is a determinant factor.
  ### Overview
AWS Ops Automator is a solution that enables customers to easily configure schedules to automatically create, copy, and delete EBS snapshots, and copy and delete Amazon Redshift snapshots. It also enables you to automatically set the throughput capacity for Amazon DynamoDB on a schedule.

  ### Cost
The customer is responsible for the cost of the AWS services used while running the solution. 
The cost of running this solution with default settings in the US East(N. Virginia) region is approximately $10 per month.
(The cost estimate assumes 1 GB of Amazon DynamoDB data storage at the default throughput capacity, 1 GB of Amazon CloudWatch Logs ingested, 
1 million AWS Lambda function executions, and 1 million CloudWatch custom events generated.)

 ### Features
This solution includes an AWS CloudFormation template that you deploy in the primary account.
The template launches all components of the solution that include:

 1. Lambda functions that manage triggering events, resource selection, task execution, concurrency control, and completion.
 2. Amazon DynamoDB tables that store task-related data.
 3. Amazon CloudWatch for logging.
 4. Amazon Simple Notification Service (Amazon SNS) for push notifications.
 
The primary template also generates additional AWS CloudFormation templates in an S3 bucket which allow you to configure tasks specified by each template. During initial configuration of the primary AWS CloudFormation template, you define a tag key you will use to identify resources that will receive automated actions (Create snapshots, Delete snapshots etc).

## Note
This solution uses AWS Lambda, Amazon DynamoDB, and Amazon CloudWatch, which are currently available in specific AWS Regions only. Therefore, you must launch this solution an AWS Region where these services are available. For the most current AWS service availability by region, see [AWS service offerings by region.](https://aws.amazon.com/about-aws/global-infrastructure/regional-product-services/) 

# Implementation


### Step 1. Launch the AWS Ops Automator Stack in the Primary Account
This automated AWS CloudFormation template deploys the AWS Ops Automator in your primary account. 
1. Follow the following link to sign in and launch the ops-automator AWS CloudFormation template.

[![Launch Stack](https://s3.amazonaws.com/cloudformation-examples/cloudformation-launch-stack.png)](https://console.aws.amazon.com/cloudformation/home?region=eu-west-1#/stacks/new?stackName=OpsAutomator&templateURL=https:%2F%2Fs3.amazonaws.com%2Fsolutions-reference%2Fops-automator%2Flatest%2Fops-automator.template)

or

Download the templet from [here](https://s3.amazonaws.com/solutions-reference/ops-automator/latest/ops-automator.template) for your own implementation. 

2. Select **Next**
3. On the **Specify Details** page
- Give the stack a name. 
- Under **Parameters** on **Ops Automator Tagname**, specify the tag key to identify the resources that will receive automated tasks. (**OpsAutomatorTaskList**) is the default tag key.
- Select **Next.**
4. On the **Options** page, choose **Next**
5. On the **Review** page, check the box **I acknowledge that AWS CloudFormation might create IAM resources.** and select **Create**



### Step 2. Tag the resources to receive the automated action (instances you want to backup).

For the AWS Ops Automator to recognize a resource, the tag key on your instance must match the custom tag that will be defined when deploying AWS CloudFormation template.(eg create a tag on all instances you want to backup with a key:OpsAutomatorTaskList and value of your choice. When creating the stack, you will specify the key.)


### Step 3. Launch a Task Template in the Primary Account

#### A To schedule snapshot creation

1. After completion of stack creation on step one, **select the ddbtabless3template** stack and navigate to outputs. 
2. Copy the value of the bucket name under: key **"Configuration"**
3. Open s3 console and search the bucket.
4. In the **Configuration** folder, select the template for creating EC2 snapshots and copy the **Link** to that templet.

               Ec2CreateSnapshot.template

5. In the AWS CloudFormation console, select **Create Stack.**

6. Select **Specify an Amazon S3 template URL.**, past the link copied in 4 above and select **Next.**

7. Enter a **Stack name.**

8. Under **Parameters**, review the parameters for the template and modify them as necessary. 
(eg, configure the parameters under the following values:)

- Task interval  00 00 * * ? * (take snapshots every midnight).
- Regions  *   (run the solution in all regions)
- Copied instance tags  *  (Apply all instance tags to the snapshot)
- Copied volume tags  *   (Apply all volume tags to the snapshot)

10. Select **Next.** 

11. Under Options, Select **Next** then **Create**.

12. Choose  to deploy the stack.

#### B To schedule snapshot Deletion

1. In the **Configuration** folder of the bucket opened in **A** above, select the template for deleting EC2 snapshots and copy the **Link** to that templet.
2. In the AWS CloudFormation console, select **Create Stack.**

3. Select **Specify an Amazon S3 template URL.**, past the link copied in 1 above and select **Next.**

4. Enter a **Stack name.**
5. Under **Parameters**, review the parameters for the template and modify them as necessary. 
(eg, configure the parameters under the following values:)

- Task interval  00 00 * * ? * (Deletes snapshots every midnight).
- Tag filter OpsAutomatorTaskList (OpsAutomatorTaskList is the default)
- Regions  *   (run the solution in all regions)
- Retention days 1
- Retention count 0
### Note:
   put 0 on **Retention days** to use **Retention count** and 0 on **Retention count** to use **Retention days**.
   
 6. On the options page, choose **Next**.
 7. Choose **Create** in the **Review** page.



 
 
