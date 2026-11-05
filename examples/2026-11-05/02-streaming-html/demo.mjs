// 人工延迟下的本机HTML流式传输。Node内置模块，无第三方依赖。
import http from 'node:http';
import assert from 'node:assert/strict';
import { performance } from 'node:perf_hooks';
import { writeFile } from 'node:fs/promises';

const delayMs = 800;
const head = `<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>本机HTML加载实验</title><style>body{font-family:system-ui,sans-serif;margin:0;padding:28px 24px;background:#f6f3eb;color:#233b3a}h1{font-size:26px;line-height:1.4}p{font-size:18px;line-height:1.8}section{background:white;border:1px solid #c8d1c9;border-radius:12px;padding:20px;margin:18px 0}small{font-size:13px;color:#647570}</style><body><small>本机教学页面 · 人工延迟800ms</small><h1>这张资料卡先到了</h1><section id="profile"><p>账户：演示用户</p><p>身份：前端开发者</p></section><p>明细还在准备，资料卡可以先看。</p><!--${'.'.repeat(2048)}-->`;
const detail = '<section id="detail"><p>明细也到了</p><p>这部分故意晚800ms发送。</p></section>';
const tail = '</body></html>';

const server = http.createServer(async (req, res) => {
  if (!['/buffered', '/stream'].includes(req.url)) {
    res.writeHead(404).end('Not found');
    return;
  }
  res.writeHead(200, {'Content-Type':'text/html; charset=utf-8', 'Cache-Control':'no-store'});
  // 两条路径的最终HTML相同，只改变准备好的内容何时交给客户端。
  if (req.url === '/stream') res.write(head);
  await new Promise(resolve => setTimeout(resolve, delayMs));
  if (req.url === '/buffered') res.end(head + detail + tail);
  else res.end(detail + tail);
});

function measure(path, port) {
  return new Promise((resolve, reject) => {
    const start = performance.now();
    const request = http.get({hostname:'127.0.0.1', port, path, agent:false}, response => {
      let firstAt = null, first = '', body = '';
      response.setEncoding('utf8');
      response.on('data', chunk => {
        if (firstAt === null) {firstAt = performance.now() - start; first = chunk;}
        body += chunk;
      });
      response.on('error', reject);
      response.on('end', () => resolve({first_chunk_ms:firstAt, total_ms:performance.now()-start, first, body}));
    });
    request.on('error', reject);
    request.setTimeout(5000, () => request.destroy(new Error('Local demo timeout')));
  });
}

await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
const port = server.address().port;
if (process.argv.includes('--serve')) {
  console.log(`http://127.0.0.1:${port}/stream`);
  console.log(`http://127.0.0.1:${port}/buffered`);
  process.on('SIGINT', () => {server.closeAllConnections(); server.close();});
} else {
  try {
    const buffered = await measure('/buffered', port);
    const stream = await measure('/stream', port);
    const checks = {
      buffered_first_chunk_after_delay:buffered.first_chunk_ms >= delayMs*0.8,
      stream_first_chunk_before_details:stream.first_chunk_ms < stream.total_ms-delayMs*0.5,
      stream_first_chunk_has_profile:stream.first.includes('id="profile"'),
      stream_first_chunk_has_detail:stream.first.includes('id="detail"'),
      final_html_equal:buffered.body === stream.body
    };
    assert.equal(checks.buffered_first_chunk_after_delay, true);
    assert.equal(checks.stream_first_chunk_before_details, true);
    assert.equal(checks.stream_first_chunk_has_profile, true);
    assert.equal(checks.stream_first_chunk_has_detail, false);
    assert.equal(checks.final_html_equal, true);
    for (const [key, value] of Object.entries(checks)) console.log(`${key}=${value}`);
    console.log(`delay_ms=${delayMs}`);
    console.log('http_scope=127.0.0.1');
    console.log('external_requests=0');
    const option = process.argv.indexOf('--output');
    if (option >= 0) {
      if (!process.argv[option+1]) throw new Error('--output需要文件名');
      await writeFile(process.argv[option+1], JSON.stringify({delay_ms:delayMs,checks,buffered:{first_chunk_ms:buffered.first_chunk_ms,total_ms:buffered.total_ms},stream:{first_chunk_ms:stream.first_chunk_ms,total_ms:stream.total_ms},scope:'local HTTP bytes; not browser performance or X benchmark'},null,2)+'\n',{flag:'wx'});
    }
  } finally {await new Promise(resolve => server.close(resolve));}
}
