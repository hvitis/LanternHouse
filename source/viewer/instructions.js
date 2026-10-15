const $=id=>document.getElementById(id);
export const STORAGE_KEY='moomin-house:assembly:v1';
let manifest,progress,scene,sceneLoading,model,initializing;
const fresh=()=>({schemaVersion:1,revision:manifest.revision,started:false,current:manifest.steps[0].id,completed:[],checklist:[]});
let storageMessage='';
function load(){
  try{
    const raw=localStorage.getItem(STORAGE_KEY);if(!raw)return fresh();
    const saved=JSON.parse(raw),stepIds=new Set(manifest.steps.map(s=>s.id)),supplyIds=new Set(manifest.supplies.map(s=>s.id));
    if(saved.schemaVersion!==1||!Array.isArray(saved.completed)||!Array.isArray(saved.checklist)||!stepIds.has(saved.current)){
      storageMessage='The saved build uses a different instruction format. Start a new build to replace it.';
      $('instructionReset').hidden=false;return fresh();
    }
    if(saved.revision!==manifest.revision){
      storageMessage='The instructions have changed. Your progress is kept. Review the updated steps before continuing.';
      // Keep the old revision until the builder explicitly accepts the update.
      $('instructionAccept').hidden=false;
    }
    return {...saved,started:saved.started===true,completed:saved.completed.filter(id=>stepIds.has(id)),checklist:saved.checklist.filter(id=>supplyIds.has(id))};
  }catch{
    storageMessage='Saved progress could not be read. Progress cannot be saved until you start a new build. You can still read the guide.';
    $('instructionReset').hidden=false;return fresh();
  }
}
function save(){
  // Do not overwrite an incompatible or unreadable save until Restart is confirmed.
  if(!$('instructionReset').hidden)return;
  try{localStorage.setItem(STORAGE_KEY,JSON.stringify(progress));}
  catch{storageMessage='Progress cannot be saved in this browser. Keep this page open to retain this session.';}
  $('instructionStorage').textContent=storageMessage;
}
function index(){return manifest.steps.findIndex(s=>s.id===progress.current);}
function text(tag,content,className){const el=document.createElement(tag);el.textContent=content;if(className)el.className=className;return el;}
function prepare(){
  const list=$('instructionChecklist');list.replaceChildren();
  const groups=[...new Set(manifest.supplies.map(s=>s.group))];
  for(const group of groups){
    const field=document.createElement('fieldset');field.append(text('legend',group));
    for(const item of manifest.supplies.filter(s=>s.group===group)){
      const label=document.createElement('label'),input=document.createElement('input');input.type='checkbox';input.checked=progress.checklist.includes(item.id);input.dataset.supply=item.id;
      const copy=document.createElement('span');copy.append(text('strong',`${item.description}${item.optional?' (optional)':''}`));
      copy.append(text('small',`Required: ${item.quantity}${item.purchase&&item.purchase!=='-'?` · Purchase allowance: ${item.purchase}`:''}${item.use?' · '+item.use:''}`));
      label.append(input,copy);field.append(label);
      input.addEventListener('change',()=>{progress.checklist=progress.checklist.filter(id=>id!==item.id);if(input.checked)progress.checklist.push(item.id);save();updatePreparation();});
    }
    list.append(field);
  }
  updatePreparation();
}
function updatePreparation(){
  const missing=manifest.supplies.filter(s=>!s.optional&&!progress.checklist.includes(s.id));
  $('instructionChecklistStatus').textContent=`${missing.length} preparation items unchecked. You can start and gather them later.`;
  $('instructionStart').textContent=progress.started?'Resume build':'Start building';
}
function playback(playing){$('instructionPlay').textContent=playing?'❚❚ Pause':'▶ Play step';$('instructionPlay').setAttribute('aria-pressed',String(playing));}
async function ensureScene(){
  if(scene)return scene;
  if(sceneLoading)return sceneLoading;
  sceneLoading=(async()=>{
    try{
      const response=await fetch('./data/parts.json');if(!response.ok)throw new Error('Model unavailable');model=await response.json();
      const {createInstructionScene}=await import('./instructions-scene.js');
      scene=createInstructionScene($('instructionView'),model,inspect,playback);
      scene.setStep(manifest.steps[index()]);scene.setActive(!$('instructionsPanel').hidden&&!$('instructionBuild').hidden);
      $('instructionSceneStatus').textContent='Yellow: current parts · muted: earlier assembly · orange: glue joints · blue: fasteners';
      $('instructionPlay').disabled=!(manifest.steps[index()].installs.length||manifest.steps[index()].motion);
      $('instructionReplay').disabled=$('instructionPlay').disabled;
      return scene;
    }catch{
      $('instructionSceneStatus').textContent='The 3D view could not load. You can continue with the written instructions and part lists.';
      $('instructionPlay').disabled=true;$('instructionReplay').disabled=true;return null;
    }
  })();
  return sceneLoading;
}
function inspect(value){
  const box=$('instructionInspect');box.replaceChildren();box.hidden=!value;
  if(value){box.append(text('strong',`${value.inst.part} · ${value.part.name}`),text('p',`${value.inst.id} · ${value.part.thickness} mm thick`),text('p',value.part.note||''));}
}
function renderStep(){
  const n=index(),step=manifest.steps[n],chapter=manifest.chapters.find(c=>c.id===step.chapter);
  $('instructionBuild').hidden=false;$('instructionPrep').hidden=true;
  $('instructionCount').textContent=`Step ${n+1} of ${manifest.steps.length}`;
  $('instructionChapterLabel').textContent=chapter.title;
  $('instructionStepTitle').textContent=step.title;
  $('instructionDescription').textContent=step.instruction;
  $('instructionReference').textContent=step.reference;
  $('instructionHint').textContent=step.hint;
  $('instructionCheck').textContent=step.check;
  $('instructionFieldHintsContent').replaceChildren(...(step.hints.length?step.hints.map(hint=>text('p',hint.text+(hint.author?' — '+hint.author:''))):[text('p','No field-tested hints for this step yet. This space is reserved for notes from builders.')]));
  $('instructionRepeat').hidden=step.repeat<2;$('instructionRepeat').textContent=`Repeat × ${step.repeat} · complete this batch together`;
  $('instructionOptional').hidden=!step.optional;
  $('instructionWarning').hidden=!step.warning;$('instructionWarning').textContent=step.warning;
  const list=$('instructionParts');list.replaceChildren();
  for(const [pid,count] of Object.entries(step.parts))list.append(text('li',`${pid} × ${count} · ${step.partInfo[pid].name} · ${step.partInfo[pid].thickness} mm`));
  if(!list.children.length)list.append(text('li','Use the assembly and supplies shown in this step. No new model parts.'));
  const required=$('instructionSupplies');required.replaceChildren();
  for(const id of step.supplies){
    const item=manifest.supplies.find(s=>s.id===id);
    required.append(text('li',`${progress.checklist.includes(id)?'✓ ':'Gather: '}${item.description} · ${item.quantity}`));
  }
  const joints=$('instructionJoints');joints.replaceChildren();
  const seen=new Set();
  for(const j of step.joints){const copy=j.type+': '+(j.glue||'Check the mating faces.');if(!seen.has(copy)){joints.append(text('li',copy));seen.add(copy);}}
  for(const f of step.fasteners){const copy=`${f.type} · ${f.diameter} × ${f.length} mm · ${f.note}`;if(!seen.has(copy)){joints.append(text('li',copy));seen.add(copy);}}
  if(!joints.children.length)joints.append(text('li','Use the detailed chapter notes for joint and alignment information.'));
  $('instructionPrevious').disabled=n===0;$('instructionNext').disabled=n===manifest.steps.length-1;
  $('instructionComplete').textContent=progress.completed.includes(step.id)?'✓ Completed — next':'Mark complete & next';
  $('instructionDone').hidden=progress.completed.length!==manifest.steps.length;
  $('instructionProgress').max=manifest.steps.length;$('instructionProgress').value=progress.completed.length;
  $('instructionProgressText').textContent=`${progress.completed.length} of ${manifest.steps.length} steps completed`;
  $('instructionStepSelect').value=step.id;
  for(const option of $('instructionStepSelect').options)option.textContent=(progress.completed.includes(option.value)?'✓ ':'')+option.dataset.label;
  $('instructionPlay').disabled=!scene||!(step.installs.length||step.motion);$('instructionReplay').disabled=$('instructionPlay').disabled;
  scene?.setStep(step);scene?.setActive(!$('instructionsPanel').hidden);
  ensureScene();
}
function go(id){progress.current=id;save();renderStep();}
function buildNavigation(){
  const select=$('instructionStepSelect');select.replaceChildren();
  for(const chapter of manifest.chapters){
    const group=document.createElement('optgroup');group.label=chapter.title;
    for(const [n,step] of manifest.steps.entries())if(step.chapter===chapter.id){const option=document.createElement('option');option.value=step.id;option.dataset.label=`${n+1}. ${step.title}`;option.textContent=option.dataset.label;group.append(option);}
    select.append(group);
  }
  select.addEventListener('change',()=>go(select.value));
}
async function init(){
  if(initializing)return initializing;
  initializing=(async()=>{
    try{
      const response=await fetch('./data/assembly.json');if(!response.ok)throw new Error('Instructions unavailable');manifest=await response.json();
      progress=load();$('instructionStorage').textContent=storageMessage;
      $('instructionIssues').replaceChildren(...manifest.issues.map(issue=>text('p',issue)));
      buildNavigation();prepare();$('instructionLoad').hidden=true;$('instructionPrep').hidden=false;
      $('instructionTotal').textContent=`${manifest.steps.length} steps · ${manifest.chapters.length} chapters`;
      $('instructionStart').addEventListener('click',()=>{progress.started=true;save();renderStep();});
      $('instructionPrevious').addEventListener('click',()=>go(manifest.steps[Math.max(0,index()-1)].id));
      $('instructionNext').addEventListener('click',()=>go(manifest.steps[Math.min(manifest.steps.length-1,index()+1)].id));
      $('instructionComplete').addEventListener('click',()=>{
        if(!progress.completed.includes(progress.current))progress.completed.push(progress.current);
        go(manifest.steps[Math.min(manifest.steps.length-1,index()+1)].id);
      });
      $('instructionPreparation').addEventListener('click',()=>{scene?.setActive(false);$('instructionBuild').hidden=true;$('instructionPrep').hidden=false;updatePreparation();});
      for(const id of ['instructionRestart','instructionReset'])$(id).addEventListener('click',()=>{
        if(!confirm('Restart this build? This clears the saved steps and preparation checklist.'))return;
        progress=fresh();storageMessage='';$('instructionReset').hidden=true;$('instructionAccept').hidden=true;save();prepare();scene?.setActive(false);$('instructionBuild').hidden=true;$('instructionPrep').hidden=false;
      });
      $('instructionAccept').addEventListener('click',()=>{progress.revision=manifest.revision;storageMessage='';$('instructionAccept').hidden=true;save();});
      $('instructionPlay').addEventListener('click',()=>scene?.playback());$('instructionReplay').addEventListener('click',()=>scene?.replay());
      $('instructionFit').addEventListener('click',()=>scene?.fit());$('instructionCloseup').addEventListener('click',()=>scene?.fit(true));
      // A reload returns a started build to its last viewed step.
      if(progress.started)renderStep();
    }catch{
      $('instructionLoad').textContent='The instructions could not load. Reload this page to try again.';$('instructionLoad').setAttribute('role','alert');
    }
  })();return initializing;
}
addEventListener('previewchange',event=>{
  const active=event.detail.preview==='instructions';
  if(active)init();scene?.setActive(active&&!$('instructionBuild').hidden);
});
if(location.hash==='#instructions')init();
