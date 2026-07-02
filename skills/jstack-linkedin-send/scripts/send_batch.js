// Batch InMail sender over Brave CDP. Processes up to N unsent leads from
// send_queue.json, one at a time: navigate -> open composer -> fill -> read free/credit
// badge -> Send -> verify -> persist. Human-paced jitter between sends. Halts on any
// restriction language or an unverified send (so an unknown credit-confirm modal stops
// us safely instead of failing silently). Progress is saved after EVERY send, so a
// timeout or halt is fully resumable.
const fs = require('fs');
const cp = require('child_process');
function findPW() {
  const hard = '/Users/thanadolsinthubodee/.npm/_npx/2fcde7aa8aa1538c/node_modules/playwright-core';
  if (fs.existsSync(hard)) return hard;
  try { return cp.execSync('find ~/.npm/_npx -maxdepth 4 -type d -name playwright-core 2>/dev/null | head -1', {shell: '/bin/zsh'}).toString().trim(); } catch (e) { return hard; }
}
const PW = findPW();
const { chromium } = require(PW);

const DIR = process.env.LINKEDIN_SEND_DIR || process.cwd();
const QUEUE = `${DIR}/send_queue.json`;
const LOG = `${DIR}/batch_log.jsonl`;
const RESULT = `${DIR}/batch_result.json`;
const SCRATCH = `${DIR}/cdp-shots`;
if (!fs.existsSync(SCRATCH)) fs.mkdirSync(SCRATCH, { recursive: true });

const N = parseInt(process.argv[2] || '20', 10);
const MIN_MS = 8000, MAX_MS = 18000;
const stamp = () => new Date().toISOString().replace('T', ' ').slice(0, 19);
const jitter = () => Math.floor(MIN_MS + Math.random() * (MAX_MS - MIN_MS));
const sleep = (ms) => new Promise(r => setTimeout(r, ms));
function logLine(obj) { fs.appendFileSync(LOG, JSON.stringify({ t: stamp(), ...obj }) + '\n'); }

(async () => {
  const browser = await chromium.connectOverCDP(process.env.CDP_URL || 'http://localhost:9222', { timeout: 8000 });
  const ctx = browser.contexts()[0];
  // Reuse one Sales Nav tab for the whole batch.
  let page = null;
  for (const p of ctx.pages()) if (p.url().includes('/sales/')) { page = p; break; }
  if (!page) page = await ctx.newPage();

  const summary = { batchStart: stamp(), requested: N, sent: [], skipped: [], halted: false, reason: null, creditsUsed: 0, freeSends: 0 };

  try {
    while (summary.sent.length + summary.skipped.length < N) {
      const Q = JSON.parse(fs.readFileSync(QUEUE, 'utf8'));
      const lead = Q.find(r => !r.sent);
      if (!lead) { summary.reason = 'queue-empty'; break; }

      // 1) navigate
      await page.goto(`https://www.linkedin.com/sales/people/${lead.leadId}`, { waitUntil: 'domcontentloaded', timeout: 45000 });
      // wait for the blue Message button
      const hasMsg = await page.waitForFunction(() => {
        return [...document.querySelectorAll('button')].some(b => /^Message$/i.test((b.innerText || '').trim()) && b.getBoundingClientRect().width > 0);
      }, { timeout: 15000 }).then(() => true).catch(() => false);
      if (!hasMsg) { summary.skipped.push({ row: lead.row, name: lead.name, why: 'no-message-button' }); logLine({ ev: 'skip', row: lead.row, why: 'no-message-button' }); lead.sent = `skip:no-msg-btn ${stamp()}`; fs.writeFileSync(QUEUE, JSON.stringify(Q, null, 2)); continue; }

      // 2) open composer
      await page.evaluate(() => { const b = [...document.querySelectorAll('button')].find(x => /^Message$/i.test((x.innerText || '').trim()) && x.getBoundingClientRect().width > 0); if (b) b.click(); });
      const composerOk = await page.waitForSelector('input[aria-label="Subject (required)"]', { timeout: 10000 }).then(() => true).catch(() => false);
      if (!composerOk) { summary.skipped.push({ row: lead.row, name: lead.name, why: 'composer-did-not-open' }); logLine({ ev: 'skip', row: lead.row, why: 'no-composer' }); lead.sent = `skip:no-composer ${stamp()}`; fs.writeFileSync(QUEUE, JSON.stringify(Q, null, 2)); continue; }

      // 3) read free/credit badge
      const badge = await page.evaluate(() => {
        const dlg = document.querySelector('[role=dialog]');
        if (!dlg) return null;
        const m = dlg.innerText.match(/Free to Open Profile/i);
        return m ? 'free' : 'credit';
      });

      // 4) fill
      await page.fill('input[aria-label="Subject (required)"]', lead.subject);
      await page.fill('textarea[name="message"]', lead.message);
      await sleep(600);

      // 5) pre-send sanity: Send enabled + values landed
      const ready = await page.evaluate(() => {
        const s = document.querySelector('input[aria-label="Subject (required)"]');
        const b = document.querySelector('textarea[name="message"]');
        const sendBtn = [...document.querySelectorAll('button')].find(x => /^Send$/i.test((x.innerText || '').trim()));
        return { subjOk: !!(s && s.value.trim()), bodyLen: b ? b.value.length : 0, sendEnabled: sendBtn ? !sendBtn.disabled : false };
      });
      if (!ready.subjOk || ready.bodyLen < 50 || !ready.sendEnabled) {
        summary.halted = true; summary.reason = `fill-failed row ${lead.row}: ${JSON.stringify(ready)}`;
        await page.screenshot({ path: `${SCRATCH}/halt_fill_${lead.row}.png` }).catch(() => {});
        logLine({ ev: 'halt', row: lead.row, why: 'fill-failed', ready }); break;
      }

      // 6) send
      await page.evaluate(() => { const b = [...document.querySelectorAll('button')].find(x => /^Send$/i.test((x.innerText || '').trim()) && !x.disabled); if (b) b.click(); });
      await sleep(4500);

      // 7) verify + restriction scan
      const post = await page.evaluate((subj) => {
        const s = document.querySelector('input[aria-label="Subject (required)"]');
        const subjCleared = s ? (s.value.trim() === '') : true; // composer reset to a fresh empty one == sent
        const body = document.body.innerText;
        const sentSignal = /Awaiting reply|Message sent|You\s*·/i.test(body);
        const restriction = (body.match(/(weekly limit|reached your|you can'?t send|restricted|try again later|unusual activity|please verify|no longer send|out of inmail|0 InMail)/i) || [])[0] || null;
        return { subjCleared, sentSignal, restriction };
      }, lead.subject);

      if (post.restriction) {
        summary.halted = true; summary.reason = `RESTRICTION row ${lead.row}: "${post.restriction}"`;
        await page.screenshot({ path: `${SCRATCH}/halt_restriction_${lead.row}.png` }).catch(() => {});
        logLine({ ev: 'halt', row: lead.row, why: 'restriction', text: post.restriction }); break;
      }
      const ok = post.sentSignal || post.subjCleared;
      if (!ok) {
        summary.halted = true; summary.reason = `send-not-verified row ${lead.row} (possible unknown credit-confirm modal)`;
        await page.screenshot({ path: `${SCRATCH}/halt_unverified_${lead.row}.png` }).catch(() => {});
        logLine({ ev: 'halt', row: lead.row, why: 'send-not-verified', post }); break;
      }

      // 8) record success
      lead.sent = `${stamp()} sent (${badge === 'free' ? 'free/OpenProfile' : 'credit'})`;
      fs.writeFileSync(QUEUE, JSON.stringify(Q, null, 2));
      if (badge === 'free') summary.freeSends++; else summary.creditsUsed++;
      summary.sent.push({ row: lead.row, name: lead.name, badge, variant: lead.variant });
      logLine({ ev: 'sent', row: lead.row, name: lead.name, badge });

      // 9) human-paced jitter (skip after the last in the batch)
      if (summary.sent.length + summary.skipped.length < N) await sleep(jitter());
    }
  } catch (e) {
    summary.halted = true; summary.reason = 'exception: ' + String(e);
    logLine({ ev: 'error', err: String(e) });
  } finally {
    summary.batchEnd = stamp();
    fs.writeFileSync(RESULT, JSON.stringify(summary, null, 2));
    await browser.close();
  }
  console.log(JSON.stringify(summary, null, 2));
})();
