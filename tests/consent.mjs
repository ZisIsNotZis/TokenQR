import assert from 'node:assert/strict';
import {mkdir} from 'node:fs/promises';
import {join} from 'node:path';
import {pathToFileURL} from 'node:url';

const [site, relay, screenshotDir] = process.argv.slice(2);
assert.ok(site && relay, 'Run this test through tests/consent_fixture.py');
const allowedOrigins = new Set([new URL(site).origin, new URL(relay).origin]);
assert.ok([...allowedOrigins].every(origin => /^http:\/\/127\.0\.0\.1:\d+$/.test(origin)));
const {chromium} = await import(process.env.PLAYWRIGHT_MODULE
  ? pathToFileURL(process.env.PLAYWRIGHT_MODULE).href
  : 'playwright');
const browser = await chromium.launch({executablePath: process.env.CHROME_BIN});

const providerName = 'Local fixture provider';
const dummyCredential = 'Bearer integration-dummy';
const ordinaryPurpose = 'Local synthetic chat';
const prompt = 'Synthetic acceptance greeting';
const desktop = {width: 1280, height: 720};
const narrow = {width: 390, height: 844};
const cases = [
  ['desktop-approve', desktop, 'confirm'],
  ['desktop-decline', desktop, 'cancel'],
  ['narrow-approve', narrow, 'confirm'],
  ['narrow-decline', narrow, 'cancel'],
  ['narrow-long-content', narrow, 'cancel', true],
];

async function events() {
  const response = await fetch(`${site}/_fixture/events`);
  assert.equal(response.status, 200);
  return response.json();
}

async function hitTarget(page, id, checkSize = true) {
  const hit = await page.locator(`#${id}`).evaluate(element => {
    const {x, y, width, height, right, bottom} = element.getBoundingClientRect();
    const center = {x: x + width / 2, y: y + height / 2};
    const top = document.elementFromPoint(center.x, center.y);
    return {
      x, y, width, height, right, bottom, center,
      inViewport: x >= 0 && y >= 0 && right <= innerWidth && bottom <= innerHeight,
      interactive: !element.disabled && (top === element || element.contains(top)),
    };
  });
  assert.ok(hit.inViewport && hit.interactive, `#${id} is not hit-testable in view: ${JSON.stringify(hit)}`);
  if (checkSize) assert.ok(hit.width >= 44 && hit.height >= 44, `#${id} is smaller than 44×44`);
  return hit;
}

async function runCase(name, viewport, action, longContent) {
  const contexts = [];
  const browserErrors = [];
  async function newPage() {
    const context = await browser.newContext({viewport, serviceWorkers: 'block'});
    contexts.push(context);
    await context.route('**/*', async route => {
      const request = new URL(route.request().url());
      if (allowedOrigins.has(request.origin)) await route.continue();
      else {
        browserErrors.push(`Blocked request to ${request.origin}`);
        await route.abort();
      }
    });
    const page = await context.newPage();
    page.setDefaultTimeout(6000);
    page.on('pageerror', error => browserErrors.push(error.message));
    await page.goto(`${site}/tokenqr.html`);
    return page;
  }

  try {
    const receiver = await newPage();
    const provider = await newPage();
    const start = await events();
    const purpose = longContent ? `${ordinaryPurpose} ${'WrappedPurpose'.repeat(65)} end` : ordinaryPurpose;
    const models = ['fixture-model'];
    if (longContent) models.push(...Array.from({length: 32}, (_, i) => `fixture-model-${i}-${'long'.repeat(30)}`));
    await receiver.locator('#relay').fill(relay);
    await receiver.locator('#app').fill('Fixture receiver');
    await receiver.locator('#purpose').fill(purpose);
    await receiver.locator('#make').click();
    await receiver.locator('#qr canvas').waitFor({state: 'visible'});
    const payload = await receiver.locator('#qrtext').textContent();
    const request = JSON.parse(payload);
    assert.equal(request.v, 'TQR1');
    assert.ok(request.r.startsWith(`${relay}/`));
    assert.ok(!payload.includes(dummyCredential));

    await provider.locator('#providerTab').click();
    await provider.locator('#addProvider').click();
    for (const [id, value] of Object.entries({
      pfName: providerName, pfBase: `${site}/v1`, pfToken: dummyCredential, pfModels: models.join(','),
    })) await provider.locator(`#${id}`).fill(value);
    await provider.locator('#pfSave').click();
    await provider.locator('#code').fill(payload);
    await provider.locator('#parse').click();

    // Sample before any action that might scroll the dialog into view. Playwright's
    // normal click auto-scrolls to targets and would not catch the original bug.
    const initial = {
      confirm: await hitTarget(provider, 'confirm'),
      cancel: await hitTarget(provider, 'cancel'),
    };
    assert.equal(await provider.locator('#modal').getAttribute('open'), '');
    assert.equal(await provider.locator('#requestApp').textContent(), 'Fixture receiver');
    assert.equal(await provider.locator('#requestPurpose').textContent(), purpose);
    assert.ok((await provider.locator('#requestExpiry').textContent()).trim());
    assert.equal(await provider.locator('#pick option:checked').textContent(), providerName);
    assert.match(await provider.locator('#rawNote').textContent(), /原始 Token/);
    assert.equal(await provider.locator('#advanced').getAttribute('open'), null);
    if (!longContent) {
      const qrHint = receiver.locator('#qrHint');
      assert.equal(await qrHint.isVisible(), true);
      assert.match(await qrHint.textContent(), /Provider.*粘贴/);
      assert.equal(await provider.getByRole('heading', {name: '粘贴 Token QR'}).count(), 1);
      assert.equal(await provider.getByLabel('复制电脑端生成的二维码内容').inputValue(), payload);
      if (viewport.width === narrow.width) {
        const layout = await receiver.evaluate(() => ({
          page: document.documentElement.scrollWidth,
          viewport: document.documentElement.clientWidth,
          qrRight: document.querySelector('#qr canvas').getBoundingClientRect().right,
          qrText: document.querySelector('#qrtext').scrollWidth,
          qrTextBox: document.querySelector('#qrtext').clientWidth,
        }));
        assert.ok(layout.page <= layout.viewport && layout.qrRight <= layout.viewport
          && layout.qrText <= layout.qrTextBox, `Narrow receiver overflows: ${JSON.stringify(layout)}`);
      }
      for (const id of ['requestApp', 'requestPurpose', 'requestExpiry', 'pick', 'rawNote']) {
        await hitTarget(provider, id, false);
      }
    }
    if (screenshotDir) await provider.screenshot({path: join(screenshotDir, `${name}.png`)});

    if (longContent) {
      const body = provider.locator('.consent-body');
      const box = await body.boundingBox();
      const metrics = () => body.evaluate(element => ({
        top: element.scrollTop,
        visibleHeight: element.clientHeight,
        height: element.scrollHeight,
        visibleWidth: element.clientWidth,
        width: element.scrollWidth,
        dialogWidth: element.closest('dialog').scrollWidth,
        dialogVisibleWidth: element.closest('dialog').clientWidth,
      }));
      const before = await metrics();
      assert.equal(before.top, 0);
      assert.ok(before.height > before.visibleHeight, 'Long purpose should need body scrolling');
      await provider.mouse.move(box.x + box.width / 2, box.y + box.height / 2);
      await provider.mouse.wheel(0, before.height);
      await provider.waitForFunction(() => document.querySelector('.consent-body').scrollTop > 0);
      await provider.locator('#advanced summary').click();
      assert.equal(await provider.locator('#models input').count(), models.length);
      const expanded = await metrics();
      assert.ok(expanded.height > before.height);
      assert.ok(expanded.width <= expanded.visibleWidth + 1 && expanded.dialogWidth <= expanded.dialogVisibleWidth + 1,
        `Long settings overflow horizontally: ${JSON.stringify(expanded)}`);
      await provider.mouse.move(box.x + box.width / 2, box.y + box.height / 2);
      await provider.mouse.wheel(0, expanded.height);
      await provider.waitForFunction(() => {
        const body = document.querySelector('.consent-body');
        return body.scrollTop + body.clientHeight >= body.scrollHeight - 2;
      });
      await hitTarget(provider, 'create');
      await hitTarget(provider, 'confirm');
      await hitTarget(provider, 'cancel');
      if (screenshotDir) await provider.screenshot({path: join(screenshotDir, `${name}-advanced.png`)});
    }

    const relayPath = new URL(request.r).pathname;
    const hit = await hitTarget(provider, action);
    if (action === 'confirm') {
      const post = provider.waitForResponse(r => r.url() === request.r && r.request().method() === 'POST');
      await provider.mouse.click(hit.center.x, hit.center.y);
      const sent = await post;
      assert.equal(sent.status(), 201);
      const raw = sent.request().postData();
      assert.ok(!raw.includes(dummyCredential) && !raw.includes(providerName));
      const envelope = JSON.parse(raw);
      assert.deepEqual(Object.keys(envelope).sort(), ['c', 'e', 'i']);
      for (const value of Object.values(envelope)) assert.match(value, /^[\w-]+$/);
      await receiver.locator('#chatPanel').waitFor({state: 'visible'});
      assert.equal(await receiver.locator('#sessionInfo').textContent(), `${providerName} / fixture-model`);
      await receiver.locator('#msg').fill(prompt);
      await receiver.locator('#ask').click();
      await receiver.waitForFunction(() => document.querySelector('#chat').textContent.includes('dummy-upstream-reached'));
      const end = await events();
      assert.deepEqual(end.relay.slice(start.relay.length), [relayPath]);
      assert.deepEqual(end.chat.slice(start.chat.length), [{
        authorization_ok: true,
        body: {model: 'fixture-model', messages: [{role: 'user', content: prompt}], stream: false},
      }]);
    } else {
      await provider.mouse.click(hit.center.x, hit.center.y);
      await provider.locator('#modal').waitFor({state: 'hidden'});
      const poll = await receiver.waitForResponse(r => r.url() === request.r && r.request().method() === 'GET');
      assert.equal(poll.status(), 200);
      assert.deepEqual(await poll.json(), {});
      assert.equal(await receiver.locator('#chatPanel').isVisible(), false);
      assert.deepEqual(await events(), start, 'Declining must not POST authorization or trigger chat');
    }
    await provider.locator('#modal').waitFor({state: 'hidden'});
    assert.deepEqual(browserErrors, []);
    const vertical = ({y, bottom}) => `${Math.round(y)}–${Math.round(bottom)}`;
    console.log(`${name} ${viewport.width}×${viewport.height}: confirm y=${vertical(initial.confirm)}, `
      + `decline y=${vertical(initial.cancel)}; ${action === 'confirm' ? 'encrypted POST and mock chat passed' : 'zero POSTs on decline'}`);
  } finally {
    await Promise.all(contexts.map(context => context.close()));
  }
}

try {
  if (screenshotDir) await mkdir(screenshotDir, {recursive: true});
  for (const test of cases) await runCase(...test);
} finally {
  await browser.close();
}
