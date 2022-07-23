/**
 * @param {string} html 
 */
function extractYoutubeLinks(html) {
    const $ = cheerio.load(html);
    /** @type {{title:string, url:string}[]} */
    const links = [];
    $("a.yt-simple-endpoint[title]").each((idx, el) => {
        const title = $(el).attr("title");
        const url = $(el).attr("href");
        links.push({ title, url });
    });
    return links;
}

module.exports = extractYoutubeLinks;