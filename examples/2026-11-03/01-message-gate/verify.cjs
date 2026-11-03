const http=require('http');const fs=require('fs');const path=require('path');const assert=require('node:assert/strict');
const {chromium}=require('playwright');
async function serve(){
 const server=http.createServer((req,res)=>{
  const name=new URL(req.url,'http://127.0.0.1').pathname;
  const file=name==='/'?'index.html':name==='/sender.html'?'sender.html':null;
  if(!file){res.writeHead(404);res.end();return;}
  res.writeHead(200,{'Content-Type':'text/html; charset=utf-8'});res.end(fs.readFileSync(path.join(__dirname,file)));
 });
 await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));return server;
}
(async()=>{
 const a=await serve(),b=await serve();let browser;
 try{
  const originA='http://127.0.0.1:'+a.address().port,originB='http://127.0.0.1:'+b.address().port;
  browser=await chromium.launch({channel:'chrome',headless:true});
  const page=await browser.newPage({viewport:{width:390,height:760},deviceScaleFactor:2});
  const requests=[];page.on('request',r=>requests.push(r.url()));
  await page.goto(originA+'/?cross='+encodeURIComponent(originB));
  await page.waitForFunction(()=>window.loadedSenders===3);
  for(const [index,id] of ['valid','origin','source','schema'].entries()){
   await page.locator('button[data-case="'+id+'"]').click();
   await page.waitForFunction(n=>window.report.length===n,index+1);
  }
  const result=await page.evaluate(()=>window.report);assert.deepEqual(result,['accepted','origin','source','schema']);
  assert(requests.every(u=>new URL(u).hostname==='127.0.0.1'));
  if(process.argv[2])await page.locator('main').screenshot({path:path.resolve(process.argv[2])});
  console.log('browser=Google Chrome');
  console.log('real_iframe_messages=4');
  console.log('accepted=1');console.log('rejected_origin=1');console.log('rejected_source=1');console.log('rejected_schema=1');
  console.log('external_requests=0');
 }finally{
  if(browser)await browser.close();
  await Promise.all([a,b].map(s=>new Promise(resolve=>s.close(resolve))));
 }
})().catch(e=>{console.error(e.message);process.exit(1)});
