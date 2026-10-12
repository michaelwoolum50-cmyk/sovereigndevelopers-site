let cancelRun = false;
const el = id => document.getElementById(id);

function logMsg(msg, type='info') {
  const c = el('log-container');
  const p = document.createElement('p');
  p.className = 'log-msg';
  if(type === 'error') p.classList.add('log-error');
  if(type === 'success') p.classList.add('log-success');
  if(type === 'warn') p.classList.add('log-warn');
  
  const time = new Date().toLocaleTimeString();
  p.textContent = `[${time}] ${msg}`;
  c.appendChild(p);
  c.scrollTop = c.scrollHeight;
}

const sleep = ms => new Promise(r => setTimeout(r, ms));

function getDegreeTitle(majorName, phase) {
  const isLaw = majorName.includes("Law");
  const isMed = majorName.includes("Medicine");
  const isCS = majorName.includes("Computer") || majorName.includes("Systems");
  
  if (phase === 'phase_1') {
    if (isLaw) return "Bachelor of Arts in Jurisprudence (Years 1–4)";
    if (isMed) return "Bachelor of Science in Pre-Medical Sciences (Years 1–4)";
    return "Bachelor of Science (Undergraduate Foundation, Years 1–4)";
  } else if (phase === 'phase_2') {
    if (isLaw) return "Juris Doctor (J.D.) & Master of Laws (Years 5–8)";
    if (isMed) return "Doctor of Medicine (M.D.) Clinical Core (Years 5–8)";
    return "Master of Science / Professional Degree (Years 5–8)";
  } else if (phase === 'phase_3') {
    if (isLaw) return "Doctor of Juridical Science (S.J.D.) & Multistate Bar Specialist (Years 8–12)";
    if (isMed) return "Board Certified Medical Specialist Fellow (USMLE Step 3, Years 8–12)";
    return "Doctor of Philosophy (Ph.D.) & Senior Research Fellow (Years 8–12)";
  } else {
    // Core (Years 1-8)
    if (isLaw) return "Comprehensive 8-Year Juris Doctor (J.D.) Professional Track";
    if (isMed) return "Comprehensive 8-Year Doctor of Medicine (M.D.) Professional Track";
    return "Comprehensive 8-Year Professional Master's Degree (Years 1–8)";
  }
}

async function startRun() {
  const majorSelect = el('major-select');
  const majorVal = majorSelect.value;
  const phaseSelect = el('phase-select');
  const phase = phaseSelect.value;
  const degreeTitle = getDegreeTitle(majorVal, phase);

  el('setup-panel').classList.add('hidden');
  el('run-panel').classList.remove('hidden');
  el('log-container').innerHTML = '';
  el('progress-fill').style.width = '0%';
  cancelRun = false;

  logMsg(`Initializing gemini-1.5-flash via Simulated Provider...`);
  logMsg(`Target Major: ${majorVal}`);
  logMsg(`Degree Track: ${degreeTitle}`);
  
  const chaptersCount = phase === 'core' ? 50 : 25;
  logMsg(`Beginning Collegiate Study Phase (${chaptersCount} primary source chapters)...`, 'warn');
  
  for (let i = 1; i <= chaptersCount; i++) {
    if (cancelRun) return logMsg("Simulation cancelled.", "error");
    logMsg(`Ingesting: ${majorVal} [${phase}] - Primary Source Module ${i}/${chaptersCount}...`);
    await sleep(25);
    const pct = (i / chaptersCount) * 50;
    el('progress-fill').style.width = `${pct}%`;
    el('status-text').textContent = `Studying: ${Math.round(pct)}%`;
  }
  
  logMsg("Collegiate Study Phase Complete. Neural weights tuned to gold standard.", 'success');
  logMsg(`Beginning Ivy League Examination (25 questions)...`, 'warn');
  
  let correct = 0;
  const totalQuestions = 25;
  for (let i = 1; i <= totalQuestions; i++) {
    if (cancelRun) return logMsg("Simulation cancelled.", "error");
    logMsg(`Administering Q${i}/${totalQuestions}: Examining advanced principles of ${majorVal}...`);
    await sleep(80);
    
    // Simulate 92% pass rate
    if (Math.random() > 0.08) {
      logMsg(`Result: CORRECT (Selected Choice ${(i % 4)})`, 'success');
      correct++;
    } else {
      logMsg(`Result: FAILED (Selected Choice ${(i+1)%4}, Expected Choice ${(i%4)})`, 'error');
    }
    
    const pct = 50 + ((i / totalQuestions) * 50);
    el('progress-fill').style.width = `${pct}%`;
    el('status-text').textContent = `Testing: ${Math.round(pct)}%`;
  }
  
  const finalScore = Math.round((correct / totalQuestions) * 100);
  logMsg(`Examination Complete! Final Score: ${finalScore}%`, finalScore >= 70 ? 'success' : 'error');
  
  if (finalScore >= 70) {
    logMsg("QUALIFICATION PASSED. Generating collegiate degree certificate...", 'success');
    await sleep(1000);
    el('run-panel').classList.add('hidden');
    el('cert-panel').classList.remove('hidden');
    el('cert-major').textContent = majorVal;
    el('cert-degree').textContent = degreeTitle;
    el('cert-score').textContent = `${finalScore}%`;
  } else {
    logMsg("QUALIFICATION FAILED. The agent requires further fine-tuning.", 'error');
  }
}

el('start-btn').addEventListener('click', startRun);
el('cancel-btn').addEventListener('click', () => { cancelRun = true; });
el('reset-btn').addEventListener('click', () => {
  el('cert-panel').classList.add('hidden');
  el('setup-panel').classList.remove('hidden');
});
