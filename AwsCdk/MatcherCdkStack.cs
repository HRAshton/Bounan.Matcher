using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using Amazon.CDK;
using Amazon.CDK.AWS.CloudWatch;
using Amazon.CDK.AWS.IAM;
using Amazon.CDK.AWS.Lambda;
using Amazon.CDK.AWS.Logs;
using Amazon.CDK.AWS.SNS;
using Amazon.CDK.AWS.SNS.Subscriptions;
using Amazon.CDK.AWS.SQS;
using Constructs;
using Microsoft.Extensions.Configuration;
using Newtonsoft.Json;
using AlarmActions = Amazon.CDK.AWS.CloudWatch.Actions;
using LogGroupProps = Amazon.CDK.AWS.Logs.LogGroupProps;

namespace Bounan.Matcher.AwsCdk;

[SuppressMessage("Performance", "CA1859:Use concrete types when possible for improved performance")]
public sealed class MatcherCdkStack : Stack
{
    internal MatcherCdkStack(Construct scope, string id, IStackProps? props = null) : base(scope, id, props)
    {
        var config = new ConfigurationBuilder()
            .AddJsonFile("appsettings.json")
            .AddEnvironmentVariables()
            .Build()
            .Get<MatcherCdkStackConfig>();
        ArgumentNullException.ThrowIfNull(config, nameof(config));
        config.Validate();

        var user = new User(this, "User");

        var videoRegisteredQueue = CreateVideoRegisteredQueue(config, user);
        GrantPermissionsForLambdas(config, user);

        var logGroup = CreateLogGroup();
        SetErrorAlarm(config, logGroup);
        SetNoLogsAlarm(config, logGroup);
        logGroup.GrantWrite(user);

        var accessKey = new CfnAccessKey(this, "AccessKey", new CfnAccessKeyProps { UserName = user.UserName });

        Out("Config", JsonConvert.SerializeObject(config));
        Out("LogGroupName", logGroup.LogGroupName);
        Out("UserAccessKeyId", accessKey.Ref);
        Out("UserSecretAccessKey", accessKey.AttrSecretAccessKey);
        Out("VideoRegisteredQueueUrl", videoRegisteredQueue.QueueUrl);
        Out(
            "env",
            $"""
             AWS_DEFAULT_REGION={Region};
             AWS_ACCESS_KEY_ID={accessKey.Ref};
             AWS_SECRET_ACCESS_KEY={accessKey.AttrSecretAccessKey};
             LOG_GROUP_NAME={logGroup.LogGroupName};
             GET_SERIES_TO_MATCH_LAMBDA_NAME={config.GetSeriesToMatchLambdaName};
             UPDATE_VIDEO_SCENES_LAMBDA_NAME={config.UpdateVideoScenesLambdaName};
             VIDEO_REGISTERED_QUEUE_URL={videoRegisteredQueue.QueueUrl};
             LOAN_API_TOKEN=;
             LOG_LEVEL=INFO;
             OMP_NUM_THREADS=1;
             """);
    }

    private IQueue CreateVideoRegisteredQueue(MatcherCdkStackConfig config, IGrantable user)
    {
        var newEpisodesTopic = Topic.FromTopicArn(this, "VideoRegisteredTopic", config.VideoRegisteredTopicArn);
        var newEpisodesQueue = new Queue(this, "VideoRegisteredQueue");
        newEpisodesTopic.AddSubscription(new SqsSubscription(newEpisodesQueue));

        newEpisodesQueue.GrantConsumeMessages(user);

        return newEpisodesQueue;
    }

    private void GrantPermissionsForLambdas(MatcherCdkStackConfig config, IGrantable user)
    {
        var getAnimeToDownloadLambda = Function.FromFunctionName(
            this,
            "GetSeriesToMatchLambda",
            config.GetSeriesToMatchLambdaName);
        getAnimeToDownloadLambda.GrantInvoke(user);

        var updateVideoStatusLambda = Function.FromFunctionName(
            this,
            "UpdateVideoScenesLambda",
            config.UpdateVideoScenesLambdaName);
        updateVideoStatusLambda.GrantInvoke(user);
    }

    private ILogGroup CreateLogGroup()
    {
        return new LogGroup(this, "LogGroup", new LogGroupProps
        {
            Retention = RetentionDays.ONE_WEEK,
            RemovalPolicy = RemovalPolicy.DESTROY,
        });
    }

    private void SetErrorAlarm(MatcherCdkStackConfig config, ILogGroup logGroup)
    {
        var metricFilter = logGroup.AddMetricFilter("ErrorMetricFilter", new MetricFilterOptions
        {
            FilterPattern = FilterPattern.AnyTerm("ERROR"),
            MetricNamespace = StackName,
            MetricName = "ErrorCount",
            MetricValue = "1",
        });

        var alarm = new Alarm(this, "LogGroupErrorAlarm", new AlarmProps
        {
            Metric = metricFilter.Metric(),
            Threshold = 1,
            EvaluationPeriods = 1,
            TreatMissingData = TreatMissingData.NOT_BREACHING,
        });

        var topic = new Topic(this, "LogGroupAlarmSnsTopic", new TopicProps());
        topic.AddSubscription(new EmailSubscription(config.AlertEmail));
        alarm.AddAlarmAction(new AlarmActions.SnsAction(topic));
    }

    private void SetNoLogsAlarm(MatcherCdkStackConfig config, ILogGroup logGroup)
    {
        var noLogsMetric = new Metric(new MetricProps
        {
            Namespace = "AWS/Logs",
            MetricName = "IncomingLogEvents",
            DimensionsMap = new Dictionary<string, string>
            {
                { "LogGroupName", logGroup.LogGroupName }
            },
            Statistic = "Sum",
            Period = Duration.Minutes(2),
        });

        var noLogAlarm = new Alarm(this, "NoLogsAlarm", new AlarmProps
        {
            Metric = noLogsMetric,
            Threshold = 0,
            ComparisonOperator = ComparisonOperator.LESS_THAN_OR_EQUAL_TO_THRESHOLD,
            EvaluationPeriods = 1,
            TreatMissingData = TreatMissingData.BREACHING,
            AlarmDescription = "Alarm if no logs received within 2 minutes"
        });

        var topic = new Topic(this, "NoLogAlarmSnsTopic", new TopicProps());
        topic.AddSubscription(new EmailSubscription(config.AlertEmail));
        noLogAlarm.AddAlarmAction(new AlarmActions.SnsAction(topic));
    }

    private void Out(string key, string value)
    {
        _ = new CfnOutput(this, key, new CfnOutputProps { Value = value });
    }
}