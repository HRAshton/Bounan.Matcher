using System;

namespace Bounan.Matcher.AwsCdk;

public class MatcherCdkStackConfig
{
    public required string AlertEmail { get; init; }

    public required string GetSeriesToMatchLambdaName { get; init; }

    public required string UpdateVideoScenesLambdaName { get; init; }

    public required string VideoRegisteredTopicArn { get; init; }

    public void Validate()
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(AlertEmail);
        ArgumentException.ThrowIfNullOrWhiteSpace(GetSeriesToMatchLambdaName);
        ArgumentException.ThrowIfNullOrWhiteSpace(UpdateVideoScenesLambdaName);
        ArgumentException.ThrowIfNullOrWhiteSpace(VideoRegisteredTopicArn);
    }
}