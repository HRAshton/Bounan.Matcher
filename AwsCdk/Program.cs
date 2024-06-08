using Amazon.CDK;
using Bounan.Matcher.AwsCdk;

var app = new App();
_ = new MatcherCdkStack(app, "Bounan-Matcher", new StackProps());
app.Synth();