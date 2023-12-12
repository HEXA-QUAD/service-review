import boto3

def send2SNS():
    aws_access_key_id = 'AKIA2Y7LLO7R5EXFRGK2'
    aws_secret_access_key = '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'
    region_name = 'us-east-1'
    sns_topic_arn = 'arn:aws:sns:us-east-1:740838569955:new_post_sns'

    sns_client = boto3.client('sns', aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key, region_name=region_name)

    message = 'test'

    response = sns_client.publish(
        TopicArn=sns_topic_arn,
        Message=message
    )

    # print("MessageId:", response['MessageId'])
