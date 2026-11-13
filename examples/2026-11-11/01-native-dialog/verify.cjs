const assert = require("node:assert/strict");
const { pathToFileURL } = require("node:url");
const path = require("node:path");
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || "playwright");

async function run() {
  const browser = await chromium.launch({ channel: "chrome" });
  try {
    const page = await browser.newPage({ viewport: { width: 760, height: 470 } });
    await page.goto(pathToFileURL(path.join(__dirname, "index.html")).href);
    const active = () => page.evaluate(() => document.activeElement.id);
    const isOpen = () => page.locator("#discard").evaluate(dialog => dialog.open);
    const background = page.locator("#background");
    const status = page.locator("#status");
    const opener = page.locator("#open");

    await opener.click();
    assert.equal(await isOpen(), true);
    assert.equal(await active(), "cancel");
    console.log("open: focus=cancel");

    if (process.env.DIALOG_SCREENSHOT) {
      await page.screenshot({ path: process.env.DIALOG_SCREENSHOT });
    }

    const target = await background.boundingBox();
    await page.mouse.click(target.x + target.width / 2, target.y + target.height / 2);
    assert.match(await status.innerText(), /：0$/);
    assert.equal(await isOpen(), true);
    console.log("modal: background clicks=0");

    await page.keyboard.press("Escape");
    await page.waitForFunction(() => !document.querySelector("#discard").open);
    assert.equal(await active(), "open");
    console.log("Escape: open=false, focus=open");

    await background.click();
    assert.match(await status.innerText(), /：1$/);
    console.log("closed: background clicks=1");

    await opener.click();
    await page.getByRole("button", { name: "确认丢弃" }).click();
    await page.waitForFunction(() => document.querySelector("#status").value.includes("草稿已丢弃"));
    console.log("submit: returnValue=discard");
    assert.equal(await page.locator("#discard").evaluate(dialog => dialog.returnValue), "discard");
    console.log(`Chrome ${browser.version()}`);
  } finally {
    await browser.close();
  }
}

run().catch(error => {
  console.error(error);
  process.exitCode = 1;
});
