
# Overview

This project is a simple serverless API hosted on AWS that provides one click access to viewing all of your unread Hipchat messages on iOS using the [Workflow](https://workflow.is) app. 

If you want an "easy button" access to unread messages because you don't like to or don't have time to click around, this will make life much easier. I use the Washington DC metro and have maybe 15 seconds of connectivity at stops. By the time I start the app, click around and wait for it to load messages... the train has literally left the station. The solution is also useful if you swipe away and clear notifications and need to review unread messages easily. 

Android users can use an app like Tasker to call the API and display the data sent back.

## Some more detail

Hipchat doesnt have a documented API to view unread messages. This app uses an undocumented API I found while reviewing the Hipchat Web App network calls. This API does not mark the messages as being read, which is ideal. 

Applications and technologies used:

- [AWS Lambda](https://aws.amazon.com/lambda/), [AWS API Gateway](https://aws.amazon.com/api-gateway/) - Look, no servers!
- [Python](http://python.org/) - Yup, serverless without NodeJS.
- [Serverless Framework](https://serverless.com) - Framework to setup and manage AWS resources
- [Hipchat access](https://hipchat.com/) - Assume you use Hipchat for chat.
- [Workflow on iOS](https://workflow.is) - Create a Today Widget for instant access - swipe down and click

# Setup

OK, lets get started. There are quite a few steps here and you may need 30 mins to 1 hour depending on your familiarity with AWS. 

*Note*

- The default setup will create a public API endpoint. Take a look at the *Private API Setup* section to make the API private. 
- The project has been tested on Ubuntu, macOS as well as Bash on Windows 10 with and without Docker.

## AWS Setup

Since we're working with AWS Lambda and AWS API Gateway, we need to setup AWS credentials. We are also using the Serverless framework to manage the AWS tech stack.

> Serverless needs a lot of privilages even if manually setup. If this concerns you, create a new AWS account to play around with.

### Serverless AWS credentials setup

- Follow the instructions at https://serverless.com/framework/docs/providers/aws/guide/credentials/ . They cover the setup pretty well.

### Manual AWS IAM Setup

If you are brave, you can setup the IAM user's role yourself. 

- Create an IAM Group with:
  - Attach Managed Policies:
    - AWSLambdaFullAccess - Create and manage Lambda functions
    - AmazonS3FullAccess - Create a bucket to store the lambda function code
    - CloudWatchLogsFullAccess - Create and manage Cloudwatch logs
    - AmazonAPIGatewayAdministrator - Create and manage API endpoints
    - IAMReadOnlyAccess - Read IAM access info
  - Create Custom Group Policy > Custom Policy:
    - Custom CloudFormation policy (below)- Create and manage CloudFormation stacks
```
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "Stmt1499009146000",
            "Effect": "Allow",
            "Action": [
                "cloudformation:*"
            ],
            "Resource": [
                "*"
            ]
        }
    ]
}
```
- Create an IAM User and assign the User the newly created Group
- Setup AWS credentials with this user's security credentials. Check the above link since it has a good overview.

## Hipchat Setup

- Setup a [Hipchat](https://hipchat.com/) team and account. Its free.
- Login and get an user specific API token from  - https://TEAMNAME.hipchat.com/account/api (Replace TEAMNAME with yours)
- This will be your `HIPCHAT_ACCESS_TOKEN`

## Code Setup

- Make sure you have Python 2.7.
- Install NodeJS - https://nodejs.org/en/download/
- Import helper bash commands - `source source.sh`
- Install Serverless - `s-install`

# Build and deploy

- Install Pythong dependencies to local site-packages - `s-requirements`. These will get packaged and deployed with your Lambda function.
- Deploy the service - `s-deploy`
- Get Stack info - `s-info`
    - This will display information about the stack. e.g. The API endpoint URL you need below
    - The resources used will be prefixed with `hipchat-dev` in AWS Lambda, AWS API Gateway and AWS CloudWatch logs.
    - Logs are setup to expire after 7 days.
    - Details are available in `serverless.yaml`

## Test the API

> Don't forget to replace `HIPCHAT_ACCESS_TOKEN` (see Hipchat Setup) and `APIID` (Output from serverless deploy)
> By default, the API is public. CHeck the section below to make it secure/private.

- Hipchat token in Query String
    - `curl https://APIID.execute-api.us-east-1.amazonaws.com/dev/hipchat/unread?access_token=HIPCHAT_ACCESS_TOKEN`
- Hipchat token in Header
    - `curl  -H "x-access-token: HIPCHAT_ACCESS_TOKEN" https://APIID.execute-api.us-east-1.amazonaws.com/dev/hipchat/unread`

Sample JSON Output

```
[
  {
    "messages":"Nik 2: Jul 02, 2017 16:12:54\nHipchat is pretty nice!!!",
    "name":"Khilnani"
  },
  {
    "messages":"Nik 2: Jul 02, 2017 02:28:50\nHI Nik, How are you?\nNik 2: Jul 02, 2017 16:14:00\nDo you have some time to chat today?",
    "name":"Nik 2"
  }
]
```

## Private API Setup

- Create an API Key - https://console.aws.amazon.com/apigateway/home?region=us-east-1#/api-keys
- Create a Usage Plan - https://console.aws.amazon.com/apigateway/home?region=us-east-1#/usage-plans
    - Add the API (`hipchat-dev`) and API Key you created to the Usage Plan.
- Update `private` to `true` in the `serverless.yaml` method definition for the `unread` function 
- Make API calls with the Request Header `x-api-key: APIKEY`

### Test the API

> Don't forget to replace `HIPCHAT_ACCESS_TOKEN` (see Hipchat Setup), `AWS_API_KEY` (from above)  and `APIID` (Output from serverless deploy)

- Hipchat token in Query String
    - curl -H "x-api-key: AWS_API_KEY" https://APIID.execute-api.us-east-1.amazonaws.com/dev/hipchat/unread?access_token=HIPCHAT_ACCESS_TOKEN
- Hipchat token in Header
    - curl -H "x-api-key: AWS_API_KEY" -H "x-access-token: HIPCHAT_ACCESS_TOKEN" https://APIID.execute-api.us-east-1.amazonaws.com/dev/hipchat/unread

# iOS Workflow App Setup

Once you have an api, you can call it from where ever you want. Since we (or I) want to use a phone as a remote, we'll use [Workflow on iOS](https://workflow.is). 

- Download the app from the app store - https://workflow.is/download
- Launch https://github.com/khilnani/hipchat-unread.serverless/blob/master/files/Hipchat%20Unread%20Sample.wflow?raw=true in Safari on your iOS device
    - Open the file using the Workflow app. 
    - It will create a workflow called 'Hipchat Unread Sample'
- Replace `https://APIID.execute-api.us-east-1.amazonaws.com/dev/hipchat/unread` with the url from the deployment stack output.
- Replace `HIPCHAT_ACCESS_TOKEN` with your Hipchat access token.
- Replace `API_KEY` with the AWS API Key created earlier
- Run the workflow!

## Creating the Workflow from scratch

> Workflow has pretty good documentation on using JSON APIs - https://workflow.is/docs/taking-advantage-of-web-apis

- Create a new Workflow
- Add a `Text` action and update it with the API endpoint `https://APIID.execute-api.us-east-1.amazonaws.com/dev/hipchat/unread?access_token=HIPCHAT_ACCESS_TOKEN`
- Add a `Get Contents of URL` action with the following (click Advanced):
    - Method: Get
    - Headers:
        - `x-access-token` - Hipchat Access Token. Use this if you do not want to pass the Hipchat token as a query param in the URL above.
        - `x-api-key`: AWS API Key. Needed if you made the API private. By default you do not need this.
- Add a `Get Dictionary from Input` action - to confirm the JSON from the API to a structured object
- Add a `Repeat with Each` action to loop through the messages
- Add a `Show Alert` action inside the repeat action to display the actual messages. Setup as below:
    - Title:  Type in `Room/User:`. Then click the space and select `Repeat Item`. Click `Repeat Name` to specific `Get Value for Key` as `name`. This is the name of the user or room.
    - Main content: Click the space and select `Repeat Item`. Click `Repeat Name` to specific `Get Value for Key` as `messages`. This is a single string with new lines seperating individual messages.
 - Set the workflow as a `Today Widget` in the Workflow's settings.
 - Save and run the workflow
