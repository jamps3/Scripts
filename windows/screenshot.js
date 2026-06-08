const { chromium } = require("playwright");
const readline = require("readline");

const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout
});

function ask(question) {
  return new Promise((resolve) => {
    rl.question(question, resolve);
  });
}

(async () => {
  let url = await ask('Enter the URL to screenshot: ');
  rl.close();

  if (!url.startsWith('http://') && !url.startsWith('https://')) {
    url = 'https://' + url;
  }

  const browser = await chromium.launch();
  const page = await browser.newPage({
    viewport: { width: 1440, height: 1200 },
    deviceScaleFactor: 1,
  });

  await page.goto(url, {
    waitUntil: "networkidle",
  });

  const urlObj = new URL(url);
  const filename = `${urlObj.hostname}-screenshot.png`;

  await page.screenshot({
    path: filename,
    fullPage: true,
  });

  await browser.close();
})();