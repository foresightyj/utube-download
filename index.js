//@ts-check

const assert = require("assert");
const path = require("path");
const fs = require("fs-extra");
const { chromium } = require('playwright');

const [url] = process.argv.slice(2);

assert(typeof url === "string", "usage: node index <url>");

const DOWNLOADS_DIR = "./downloads";

(async () => {
    const browser = await chromium.launch({
        headless: true,
    });
    const page = await browser.newPage({
        viewport: {
            width: 1280,
            height: 9600
        }
    });
    await page.goto(url);
    const content = await page.content();
    await fs.ensureDir(DOWNLOADS_DIR);
    await fs.outputFile(path.join(DOWNLOADS_DIR, "index.html"), content, { encoding: "utf-8" });
    await page.emulateMedia({ media: "print" });
    await page.pdf({
        path: path.join(DOWNLOADS_DIR, "index.pdf"),
        format: "A2"
    });
    await browser.close();
})();

