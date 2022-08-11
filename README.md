# Integrate api gateway with event bridge and invoke lambda

AWS Api gateway can be integrated with many aws services directly without using a compute layer between. This helps to eliminate lets say in lambda function to take the event and send it to eventbridge. 

Today we'll see how can we integrate api gateway to send message directly to eventbridge and invoke a lambda function from there. 

We'll use AWS SAM to build our infrastructure. The following is the architecture we'll make.
![Architecture diagram](https://drive.google.com/uc?id=1Ku168iK2XJRQOIvBcux5WwDcU7Zetc5C)

First the integration of api gateway and eventbridge. The code is below

    EventBridgeApi:  
      Type: AWS::Serverless::HttpApi  
      Properties:  
        DefinitionBody:  
          'Fn::Transform':  
            Name: 'AWS::Include'  
      Parameters:  
              Location: './api_definition.yaml'  
      
    HttpApiRole:  
      Type: "AWS::IAM::Role"  
      Properties:  
        AssumeRolePolicyDocument:  
          Version: "2012-10-17"  
      Statement:  
            - Effect: "Allow"  
      Principal:  
                Service: "apigateway.amazonaws.com"  
      Action:  
                - "sts:AssumeRole"  
      Policies:  
          - PolicyName: ApiWriteToEventBridge  
            PolicyDocument:  
              Version: '2012-10-17'  
      Statement:  
                Action:  
                - events:PutEvents  
                Effect: Allow  
                Resource:  
                  - !Sub arn:aws:events:${AWS::Region}:${AWS::AccountId}:event-bus/default

The first resource creates an API gateway resource from an api definition file. Then there is a IAM role resource which assumes a role on behalf of api gateway and allowes api gateway to write events to the default event bus in eventbridge. 

The defination of api is below

> api_definition.yaml

    openapi: "3.0.1"  
    info:  
      title: "API Gateway HTTP API to EventBridge"  
      version: "1"  
    paths:  
      /send-to-eventbridge:  
        post:  
          responses:  
            default:  
              description: "EventBridge response"  
      x-amazon-apigateway-integration:  
            integrationSubtype: "EventBridge-PutEvents"  
      credentials:  
              Fn::GetAtt: [HttpApiRole, Arn]  
            requestParameters:  
              Detail: "$request.body.Detail"  
      DetailType: MyDetailType  
              Source: MyCustomEvent  
            payloadFormatVersion: "1.0"  
      type: "aws_proxy"  
      connectionType: "INTERNET"

Note the `Source` value from above. We'll use it later.

Now we'll see the lambda function definition of SAM template

    EventBridgeInvokeFunction:  
      Type: AWS::Serverless::Function  
      Properties:  
        CodeUri: eventbridge_function/  
        Handler: app.lambda_handler  
        Runtime: python3.8  
        Events:  
          EventFromEventBus:  
            Type: CloudWatchEvent  
            Properties:  
              Pattern:  
                source:  
                  - MyCustomEvent

In the above block we can see the lambda function is being triggered from CloudWatchEvent(EventBridge). And the pattern match has to be from source `MyCustomEvent` which we declared in `api_definition.yaml`

The lambda function has a simple logger that logs the input event. Nothing fancy.

The output block looks like this

    ApiEndpoint:  
      Description: "API endpoint URL"  
      Value: !Sub "https://${EventBridgeApi}.execute-api.${AWS::Region}.amazonaws.com"

After deploying the stack we'll get the ApiEndpoint in console.

![Output of api sam deploy](https://drive.google.com/uc?id=1Z0giJ06y6wtZOC711Jo46Iy8zybUgb1_)

Copy the url and paste it in postman. Pick POST as method. Pick raw and json as request body type and the body must have a tag named `Detail` and the contents inside the `Detail` have to be an object. After calling the api we'll get a response like below with the `EventId`. 

![Checking in Postman](https://drive.google.com/uc?id=1bw4-eK1cRdesIWMUt3QMg3fYid3PLfh1)

The event is sent from api gateway to eventbridge and finally envoking the lambda function. 

The output of lambda function is below

![Lambda output](https://drive.google.com/uc?id=1nw2IGizKnKscp8fez7P7ugaXru2RcXKX)

We've successfully integrated API gateway with EventBridge and Lambda.

You can get the source code in the following link

https://github.com/masudur-rahman-niloy/ApiGw-EventBridge-Lambda
