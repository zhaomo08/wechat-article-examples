import assert from 'node:assert/strict';

const url = 'https://todomvc.com/examples/react/dist/index.html';
const rendered = new URL('https://kitesurf.dev/html');
rendered.searchParams.set('url', url);

async function getHtml(address) {
  const response = await fetch(address, { signal: AbortSignal.timeout(20000) });
  assert.equal(response.status, 200, String(address));
  return response.text();
}

const [original, result] = await Promise.all([getHtml(url), getHtml(rendered)]);
const marker = 'placeholder="What needs to be done?"';
assert.match(original, /id="root"\s*>\s*<\/section>/);
assert.ok(!original.includes(marker));
assert.ok(result.includes(marker));
assert.match(result, /class="todo-count">0 items left!<\/span>/);

console.log('原始 HTML | root 容器为空，找不到待办输入框');
console.log('Kitesurf 渲染 HTML | 有待办输入框，剩余计数为 0');
