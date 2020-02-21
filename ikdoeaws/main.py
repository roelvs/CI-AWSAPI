import boto3
from flask import Flask, render_template
app = Flask(__name__)

boto3.setup_default_session(region_name="us-east-1")


def get_regional_instances(region):
    ec2 = boto3.resource('ec2',
                         region_name=region,
                         aws_access_key_id=newsession_id,
                         aws_secret_access_key=newsession_key,
                         aws_session_token=newsession_token)

    print("\nEC2 instances in region {}: ".format(region))

    all_instances = ec2.instances.filter()
    instance_list = []
    for instance in all_instances:
        state = "        "

        if instance.state["Code"] == 16:
            state = "\033[92mRUNNING\x1b[0m "
        print('{} {} type: {} tags {}'.format(state, instance.id, instance.instance_type, instance.tags[0]))
        instance_details = {'state': instance.state["Code"],
                            'type': instance.instance_type,
                            'tags': instance.tags}
        instance_list.append(instance_details)
    return instance_list

@app.route('/')
def hello_world():
    resources = []
    for region in regions['Regions']:
        try:
            instance_list = get_regional_instances(region['RegionName'])

            if len(instance_list):
                resources.append({region['RegionName']: instance_list})
        except:
            pass
        continue
    return render_template('index.html', regions=regions, test=resources)


# https://www.slsmk.com/use-boto3-to-assume-a-role-in-another-aws-account/
# Create session using your current creds
boto_sts = boto3.client('sts')

# Request to assume the role like this, the ARN is the Role's ARN from
# the other account you wish to assume. Not your current ARN.
stsresponse = boto_sts.assume_role(
    RoleArn="arn:aws:iam::584994643673:role/OrganizationAccountAccessRole",
    RoleSessionName='cloudinfra'
)

# Save the details from assumed role into vars
newsession_id = stsresponse["Credentials"]["AccessKeyId"]
newsession_key = stsresponse["Credentials"]["SecretAccessKey"]
newsession_token = stsresponse["Credentials"]["SessionToken"]

ec2_assumed_client = boto3.client('ec2',
                                  aws_access_key_id=newsession_id,
                                  aws_secret_access_key=newsession_key,
                                  aws_session_token=newsession_token)
regions = ec2_assumed_client.describe_regions()

app.run()

