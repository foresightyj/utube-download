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
    const runs = await octokit.rest.actions.listWorkflowRunsForRepo({
        ...commonRepoInfo,
        per_page: 100
    });
    assert.strictEqual(runs.status, 200);
    const allRuns = runs.data.workflow_runs;
    console.log(`Deleting ${allRuns.length} runs`);
    for (const run of allRuns) {
        if (run.status === "completed") {
            const deletion = await octokit.rest.actions.deleteWorkflowRun({
                ...commonRepoInfo,
                run_id: run.id
            });
            assert.strictEqual(deletion.status, 204);
            console.log(`DELETED ${run.name} with run id ${run.id}`);
        }
    }
    console.log("DONE");
}

main();
