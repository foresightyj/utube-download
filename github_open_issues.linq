<Query Kind="Program">
  <Reference Relative="..\..\.nuget\packages\newtonsoft.json\12.0.3\lib\netstandard2.0\Newtonsoft.Json.dll">&lt;NuGet&gt;\newtonsoft.json\12.0.3\lib\netstandard2.0\Newtonsoft.Json.dll</Reference>
  <Reference Relative="dlls\Octokit.dll">&lt;MyDocuments&gt;\LINQPad Queries\dlls\Octokit.dll</Reference>
  <Namespace>Newtonsoft.Json</Namespace>
  <Namespace>Octokit</Namespace>
  <Namespace>System.Threading.Tasks</Namespace>
</Query>

async void Main()
{
	var GITHUB_TOKEN = Util.GetPassword("github_token").Trim();
	var tokenAuth = new Credentials(GITHUB_TOKEN);
	var github = new GitHubClient(new ProductHeaderValue("MyAmazingApp"));
	github.Credentials = tokenAuth;
	var filePath = @"C:\Users\yuanjian\Downloads\ph_batch1.md";

	var urls = File.ReadAllText(filePath).Split('\n').Select(l => l.Trim()).Where(l => !string.IsNullOrEmpty(l)).ToList();

	var rand = new Random();
	const int SECOND = 1000;
	int count = 0;
	foreach (var url in urls)
	{
		count++;
		var title = "haha: " + url.Split('=').Last();
		var createIssue = new NewIssue(title);
		createIssue.Body = url;
		var issue = await github.Issue.Create("foresightyj", "utube-download", createIssue);
		Console.WriteLine($"create issue [{count}/{urls.Count}]: {title}");
		await Task.Delay(rand.Next(120 * SECOND, 300 * SECOND));
	}
	Console.WriteLine("DONE");
}
