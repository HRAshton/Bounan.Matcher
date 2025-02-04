using Amazon.CDK;
using Microsoft.Extensions.Configuration;

namespace Bounan.Matcher.AwsCdk;

public class MatcherCdkStackConfig
{
    public MatcherCdkStackConfig(string cdkPrefix)
    {
        var localConfig = new ConfigurationBuilder()
            .AddJsonFile("appsettings.json")
            .AddEnvironmentVariables()
            .Build();

        AlertEmail = GetCdkValue(cdkPrefix, "alert-email", localConfig);
        LoanApiToken = GetCdkValue(cdkPrefix, "loan-api-token", localConfig);
        GetSeriesToMatchLambdaName = GetCdkValue(cdkPrefix, "get-series-to-match", localConfig);
        UpdateVideoScenesLambdaName = GetCdkValue(cdkPrefix, "update-video-scenes", localConfig);
        VideoRegisteredTopicArn = GetCdkValue(cdkPrefix, "video-registered-sns-topic-arn", localConfig);
    }

    public string AlertEmail { get; }

    public string LoanApiToken { get; }

    public string GetSeriesToMatchLambdaName { get; }

    public string UpdateVideoScenesLambdaName { get; }

    public string VideoRegisteredTopicArn { get; }

    private static string GetCdkValue(string cdkPrefix, string key, IConfigurationRoot localConfig)
    {
        var localValue = localConfig.GetValue<string>(key);
        return localValue is { Length: > 0 } ? localValue : Fn.ImportValue(cdkPrefix + key);
    }
}