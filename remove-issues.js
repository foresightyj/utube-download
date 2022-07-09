//@ts-check

const assert = require("assert");
const { Octokit, App } = require("octokit");

const GITHUB_TOKEN = process.env.GITHUB_TOKEN;

assert(typeof GITHUB_TOKEN === "string", "GITHUB_TOKEN env not found")

const commonRepoInfo = {
    owner: "foresightyj",
    repo: "utube-download",
};

async function main() {
    const octokit = new Octokit({ auth: GITHUB_TOKEN });
    const issues = await octokit.rest.issues.listForRepo({
        ...commonRepoInfo,
        filter: "created",
        sort: "created",
        direction: "desc",
        per_page: 100
    });
    assert.strictEqual(issues.status, 200);
    const allIssues = issues.data;
    for (const issue of allIssues) {
        if (!issue.title.includes("http")) {
            console.log(`Please delete ${issue.title} manually: ${issue.html_url}`);
        }
    }
    console.log("DONE");
}

main();
