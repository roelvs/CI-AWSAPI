import boto3
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

class AWS:
    def __init__(self):
        boto3.setup_default_session(region_name="us-east-1")

        self.ec2_assumed_client = None
        self.newsession_id = ""
        self.newsession_key = ""
        self.newsession_token = ""
        self.ec2 = None

    def authorize(self):
        # https://www.slsmk.com/use-boto3-to-assume-a-role-in-another-aws-account/
        # Create session using your current creds
        boto_sts = boto3.client('sts')

        # Request to assume the role like this, the ARN is the Role's ARN from
        # the other account you wish to assume. Not your current ARN.
        sts_response = boto_sts.assume_role(
            RoleArn="arn:aws:iam::584994643673:role/OrganizationAccountAccessRole",
            RoleSessionName='cloudinfra'
        )

        # Save the details from assumed role into vars
        self.newsession_id = sts_response["Credentials"]["AccessKeyId"]
        self.newsession_key = sts_response["Credentials"]["SecretAccessKey"]
        self.newsession_token = sts_response["Credentials"]["SessionToken"]

    def create_connection(self, region):

        self.ec2_assumed_client = boto3.client('ec2',
                                               aws_access_key_id=self.newsession_id,
                                               aws_secret_access_key=self.newsession_key,
                                               aws_session_token=self.newsession_token)
        self.ec2 = boto3.resource('ec2',
                                  region_name=region,
                                  aws_access_key_id=self.newsession_id,
                                  aws_secret_access_key=self.newsession_key,
                                  aws_session_token=self.newsession_token)
        return True

    def get_regional_instances(self, region):
        try:
            self.authorize()
            self.create_connection(region)
            print("\nEC2 instances in region {}: ".format(region))
            all_instances = self.ec2.instances.filter()
        except Exception as ex:
            return {"exception while requesting instances", 418}
        instance_list = []
        for instance in all_instances:
            state = "        "

            print('{} {} type: {} tags {}'.format(state, instance.id, instance.instance_type, instance.tags))

            simple_tags = {"instanceid": instance.id}
            try:
                for x in instance.tags:
                    singletag = {x["Key"]: x["Value"]}
                    simple_tags.update(singletag)
            except Exception as ex:
                pass

            instance_details = {'state': instance.state["Code"],
                                'type': instance.instance_type,
                                'tags': simple_tags}
            instance_list.append(instance_details)
            print(instance_details)
        return instance_list

    def get_regions(self):
        self.authorize()
        self.create_connection("us-east-1")  # region onbelangrijk
        regions = self.ec2_assumed_client.describe_regions()
        return regions

    def get_instances(self, region):
        self.authorize()
        try:
            self.create_connection(region)

            instance_list = self.get_regional_instances(region)

            result = jsonify(instance_list)
            print("RESULT " + str(result.data))
            return result, 200
        except:
            return "error while fetching this region", 418


aws = AWS()


@app.route('/get_regions')
def get_regions():
    return aws.get_regions()


@app.route('/get_instances')
def get_instances():
    region = request.args['region']

    instance_list = aws.get_regional_instances(region)
    try:
        result = jsonify(instance_list)
        print("RESULT " + str(result.data))
        return result, 200
    except:
        return "error while fetching this region", 500


@app.route('/')
def hello_world():
    return "hello world"


application = app

#below: only needed for a local dev server..
if __name__ == "__main__":
    # Only for debugging while developing. This will start a flask dev server, listening on port 80
    application.run(host='0.0.0.0', debug=False, port=8080)