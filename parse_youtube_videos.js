const assert = require("assert");
const path = require("path");
const fs = require("fs-extra");
const cheerio = require("cheerio");

async function main() {
    const html = await fs.readFile("./downloads/index.html", { encoding: "utf-8" });
    const $ = cheerio.load(html);
    $("a.yt-simple-endpoint[title]").each((idx, el) => {
        const title = $(el).attr("title");
        const url = $(el).attr("href");
        console.log(`[${title}](${url})`);
    });
}

main()