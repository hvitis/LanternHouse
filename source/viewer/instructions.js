const $=id=>document.getElementById(id);
export const STORAGE_KEY='lanternwood-house:assembly:v1';
export const LANG_STORAGE_KEY='lanternwood-house:instructions:lang';

let manifest,progress,scene,sceneLoading,model,initializing;
function getStoredLang(){try{return localStorage.getItem(LANG_STORAGE_KEY)||'pl';}catch{return 'pl';}}
let currentLang=getStoredLang();
const fresh=()=>({schemaVersion:1,revision:manifest.revision,started:false,current:manifest.steps[0].id,completed:[],checklist:[]});
let storageMessage='';

const I18N = {
  pl: {
    langButton: 'EN',
    langAria: 'Switch to English',
    eyebrow: 'OD WIZUALIZACJI DO PROJEKTU',
    mainTitle: 'Przewodnik budowy domku.',
    totalBadge: (steps, chapters) => `${steps} kroków · ${chapters} rozdziałów`,
    load: 'Wczytywanie instrukcji budowy…',
    loadError: 'Nie można wczytać instrukcji budowy. Odśwież stronę, aby spróbować ponownie.',
    sceneStatus: 'Żółty: bieżące części · stonowany: wcześniejszy montaż · pomarańczowy: połączenia klejone · niebieski: łączniki',
    sceneError: 'Nie można załadować widoku 3D. Możesz kontynuować z instrukcją tekstową i listą części.',
    keysHint: 'Klawisze: <kbd>Spacja</kbd> odtwórz · <kbd>←</kbd>/<kbd>→</kbd> krok · <kbd>Enter</kbd> ukończ · <kbd>X</kbd> izoluj · <kbd>Z</kbd> zbliżenie',
    storageIncompatible: 'Zapisany postęp używa innego formatu. Rozpocznij nową budowę, aby go zastąpić.',
    storageChanged: 'Instrukcja została zaktualizowana. Twój postęp został zachowany. Przejrzyj zmiany przed kontynuacją.',
    storageCorrupt: 'Nie udało się odczytać zapisanego postępu. Rozpocznij nową budowę. Wciąż możesz przeglądać instrukcję.',
    storageUnavailable: 'Nie można zapisać postępu w tej przeglądarce. Pozostaw tę stronę otwartą, aby zachować sesję.',
    acceptUpdate: 'Zachowaj postęp i zaakceptuj zaktualizowaną instrukcję',
    resetBuild: 'Rozpocznij nową budowę',
    prepTitle: 'Zanim zaczniesz',
    prepP1: 'Sprawdź zestaw sklejki według oznaczeń części. Przygotuj materiały i narzędzia z poniższej listy. Ilości wynikają z tego modelu.',
    prepP2: 'Korzystaj z szablonów 1:1 do cięcia i wiercenia. Widok 3D pokazuje rozmieszczenie i orientację elementów.',
    prepP3: 'Lista kontrolna i postęp budowy są zapisywane w tej przeglądarce. Możesz czytać kolejne kroki bez oznaczania ich jako ukończone.',
    startBuild: 'Rozpocznij budowę',
    resumeBuild: 'Wznów budowę',
    downloadPdf: '📄 Pobierz listę PDF (A4)',
    checklistStatus: missing => `${missing} pozycji przygotowania nieodhaczonych. Możesz rozpocząć i skompletować je później.`,
    play: '▶ Odtwórz krok',
    pause: '❚❚ Wstrzymaj',
    replay: 'Powtórz',
    scrubTitle: 'Przewiń animację montażu',
    fit: 'Resetuj widok',
    closeup: 'Zbliżenie połączenia',
    isolate: 'Izoluj',
    fullContext: 'Pełny kontekst',
    angleStep: 'Kąt',
    angleFront: 'Przód',
    angleTop: 'Góra',
    stepCount: (n, total) => `Krok ${n} z ${total}`,
    selectLabel: 'Przeglądaj rozdziały i kroki',
    progressText: (done, total) => `${done} z ${total} kroków ukończono`,
    optionalBadge: 'Opcjonalny · oznacz jako ukończony, aby pominąć',
    repeatText: r => `Powtórz × ${r} · wykonaj tę serię razem`,
    partsHeading: 'Elementy do tej operacji',
    noParts: 'Użyj elementów zmontowanych wcześniej i materiałów podanych w tym kroku. Brak nowych części modelu.',
    suppliesSummary: 'Materiały i narzędzia',
    gather: 'Przygotuj: ',
    purchased: '✓ ',
    jointsSummary: 'Szczegóły połączeń i łączników',
    noJoints: 'Skorzystaj ze szczegółowych uwag do rozdziału, aby sprawdzić spasowanie i wyrównanie połączeń.',
    chapterSummary: 'Szczegółowe instrukcje rozdziału',
    checkHeading: 'Przed kolejnym krokiem',
    checkNotice: 'Złóż na sucho przed klejeniem. Odczekaj do związania kleju przed obciążeniem połączenia. Przestrzegaj czasu schnięcia podanego przez producenta.',
    doneText: 'Wszystkie kroki zostały ukończone. Sprawdź ruchome części i zamocuj zabezpieczenie przed przewróceniem.',
    previous: '← Poprzedni',
    next: 'Następny →',
    completeNext: 'Oznacz jako ukończony i dalej',
    completedNext: '✓ Ukończono — dalej',
    prepButton: 'Lista przygotowawcza',
    restartButton: 'Rozpocznij od nowa',
    hintsTitle: 'WSKAZÓWKI <small>Z prawdziwych budów</small>',
    noHints: 'Brak sprawdzonych w praktyce wskazówek dla tego kroku. To miejsce na uwagi konstruktorów.',
    restartConfirm: 'Rozpocząć tę budowę od nowa? Spowoduje to wyczyszczenie zapisanych kroków i listy przygotowawczej.',
    dxfFind: (pid, layer) => `Znajdź ${pid} w DXF (${layer})`,
    requiredText: (qty, purchase, use) => `Wymagane: ${qty}${purchase && purchase !== '-' ? ` · Zapas zakupu: ${purchase}` : ''}${use ? ' · ' + use : ''}`,
    optionalSupply: ' (opcjonalnie)',
  },
  en: {
    langButton: 'PL',
    langAria: 'Przełącz na język polski',
    eyebrow: 'FROM PREVIEW TO PROJECT',
    mainTitle: 'A companion for your build.',
    totalBadge: (steps, chapters) => `${steps} steps · ${chapters} chapters`,
    load: 'Loading the build instructions…',
    loadError: 'The instructions could not load. Reload this page to try again.',
    sceneStatus: 'Yellow: current parts · muted: earlier assembly · orange: glue joints · blue: fasteners',
    sceneError: 'The 3D view could not load. You can continue with the written instructions and part lists.',
    keysHint: 'Keys: <kbd>Space</kbd> play · <kbd>←</kbd>/<kbd>→</kbd> step · <kbd>Enter</kbd> complete · <kbd>X</kbd> isolate · <kbd>Z</kbd> close-up',
    storageIncompatible: 'The saved build uses a different instruction format. Start a new build to replace it.',
    storageChanged: 'The instructions have changed. Your progress is kept. Review the updated steps before continuing.',
    storageCorrupt: 'Saved progress could not be read. Progress cannot be saved until you start a new build. You can still read the guide.',
    storageUnavailable: 'Progress cannot be saved in this browser. Keep this page open to retain this session.',
    acceptUpdate: 'Keep progress and accept updated instructions',
    resetBuild: 'Start a new build',
    prepTitle: 'Before you start',
    prepP1: 'Check the plywood kit against its part IDs. Gather the supplies below. Quantities come from this model.',
    prepP2: 'Use the full-size templates for cutting and drilling. The 3D view shows placement and orientation.',
    prepP3: 'Your checklist and build progress stay in this browser. You can read ahead without marking steps complete.',
    startBuild: 'Start building',
    resumeBuild: 'Resume build',
    downloadPdf: '📄 Download Checklist PDF (A4)',
    checklistStatus: missing => `${missing} preparation items unchecked. You can start and gather them later.`,
    play: '▶ Play step',
    pause: '❚❚ Pause',
    replay: 'Replay',
    scrubTitle: 'Scrub assembly movement',
    fit: 'Reset view',
    closeup: 'Joint close-up',
    isolate: 'Isolate',
    fullContext: 'Full context',
    angleStep: 'Angle',
    angleFront: 'Front',
    angleTop: 'Top',
    stepCount: (n, total) => `Step ${n} of ${total}`,
    selectLabel: 'Browse chapters and steps',
    progressText: (done, total) => `${done} of ${total} steps completed`,
    optionalBadge: 'Optional · mark complete to skip',
    repeatText: r => `Repeat × ${r} · complete this batch together`,
    partsHeading: 'Parts for this operation',
    noParts: 'Use the assembly and supplies shown in this step. No new model parts.',
    suppliesSummary: 'Supplies and tools',
    gather: 'Gather: ',
    purchased: '✓ ',
    jointsSummary: 'Joint and fastener details',
    noJoints: 'Use the detailed chapter notes for joint and alignment information.',
    chapterSummary: 'Detailed chapter instructions',
    checkHeading: 'Before you continue',
    checkNotice: 'Dry-fit before gluing. Let each joint cure before loading it. Use the adhesive maker’s curing time.',
    doneText: 'All steps are marked complete. Check the moving parts and anchor before use.',
    previous: '← Previous',
    next: 'Next →',
    completeNext: 'Mark complete & next',
    completedNext: '✓ Completed — next',
    prepButton: 'Preparation checklist',
    restartButton: 'Restart build',
    hintsTitle: 'HINTS <small>From real builds</small>',
    noHints: 'No field-tested hints for this step yet. This space is reserved for notes from builders.',
    restartConfirm: 'Restart this build? This clears the saved steps and preparation checklist.',
    dxfFind: (pid, layer) => `Find ${pid} in DXF (${layer})`,
    requiredText: (qty, purchase, use) => `Required: ${qty}${purchase && purchase !== '-' ? ` · Purchase allowance: ${purchase}` : ''}${use ? ' · ' + use : ''}`,
    optionalSupply: ' (optional)',
  }
};

const t=()=>I18N[currentLang]||I18N.pl;

function load(){
  try{
    const raw=localStorage.getItem(STORAGE_KEY);if(!raw)return fresh();
    const saved=JSON.parse(raw),stepIds=new Set(manifest.steps.map(s=>s.id)),supplyIds=new Set(manifest.supplies.map(s=>s.id));
    if(saved.schemaVersion!==1||!Array.isArray(saved.completed)||!Array.isArray(saved.checklist)||!stepIds.has(saved.current)){
      storageMessage=t().storageIncompatible;
      $('instructionReset').hidden=false;return fresh();
    }
    if(saved.revision!==manifest.revision){
      storageMessage=t().storageChanged;
      $('instructionAccept').hidden=false;
    }
    return {...saved,started:saved.started===true,completed:saved.completed.filter(id=>stepIds.has(id)),checklist:saved.checklist.filter(id=>supplyIds.has(id))};
  }catch{
    storageMessage=t().storageCorrupt;
    $('instructionReset').hidden=false;return fresh();
  }
}

function save(){
  if(!$('instructionReset').hidden)return;
  try{localStorage.setItem(STORAGE_KEY,JSON.stringify(progress));}
  catch{storageMessage=t().storageUnavailable;}
  $('instructionStorage').textContent=storageMessage;
}

function index(){return manifest.steps.findIndex(s=>s.id===progress.current);}
function text(tag,content,className){const el=document.createElement(tag);el.textContent=content;if(className)el.className=className;return el;}

function updateLanguageUI(){
  const dict=t(),isPl=currentLang==='pl';
  const btn=$('instructionLang');
  if(btn){
    btn.textContent=dict.langButton;
    btn.setAttribute('aria-label',dict.langAria);
    btn.title=dict.langAria;
  }
  if($('instructionEyebrow'))$('instructionEyebrow').textContent=dict.eyebrow;
  if($('instructionMainTitle'))$('instructionMainTitle').textContent=dict.mainTitle;
  if($('instructionTotal'))$('instructionTotal').textContent=dict.totalBadge(manifest.steps.length,manifest.chapters.length);
  if($('instructionAccept'))$('instructionAccept').textContent=dict.acceptUpdate;
  if($('instructionReset'))$('instructionReset').textContent=dict.resetBuild;
  if($('instructionPrepTitle'))$('instructionPrepTitle').textContent=dict.prepTitle;
  if($('instructionPrepP1'))$('instructionPrepP1').textContent=dict.prepP1;
  if($('instructionPrepP2'))$('instructionPrepP2').textContent=dict.prepP2;
  if($('instructionPrepP3'))$('instructionPrepP3').textContent=dict.prepP3;
  const pdfBtn=$('instructionDownloadPdf');
  if(pdfBtn){
    pdfBtn.textContent=dict.downloadPdf;
    pdfBtn.href=isPl?'./data/checklist-pl.pdf':'./data/checklist-en.pdf';
    pdfBtn.setAttribute('download',isPl?'Lanternwood-House-Checklist-PL.pdf':'Lanternwood-House-Checklist.pdf');
  }
  if($('instructionIssues'))$('instructionIssues').replaceChildren(...(isPl&&manifest.issues_pl?manifest.issues_pl:manifest.issues).map(issue=>text('p',issue)));
  if($('instructionFit'))$('instructionFit').textContent=dict.fit;
  if($('instructionCloseup'))$('instructionCloseup').textContent=dict.closeup;
  if($('instructionReplay'))$('instructionReplay').textContent=dict.replay;
  if($('instructionAngleStep'))$('instructionAngleStep').textContent=dict.angleStep;
  if($('instructionAngleFront'))$('instructionAngleFront').textContent=dict.angleFront;
  if($('instructionAngleTop'))$('instructionAngleTop').textContent=dict.angleTop;
  if($('instructionKeysHint'))$('instructionKeysHint').innerHTML=dict.keysHint;
  if($('instructionStepSelectLabel'))$('instructionStepSelectLabel').textContent=dict.selectLabel;
  if($('instructionPartsHeading'))$('instructionPartsHeading').textContent=dict.partsHeading;
  if($('instructionSuppliesSummary'))$('instructionSuppliesSummary').textContent=dict.suppliesSummary;
  if($('instructionJointsSummary'))$('instructionJointsSummary').textContent=dict.jointsSummary;
  if($('instructionChapterSummary'))$('instructionChapterSummary').textContent=dict.chapterSummary;
  if($('instructionCheckHeading'))$('instructionCheckHeading').textContent=dict.checkHeading;
  if($('instructionCheckNotice'))$('instructionCheckNotice').textContent=dict.checkNotice;
  if($('instructionPrevious'))$('instructionPrevious').textContent=dict.previous;
  if($('instructionNext'))$('instructionNext').textContent=dict.next;
  if($('instructionPreparation'))$('instructionPreparation').textContent=dict.prepButton;
  if($('instructionRestart'))$('instructionRestart').textContent=dict.restartButton;
  if($('instructionFieldHintsTitle'))$('instructionFieldHintsTitle').innerHTML=dict.hintsTitle;

  buildNavigation();
  prepare();
  if(!$('instructionBuild').hidden)renderStep();
}

function setLanguage(lang){
  currentLang=lang==='en'?'en':'pl';
  try{localStorage.setItem(LANG_STORAGE_KEY,currentLang);}catch{}
  updateLanguageUI();
}

function prepare(){
  const isPl=currentLang==='pl',dict=t();
  const list=$('instructionChecklist');list.replaceChildren();
  const groups=[...new Set(manifest.supplies.map(s=>isPl?(s.group_pl||s.group):s.group))];
  for(const group of groups){
    const field=document.createElement('fieldset');field.append(text('legend',group));
    const items=manifest.supplies.filter(s=>(isPl?(s.group_pl||s.group):s.group)===group);
    for(const item of items){
      const label=document.createElement('label'),input=document.createElement('input');input.type='checkbox';input.checked=progress.checklist.includes(item.id);input.dataset.supply=item.id;
      const desc=isPl?(item.description_pl||item.description):item.description;
      const qty=isPl?(item.quantity_pl||item.quantity):item.quantity;
      const purchase=isPl?(item.purchase_pl||item.purchase):item.purchase;
      const use=isPl?(item.use_pl||item.use):item.use;
      const copy=document.createElement('span');
      copy.append(text('strong',`${desc}${item.optional?dict.optionalSupply:''}`));
      copy.append(text('small',dict.requiredText(qty,purchase,use)));
      label.append(input,copy);field.append(label);
      input.addEventListener('change',()=>{progress.checklist=progress.checklist.filter(id=>id!==item.id);if(input.checked)progress.checklist.push(item.id);save();updatePreparation();});
    }
    list.append(field);
  }
  updatePreparation();
}

function updatePreparation(){
  const missing=manifest.supplies.filter(s=>!s.optional&&!progress.checklist.includes(s.id));
  const dict=t();
  $('instructionChecklistStatus').textContent=dict.checklistStatus(missing.length);
  $('instructionStart').textContent=progress.started?dict.resumeBuild:dict.startBuild;
}

function playback(playing){
  const dict=t();
  $('instructionPlay').textContent=playing?dict.pause:dict.play;
  $('instructionPlay').setAttribute('aria-pressed',String(playing));
}

function updateScrub(val){const scrub=$('instructionScrub');if(scrub)scrub.value=Math.round(val*100);}

async function ensureScene(){
  if(scene)return scene;
  if(sceneLoading)return sceneLoading;
  sceneLoading=(async()=>{
    try{
      const response=await fetch('./data/parts.json');if(!response.ok)throw new Error('Model unavailable');model=await response.json();
      const {createInstructionScene}=await import('./instructions-scene.js');
      scene=createInstructionScene($('instructionView'),model,inspect,playback,updateScrub);
      scene.setStep(manifest.steps[index()]);scene.setActive(!$('instructionsPanel').hidden&&!$('instructionBuild').hidden);
      $('instructionSceneStatus').textContent=t().sceneStatus;
      const canAnimate=Boolean(manifest.steps[index()].installs.length||manifest.steps[index()].motion);
      $('instructionPlay').disabled=!canAnimate;$('instructionReplay').disabled=!canAnimate;$('instructionScrub').disabled=!canAnimate;
      return scene;
    }catch{
      $('instructionSceneStatus').textContent=t().sceneError;
      $('instructionPlay').disabled=true;$('instructionReplay').disabled=true;$('instructionScrub').disabled=true;return null;
    }
  })();
  return sceneLoading;
}

function inspect(value){
  const box=$('instructionInspect'),isPl=currentLang==='pl';box.replaceChildren();box.hidden=!value;
  for(const li of $('instructionParts').children)li.classList.remove('highlighted-part');
  if(value){
    const pName=isPl?(value.part.name_pl||value.part.name):value.part.name;
    box.append(text('strong',`${value.inst.part} · ${pName}`),text('p',`${value.inst.id} · ${value.part.thickness} mm`),text('p',value.part.note||''));
    const matching=$('instructionParts').querySelector(`[data-part-id="${value.inst.part}"]`);
    if(matching){matching.classList.add('highlighted-part');matching.scrollIntoView({behavior:'smooth',block:'nearest'});}
  }
}

function jumpToDxf(){
  const tab=$('tab-dxf');
  if(tab){
    tab.click();
    const box=$('dxfPieceIds');
    if(box&&!box.checked){box.checked=true;box.dispatchEvent(new Event('change'));}
  }
}

function renderStep(){
  const n=index(),step=manifest.steps[n],chapter=manifest.chapters.find(c=>c.id===step.chapter);
  const isPl=currentLang==='pl',dict=t();
  $('instructionBuild').hidden=false;$('instructionPrep').hidden=true;
  $('instructionCount').textContent=dict.stepCount(n+1,manifest.steps.length);
  $('instructionChapterLabel').textContent=isPl?(chapter.title_pl||chapter.title):chapter.title;
  $('instructionStepTitle').textContent=isPl?(step.title_pl||step.title):step.title;
  $('instructionDescription').textContent=isPl?(step.instruction_pl||step.instruction):step.instruction;
  $('instructionReference').textContent=isPl?(step.reference_pl||step.reference):step.reference;
  $('instructionHint').textContent=isPl?(step.hint_pl||step.hint):step.hint;
  $('instructionCheck').textContent=isPl?(step.check_pl||step.check):step.check;

  const hints=step.hints||[];
  $('instructionFieldHintsContent').replaceChildren(...(hints.length?hints.map(hint=>{
    const hText=isPl?(hint.text_pl||hint.text):hint.text;
    return text('p',hText+(hint.author?' — '+hint.author:''));
  }):[text('p',dict.noHints)]));

  $('instructionRepeat').hidden=step.repeat<2;$('instructionRepeat').textContent=dict.repeatText(step.repeat);
  $('instructionOptional').hidden=!step.optional;
  const warnText=isPl?(step.warning_pl||step.warning):step.warning;
  $('instructionWarning').hidden=!warnText;$('instructionWarning').textContent=warnText;

  const list=$('instructionParts');list.replaceChildren();
  for(const [pid,count] of Object.entries(step.parts)){
    const info=step.partInfo[pid];
    const li=document.createElement('li');li.className='instruction-part-item';li.dataset.partId=pid;
    const pName=isPl?(info.name_pl||info.name):info.name;
    const desc=text('span',`${pid} × ${count} · ${pName} · ${info.thickness} mm`);li.append(desc);
    if(info.layer){
      const btn=document.createElement('button');btn.type='button';btn.className='dxf-jump-btn';btn.textContent='DXF ↗';btn.title=dict.dxfFind(pid,info.layer);
      btn.addEventListener('click',e=>{e.stopPropagation();jumpToDxf();});li.append(btn);
    }
    li.addEventListener('mouseenter',()=>scene?.highlightPart(pid));
    li.addEventListener('mouseleave',()=>scene?.highlightPart(null));
    li.addEventListener('click',()=>{scene?.highlightPart(pid);scene?.fit(true);});
    list.append(li);
  }
  if(!list.children.length)list.append(text('li',dict.noParts));

  const required=$('instructionSupplies');required.replaceChildren();
  for(const id of step.supplies){
    const item=manifest.supplies.find(s=>s.id===id);
    const itemDesc=isPl?(item.description_pl||item.description):item.description;
    const itemQty=isPl?(item.quantity_pl||item.quantity):item.quantity;
    required.append(text('li',`${progress.checklist.includes(id)?dict.purchased:dict.gather}${itemDesc} · ${itemQty}`));
  }

  const joints=$('instructionJoints');joints.replaceChildren();
  const seen=new Set();
  for(const j of step.joints){
    const copy=j.type+': '+(j.glue||(isPl?'Sprawdź powierzchnie styku.':'Check the mating faces.'));
    if(!seen.has(copy)){joints.append(text('li',copy));seen.add(copy);}
  }
  for(const f of step.fasteners){
    const copy=`${f.type} · ${f.diameter} × ${f.length} mm · ${f.note}`;
    if(!seen.has(copy)){joints.append(text('li',copy));seen.add(copy);}
  }
  if(!joints.children.length)joints.append(text('li',dict.noJoints));

  $('instructionPrevious').disabled=n===0;$('instructionNext').disabled=n===manifest.steps.length-1;
  $('instructionComplete').textContent=progress.completed.includes(step.id)?dict.completedNext:dict.completeNext;
  $('instructionDone').hidden=progress.completed.length!==manifest.steps.length;
  $('instructionProgress').max=manifest.steps.length;$('instructionProgress').value=progress.completed.length;
  $('instructionProgressText').textContent=dict.progressText(progress.completed.length,manifest.steps.length);
  $('instructionStepSelect').value=step.id;
  for(const option of $('instructionStepSelect').options)option.textContent=(progress.completed.includes(option.value)?'✓ ':'')+option.dataset.label;

  const canAnimate=Boolean(step.installs.length||step.motion);
  $('instructionPlay').disabled=!scene||!canAnimate;$('instructionReplay').disabled=$('instructionPlay').disabled;
  $('instructionScrub').disabled=!scene||!canAnimate;$('instructionScrub').value=100;
  playback(false);
  scene?.setStep(step);scene?.setActive(!$('instructionsPanel').hidden);
  ensureScene();
}

function go(id){progress.current=id;save();renderStep();}

function buildNavigation(){
  const isPl=currentLang==='pl';
  const select=$('instructionStepSelect');select.replaceChildren();
  for(const chapter of manifest.chapters){
    const group=document.createElement('optgroup');
    group.label=isPl?(chapter.title_pl||chapter.title):chapter.title;
    for(const [n,step] of manifest.steps.entries())if(step.chapter===chapter.id){
      const option=document.createElement('option');
      option.value=step.id;
      const sTitle=isPl?(step.title_pl||step.title):step.title;
      option.dataset.label=`${n+1}. ${sTitle}`;
      option.textContent=(progress?.completed.includes(step.id)?'✓ ':'')+option.dataset.label;
      group.append(option);
    }
    select.append(group);
  }
  if(progress)select.value=progress.current;
  select.onchange=()=>go(select.value);
}

async function init(){
  if(initializing)return initializing;
  initializing=(async()=>{
    try{
      const response=await fetch('./data/assembly.json');if(!response.ok)throw new Error('Instructions unavailable');manifest=await response.json();
      progress=load();$('instructionStorage').textContent=storageMessage;
      updateLanguageUI();
      $('instructionLoad').hidden=true;$('instructionPrep').hidden=false;

      $('instructionLang').addEventListener('click',()=>{
        setLanguage(currentLang==='pl'?'en':'pl');
      });

      $('instructionStart').addEventListener('click',()=>{progress.started=true;save();renderStep();});
      $('instructionPrevious').addEventListener('click',()=>go(manifest.steps[Math.max(0,index()-1)].id));
      $('instructionNext').addEventListener('click',()=>go(manifest.steps[Math.min(manifest.steps.length-1,index()+1)].id));
      $('instructionComplete').addEventListener('click',()=>{
        if(!progress.completed.includes(progress.current))progress.completed.push(progress.current);
        go(manifest.steps[Math.min(manifest.steps.length-1,index()+1)].id);
      });
      $('instructionPreparation').addEventListener('click',()=>{scene?.setActive(false);$('instructionBuild').hidden=true;$('instructionPrep').hidden=false;updatePreparation();});
      for(const id of ['instructionRestart','instructionReset'])$(id).addEventListener('click',()=>{
        if(!confirm(t().restartConfirm))return;
        progress=fresh();storageMessage='';$('instructionReset').hidden=true;$('instructionAccept').hidden=true;save();prepare();scene?.setActive(false);$('instructionBuild').hidden=true;$('instructionPrep').hidden=false;
      });
      $('instructionAccept').addEventListener('click',()=>{progress.revision=manifest.revision;storageMessage='';$('instructionAccept').hidden=true;save();});
      $('instructionPlay').addEventListener('click',()=>scene?.playback());$('instructionReplay').addEventListener('click',()=>scene?.replay());
      $('instructionScrub').addEventListener('input',()=>scene?.setProgress(Number($('instructionScrub').value)/100));
      $('instructionFit').addEventListener('click',()=>scene?.fit());$('instructionCloseup').addEventListener('click',()=>scene?.fit(true));
      $('instructionIsolate').addEventListener('click',()=>{
        const isolated=scene?.toggleIsolated();
        $('instructionIsolate').setAttribute('aria-pressed',String(isolated));
        $('instructionIsolate').classList.toggle('active',Boolean(isolated));
        $('instructionIsolate').textContent=isolated?t().fullContext:t().isolate;
      });
      $('instructionAngleStep').addEventListener('click',()=>scene?.setView('step'));
      $('instructionAngleFront').addEventListener('click',()=>scene?.setView('front'));
      $('instructionAngleTop').addEventListener('click',()=>scene?.setView('top'));
      if(progress.started)renderStep();
    }catch{
      $('instructionLoad').textContent=t().loadError;$('instructionLoad').setAttribute('role','alert');
    }
  })();return initializing;
}

addEventListener('previewchange',event=>{
  const active=event.detail.preview==='instructions';
  if(active)init();scene?.setActive(active&&!$('instructionBuild').hidden);
});
if(location.hash==='#instructions')init();
window.addEventListener('keydown',e=>{
  if($('instructionsPanel').hidden||$('instructionBuild').hidden)return;
  const tag=document.activeElement?.tagName;
  if(tag==='INPUT'||tag==='SELECT'||tag==='TEXTAREA')return;
  if(e.key==='ArrowLeft'||e.key==='j'||e.key==='J'){
    e.preventDefault();$('instructionPrevious').click();
  }else if(e.key==='ArrowRight'||e.key==='k'||e.key==='K'){
    e.preventDefault();$('instructionNext').click();
  }else if(e.key===' '||e.code==='Space'){
    e.preventDefault();if(!$('instructionPlay').disabled)$('instructionPlay').click();
  }else if(e.key==='Enter'||e.key==='c'||e.key==='C'){
    e.preventDefault();$('instructionComplete').click();
  }else if(e.key==='z'||e.key==='Z'){
    e.preventDefault();$('instructionCloseup').click();
  }else if(e.key==='x'||e.key==='X'){
    e.preventDefault();$('instructionIsolate').click();
  }else if(e.key==='r'||e.key==='R'){
    e.preventDefault();if(!$('instructionReplay').disabled)$('instructionReplay').click();
  }
});
