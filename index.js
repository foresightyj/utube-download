//@ts-check

const assert = require("assert");
const path = require("path");
const fs = require("fs-extra");
const minimist = require('minimist');
const filenamify = require('filenamify');
const { chromium } = require('playwright');

const opts = minimist(process.argv.slice(2));

const url = opts.url;
assert(typeof url === "string", "url arg required");

const DOWNLOADS_DIR = "./downloads";

/** @type {{[host:string]: (htmlPath: string)=> {title:string, url:string}[]}} */
const linkExtractorsMap = {
    "www.youtube.com": require("./link-extractors/youtube"),
};

(async () => {
    const u = new URL(url);
    const hostName = u.hostname;
    const fileName = filenamify(u.pathname + u.search, { replacement: "-" });

    const browser = await chromium.launch({ headless: true, });

    const page = await browser.newPage({
        viewport: {
            width: Number(opts.timeout) || 1280,
            height: Number(opts.timeout) || 9600,
        }
    });

    await page.goto(url, { waitUntil: opts.waitUtil || "load", timeout: Number(opts.timeout) || 30 });

    const content = await page.content();
    const htmlOutPath = path.join(DOWNLOADS_DIR, hostName, fileName + ".html");
    await fs.outputFile(htmlOutPath, content, { encoding: "utf-8" });

    const linkExtractor = linkExtractorsMap[hostName];
    if (!!linkExtractor) {
        const linksOutPath = path.join(DOWNLOADS_DIR, hostName, fileName + ".json");
        const links = linkExtractor(content);
        await fs.outputFile(linksOutPath, JSON.stringify(links, null, 2), { encoding: "utf-8" });
    }

    const pdfOutPath = path.join(DOWNLOADS_DIR, hostName, fileName + ".pdf");
    await page.emulateMedia({ media: "print" });
    await page.pdf({ path: pdfOutPath, format: opts.format || "A2" });
    await browser.close();
})();
