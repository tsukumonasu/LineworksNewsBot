import json
import os
import requests
import urllib
import datetime
import urllib.parse
import tweepy
import jwt
import boto3
from base64 import b64decode


def get_jwt():
    timestamp = datetime.datetime.now().timestamp()
    jwt_token = jwt.encode(
        {
            "iss": decrypt(os.environ['LW_SERVER_ID']),
            "iat": timestamp,
            "exp": timestamp + 3600
        },
        boto3.resource('s3').Bucket(os.environ['LW_SERVER_KEY_BUCKET']).Object('lwlambda.key').get()[
          'Body'].read().decode('utf-8'),
        algorithm="RS256")
    return jwt_token


def get_token():
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'
    }
    form_data = {
        "grant_type": urllib.parse.quote("urn:ietf:params:oauth:grant-type:jwt-bearer"),
        "assertion": get_jwt()
    }
    r = requests.post(url='https://authapi.worksmobile.com/b/' + decrypt(os.environ['LW_API_KEY']) + '/server/token',
                      data=form_data,
                      headers=headers)
    body = json.loads(r.text)
    return body["access_token"]


def post_lw_tweets():
    url = 'https://apis.worksmobile.com/r/%s/message/v1/bot/%s/message/push' % (
        decrypt(os.environ['LW_API_KEY']), os.environ['LW_BOT_ID'])
    headers = {
        'Content-Type': 'application/json; charset=UTF-8',
        'consumerKey': decrypt(os.environ['LW_CONSUMER_KEY']),
        'Authorization': ('Bearer %s' % get_token())
    }
    payload = {
        'roomId': os.environ['LW_ROOM_ID'],
        'content': {
            'type': 'text',
            'text': get_tweets()
        }
    }

    result = requests.post(url, data=json.dumps(payload), headers=headers)
    print(result.text)

    return result.status_code


def get_tweets():
    auth = tweepy.OAuthHandler(decrypt(os.environ['TWITTER_CONSUMER_KEY']),
                               decrypt(os.environ['TWITTER_CONSUMER_SECRET']))
    auth.set_access_token(decrypt(os.environ['TWITTER_ACCESS_TOKEN']),
                          decrypt(os.environ['TWITTER_ACCESS_TOKEN_SECRET']))
    api = tweepy.API(auth)

    tweets = api.user_timeline(include_rts=False,
                               screen_name=os.environ['TWITTER_SCREEN_NAME'],
                               count=int(os.environ['TWITTER_MAX_COUNT']))
    tweets.reverse()  # 降順にする
    yesterday = datetime.datetime.now() + datetime.timedelta(days=-1)  # 昨日
    tw_str = '【' + os.environ['TWITTER_SCREEN_NAME'] + datetime.datetime.now().strftime(' %m/%d') + 'のニュース】\n\n'
    for tweet in tweets:

        tw_time = tweet.created_at + datetime.timedelta(hours=9)  # UTC→JST

        if tw_time < yesterday:
            # 昨日以前は不要
            continue

        tw_str += tw_time.strftime('%m/%d %H:%M')

        lines = tweet.text.split('\n')  # 改行で分ける
        for i in range(0, len(lines)):  # 多分一番最後の行は不要
            line = lines[i]
            if line == '':
                continue
            if line[0:1] == '#':  # ハッシュタグ行は見ない
                continue
            tw_str += ' ' + lines[i]
        tw_str += '\n\n'
    return tw_str.strip()


def decrypt(enc):
    return boto3.client('kms').decrypt(
        CiphertextBlob=b64decode(enc),
        EncryptionContext={'LambdaFunctionName': os.environ['AWS_LAMBDA_FUNCTION_NAME']}
    )['Plaintext'].decode('utf-8')


def handler(event, context):
    return post_lw_tweets()
