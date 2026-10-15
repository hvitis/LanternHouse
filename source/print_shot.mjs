// Screenshots of the running print studio (or any copy of prints.html), to check a change by eye without
// switching to the browser. Claude uses this to look at its own edits.
//
//   node source/print_shot.mjs chair                      # 3/4, front, side and underside views
//   node source/print_shot.mjs chair --views iso,top --url http://127.0.0.1:8766/
//
// The studio's address comes from output/prints/studio-url.txt, which print_studio.py writes when it starts.
//
// Writes output/prints/shots/<design>-<view>.png and prints their paths.
import {mkdir, readFile} from 'node:fs/promises';
import {fileURLToPath} from 'node:url';
import {chromium} from 'playwright';

const args=process.argv.slice(2),option=(name,fallback)=>{const i=args.indexOf(`--${name}`);return i<0?fallback:args.splice(i,2)[1];};
const running=await readFile(new URL('../output/prints/studio-url.txt',import.meta.url),'utf8').catch(()=>'');
const url=option('url',running.trim()),views=option('views','iso,front,side,under').split(','),size=option('size','1280x860').split('x').map(Number);
const name=args[0];
if(!name){console.error('Usage: node source/print_shot.mjs <design> [--views iso,front,side,back,top,under] [--url …] [--size 1280x860]');process.exit(2);}
if(!url){console.error('No print studio is running: start it with `make studio`, or pass --url.');process.exit(2);}
const out=fileURLToPath(new URL('../output/prints/shots/',import.meta.url));
await mkdir(out,{recursive:true});
const browser=await chromium.launch({args:['--enable-unsafe-swiftshader']});
try{
  const page=await browser.newPage({viewport:{width:size[0],height:size[1]}});
  const errors=[];page.on('pageerror',e=>errors.push(e.message));
  for(const view of views){
    const target=new URL(url);target.searchParams.set('view',view);target.hash=name;
    await page.goto(target.href);
    await page.locator(`#view[data-ready="true"][data-part="${name}"]`).waitFor({timeout:30_000});
    await page.waitForTimeout(400);   // let the orbit damping settle
    const file=`${out}${name}-${view}.png`;await page.screenshot({path:file});console.log(file);
  }
  if(errors.length){console.error('Page errors:\n'+errors.join('\n'));process.exitCode=1;}
}finally{await browser.close();}
