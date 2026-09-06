import json, os, re, zipfile, html
from pathlib import Path

src_path = Path('/mnt/data/build_recipe_bank.py')
text = src_path.read_text(encoding='utf-8')
# Execute only recipe-data generation, stripping artifact_tool imports.
prefix = text.split("wb=Workbook.create()", 1)[0]
prefix = re.sub(r"^import os\n.*?from itertools import product\n", "from itertools import product\n", prefix, count=1, flags=re.S)
ns = {}
exec(prefix, ns)
recipes = ns['recipes']
ingredients = ns['ingredients']
swaps = ns['swaps']
assert len(recipes) == 800

recipe_keys = ['id','mealType','name','family','baseServes','prepMin','cookMin','budgetTier','protein','carb','focus','freezer','lunchbox','vegetarian','gfAdaptable','dfAdaptable','onePot','method','swapNotes']
recipe_objs = [dict(zip(recipe_keys, r)) for r in recipes]
by_recipe = {r['id']: [] for r in recipe_objs}
for row in ingredients:
    rid, num, ing, qty, unit, group, optional, swap_group = row
    by_recipe[rid].append({
        'number': num, 'ingredient': ing, 'baseQty': qty, 'unit': unit,
        'group': group, 'optional': optional == 'Yes', 'swapGroup': swap_group
    })
for r in recipe_objs:
    r['ingredients'] = by_recipe[r['id']]

swap_map = {}
for row in swaps:
    group = row[0]
    swap_map[group] = [x for x in row[1:] if x]

pairs = sorted({(i['ingredient'], i['unit']) for r in recipe_objs for i in r['ingredients']}, key=lambda x:(x[0].lower(),x[1].lower()))

data = {'recipes': recipe_objs, 'swapMap': swap_map, 'ingredientUnitPairs': [{'ingredient':a,'unit':b,'key':f'{a}|{b}'} for a,b in pairs]}

outdir = Path('/mnt/data/GENEVIEVE_Family_Budget_Cookbook_Household_Engine')
outdir.mkdir(exist_ok=True)
(outdir/'data.js').write_text('window.GENEVIEVE_DATA = ' + json.dumps(data, ensure_ascii=False, separators=(',',':')) + ';', encoding='utf-8')

index = r'''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>GENEVIEVE Family Budget Cookbook — Household Engine</title>
  <link rel="stylesheet" href="styles.css" />
</head>
<body>
  <header class="topbar">
    <div>
      <div class="brand">GENEVIEVE App™</div>
      <h1>Family Budget Cookbook</h1>
      <p>What have I got? · What can I afford? · How many people am I feeding?</p>
    </div>
    <div class="recipe-count"><strong id="recipeCount">800</strong><span>recipes</span></div>
  </header>

  <main>
    <section class="panel control-panel">
      <h2>1. Tell GENEVIEVE what the household needs</h2>
      <div class="controls-grid">
        <label>People to feed<input id="householdSize" type="number" min="1" max="30" value="4"></label>
        <label>Maximum spend for this meal ($)<input id="mealBudget" type="number" min="0" step="0.50" value="20"></label>
        <label>Meal type<select id="mealType"><option>Any</option><option>Breakfast</option><option>Lunch</option><option>Dinner/Tea</option><option>Snack</option><option>Dessert</option><option>Baking/Side</option></select></label>
        <label>Vegetarian<select id="vegetarian"><option>No restriction</option><option>Required</option></select></label>
        <label>GF adaptable<select id="gf"><option>No restriction</option><option>Required</option></select></label>
        <label>DF adaptable<select id="df"><option>No restriction</option><option>Required</option></select></label>
        <label>Lunchbox friendly<select id="lunchbox"><option>No restriction</option><option>Required</option></select></label>
        <label>Freezer friendly<select id="freezer"><option>No restriction</option><option>Required</option></select></label>
        <label>One pan / pot<select id="onePot"><option>No restriction</option><option>Required</option></select></label>
      </div>
      <button class="primary" id="rankBtn">Find meals</button>
    </section>

    <section class="two-col">
      <div class="panel">
        <div class="panel-head"><div><h2>2. What have I got?</h2><p>Enter only what is already at home. Quantities use the recipe unit shown.</p></div><span id="pantryCount" class="pill">0 entered</span></div>
        <div class="search-row"><input id="pantrySearch" placeholder="Search pantry ingredients…"><button id="clearPantry" class="secondary">Clear pantry</button></div>
        <div id="pantryList" class="entry-list"></div>
      </div>
      <div class="panel">
        <div class="panel-head"><div><h2>3. What will missing food cost?</h2><p>Enter a local price for the recipe unit. Unpriced shortages are labelled — never guessed.</p></div><span id="priceCount" class="pill">0 priced</span></div>
        <div class="search-row"><input id="priceSearch" placeholder="Search price book…"><button id="clearPrices" class="secondary">Clear prices</button></div>
        <div id="priceList" class="entry-list"></div>
      </div>
    </section>

    <section class="panel results-panel">
      <div class="panel-head">
        <div><h2>4. Best matches from all 800 recipes</h2><p>Ranking = pantry coverage (60) + affordability (30) + low missing-item bonus (10).</p></div>
        <div class="kpis"><span><b id="eligibleKpi">800</b> eligible</span><span><b id="cookNowKpi">0</b> cook now</span><span><b id="budgetKpi">0</b> within budget</span></div>
      </div>
      <div id="results" class="results"></div>
    </section>
  </main>

  <dialog id="recipeDialog">
    <button id="closeDialog" class="dialog-close" aria-label="Close">×</button>
    <div id="recipeDetail"></div>
  </dialog>

  <footer>GENEVIEVE Family Budget Cookbook™ · Prototype household decision engine · Local browser storage only</footer>
  <script src="data.js"></script>
  <script src="engine.js"></script>
</body>
</html>'''
(outdir/'index.html').write_text(index, encoding='utf-8')

css = r''':root{--gold:#c9a227;--black:#111;--ink:#222;--muted:#6b6b6b;--paper:#f6f4ed;--card:#fff;--green:#e3f3e7;--red:#fae7e7;--blue:#e9f2ff;--border:#ded9ca}*{box-sizing:border-box}body{margin:0;font-family:Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;background:var(--paper);color:var(--ink)}.topbar{background:var(--black);color:#fff;padding:26px max(22px,5vw);display:flex;justify-content:space-between;gap:24px;align-items:center;border-bottom:5px solid var(--gold)}.brand{color:var(--gold);font-weight:800;letter-spacing:.08em}.topbar h1{margin:3px 0 4px;font-size:clamp(28px,4vw,48px)}.topbar p{margin:0;color:#d7d7d7}.recipe-count{min-width:110px;border:1px solid #4b4327;border-radius:16px;padding:12px 20px;text-align:center;background:#1d1d1d}.recipe-count strong{display:block;color:var(--gold);font-size:30px}.recipe-count span{font-size:13px;color:#ccc}main{width:min(1500px,94vw);margin:28px auto 50px}.panel{background:var(--card);border:1px solid var(--border);border-radius:18px;padding:22px;box-shadow:0 6px 24px #0000000a}.panel h2{margin:0 0 5px;font-size:21px}.panel p{margin:0;color:var(--muted);font-size:14px}.controls-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:13px;margin:18px 0}label{font-size:12px;font-weight:750;color:#4d4d4d;text-transform:uppercase;letter-spacing:.03em}input,select{display:block;width:100%;margin-top:6px;border:1px solid #cac4b2;border-radius:10px;padding:11px;background:#fff;font:inherit;color:var(--ink)}button{cursor:pointer;font:inherit}.primary{background:var(--black);color:var(--gold);border:0;border-radius:10px;padding:12px 22px;font-weight:800}.secondary{border:1px solid #bbb29b;background:#fff;border-radius:10px;padding:9px 12px;font-weight:700}.two-col{display:grid;grid-template-columns:1fr 1fr;gap:18px;margin:18px 0}.panel-head{display:flex;justify-content:space-between;gap:14px;align-items:flex-start}.pill{background:#f2eedf;border:1px solid #e1d6a9;color:#554714;border-radius:999px;padding:6px 10px;font-weight:800;font-size:12px;white-space:nowrap}.search-row{display:flex;gap:8px;margin:15px 0 10px}.search-row input{margin:0}.entry-list{height:340px;overflow:auto;border-top:1px solid #eee}.entry-row{display:grid;grid-template-columns:1fr 112px;gap:12px;align-items:center;padding:9px 3px;border-bottom:1px solid #f0eee7}.entry-name{font-weight:700}.entry-unit{font-size:12px;color:var(--muted)}.entry-row input{margin:0;text-align:right}.results-panel{margin-top:18px}.kpis{display:flex;gap:9px;flex-wrap:wrap}.kpis span{background:#f3f1e8;border-radius:10px;padding:8px 10px;font-size:12px}.kpis b{font-size:17px}.results{display:grid;grid-template-columns:repeat(auto-fit,minmax(285px,1fr));gap:12px;margin-top:18px}.recipe-card{border:1px solid var(--border);border-radius:14px;padding:15px;display:flex;flex-direction:column;gap:10px;background:#fff}.recipe-card:hover{border-color:#c4aa52;box-shadow:0 5px 18px #0000000c}.recipe-top{display:flex;justify-content:space-between;gap:10px}.rank{font-size:12px;font-weight:900;color:#766114}.recipe-card h3{margin:0;font-size:17px}.tags{display:flex;flex-wrap:wrap;gap:5px}.tag{font-size:11px;padding:4px 7px;border-radius:999px;background:#eee}.tag.good{background:var(--green)}.tag.warn{background:#fff0cc}.tag.bad{background:var(--red)}.scorebar{height:7px;background:#eee;border-radius:20px;overflow:hidden}.scorebar i{display:block;height:100%;background:var(--gold)}.stats{display:grid;grid-template-columns:repeat(3,1fr);gap:7px}.stat{background:#f8f7f2;border-radius:8px;padding:7px;font-size:11px}.stat b{display:block;font-size:14px;margin-top:2px}.card-action{margin-top:auto;display:flex;justify-content:space-between;align-items:center;gap:8px}.view-btn{border:0;background:var(--black);color:#fff;border-radius:8px;padding:8px 10px;font-weight:750}.action-text{font-size:11px;color:var(--muted)}dialog{width:min(900px,94vw);max-height:90vh;border:0;border-radius:18px;padding:0;box-shadow:0 30px 90px #0006}dialog::backdrop{background:#0009}.dialog-close{position:absolute;right:14px;top:12px;border:0;background:#111;color:#fff;width:34px;height:34px;border-radius:50%;font-size:24px}.detail{padding:26px}.detail h2{font-size:29px;margin:0 45px 5px 0}.detail-sub{color:var(--muted)}.detail-grid{display:grid;grid-template-columns:1fr 1fr;gap:18px;margin-top:20px}.detail-box{border:1px solid var(--border);border-radius:12px;padding:14px}.detail-box h3{margin:0 0 10px}.ingredient-line{display:grid;grid-template-columns:1.3fr .55fr .55fr .7fr;gap:8px;padding:7px 0;border-bottom:1px solid #eee;font-size:13px}.ingredient-line.missing{background:#fff9f0}.ingredient-line.have{background:#f3faf4}.swap-note{font-size:11px;color:#75620d;margin-top:3px}.method-list{padding-left:20px;line-height:1.55}.budget-note{padding:12px;border-radius:10px;background:#f7f3e5;margin:14px 0}.warning{background:#fff0f0;border-left:4px solid #b94b4b;padding:10px;margin:12px 0;font-size:13px}footer{text-align:center;color:#777;padding:20px 12px 40px;font-size:12px}@media(max-width:900px){.two-col,.detail-grid{grid-template-columns:1fr}.topbar{align-items:flex-start}.recipe-count{display:none}.entry-list{height:280px}.panel-head{flex-direction:column}.ingredient-line{grid-template-columns:1fr .7fr}.ingredient-line span:nth-child(3),.ingredient-line span:nth-child(4){font-size:11px}}'''
(outdir/'styles.css').write_text(css, encoding='utf-8')

js = r'''(() => {
const D=window.GENEVIEVE_DATA; const $=id=>document.getElementById(id);
const pantry=JSON.parse(localStorage.getItem('gen_pantry_v1')||'{}');
const prices=JSON.parse(localStorage.getItem('gen_prices_v1')||'{}');
const controls=['householdSize','mealBudget','mealType','vegetarian','gf','df','lunchbox','freezer','onePot'];
let current=[];
const save=()=>{localStorage.setItem('gen_pantry_v1',JSON.stringify(pantry));localStorage.setItem('gen_prices_v1',JSON.stringify(prices));};
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const num=x=>Number(x)||0; const money=x=>'$'+Number(x||0).toFixed(2); const pct=x=>Math.round((x||0)*100)+'%';
function settings(){return {size:Math.max(1,num($('householdSize').value)),budget:Math.max(0,num($('mealBudget').value)),meal:$('mealType').value,veg:$('vegetarian').value,gf:$('gf').value,df:$('df').value,lunchbox:$('lunchbox').value,freezer:$('freezer').value,onePot:$('onePot').value};}
function pass(r,s){return (s.meal==='Any'||r.mealType===s.meal)&&(s.veg==='No restriction'||r.vegetarian==='Yes')&&(s.gf==='No restriction'||r.gfAdaptable==='Yes')&&(s.df==='No restriction'||r.dfAdaptable==='Yes')&&(s.lunchbox==='No restriction'||r.lunchbox==='Yes')&&(s.freezer==='No restriction'||r.freezer==='Yes')&&(s.onePot==='No restriction'||r.onePot==='Yes');}
function assess(r,s){const scale=s.size/r.baseServes; let req=0,covered=0,missing=0,cost=0,pricingComplete=true; const lines=[];
 r.ingredients.forEach(i=>{const required=i.optional?0:i.baseQty*scale; const key=i.ingredient+'|'+i.unit; const have=num(pantry[key]); const shortage=Math.max(0,required-have); const price=num(prices[key]); if(!i.optional){req++; if(shortage<=1e-9)covered++; else {missing++; if(price<=0)pricingComplete=false; cost+=shortage*price;}}
 lines.push({...i,required,have,shortage,price,missingCost:shortage*price});});
 const coverage=req?covered/req:1; const budgetScore=pricingComplete?(cost<=s.budget?30:Math.max(0,30*(1-cost/Math.max(s.budget,.01)))):0; const score=coverage*60+budgetScore+(missing===0?10:Math.max(0,10-missing));
 const budgetStatus=!pricingComplete?'Need prices':(cost<=s.budget?'Within budget':'Over budget'); const action=missing===0?'Cook now':(!pricingComplete?'Enter prices for missing ingredients':budgetStatus==='Within budget'?`Buy ${missing} missing ingredient line${missing===1?'':'s'}`:'Use swaps or choose another recipe');
 return {recipe:r,scale,lines,coverage,missing,cost,pricingComplete,budgetStatus,score,action}; }
function rank(){const s=settings(); current=D.recipes.filter(r=>pass(r,s)).map(r=>assess(r,s)).sort((a,b)=>b.score-a.score||b.coverage-a.coverage||a.recipe.name.localeCompare(b.recipe.name)); renderResults(current);}
function renderResults(rows){$('eligibleKpi').textContent=rows.length;$('cookNowKpi').textContent=rows.filter(x=>x.missing===0).length;$('budgetKpi').textContent=rows.filter(x=>x.pricingComplete&&x.cost<=settings().budget).length;
 $('results').innerHTML=rows.slice(0,30).map((x,i)=>{const r=x.recipe; const tag=x.missing===0?'good':x.budgetStatus==='Within budget'?'good':x.budgetStatus==='Need prices'?'warn':'bad';return `<article class="recipe-card"><div class="recipe-top"><div><div class="rank">#${i+1} · score ${x.score.toFixed(1)}</div><h3>${esc(r.name)}</h3></div><span class="tag ${tag}">${esc(x.budgetStatus)}</span></div><div class="tags"><span class="tag">${esc(r.mealType)}</span>${r.freezer==='Yes'?'<span class="tag">Freezer</span>':''}${r.lunchbox==='Yes'?'<span class="tag">Lunchbox</span>':''}${r.vegetarian==='Yes'?'<span class="tag">Vegetarian</span>':''}</div><div class="scorebar"><i style="width:${Math.min(100,x.score)}%"></i></div><div class="stats"><div class="stat">Pantry<b>${pct(x.coverage)}</b></div><div class="stat">Missing<b>${x.missing}</b></div><div class="stat">Gap cost<b>${x.pricingComplete?money(x.cost):'—'}</b></div></div><div class="card-action"><span class="action-text">${esc(x.action)}</span><button class="view-btn" data-id="${r.id}">View meal</button></div></article>`}).join('');
 document.querySelectorAll('.view-btn').forEach(b=>b.onclick=()=>openRecipe(b.dataset.id));}
function renderEntryList(kind,query=''){const store=kind==='pantry'?pantry:prices; const list=$(kind==='pantry'?'pantryList':'priceList'); const q=query.toLowerCase().trim(); const rows=D.ingredientUnitPairs.filter(p=>!q||p.ingredient.toLowerCase().includes(q)||p.unit.toLowerCase().includes(q)).slice(0,180); list.innerHTML=rows.map(p=>`<div class="entry-row"><div><div class="entry-name">${esc(p.ingredient)}</div><div class="entry-unit">recipe unit: ${esc(p.unit)}</div></div><input type="number" min="0" step="0.01" value="${store[p.key]||''}" data-key="${esc(p.key)}" placeholder="0"></div>`).join(''); list.querySelectorAll('input').forEach(inp=>inp.onchange=()=>{const v=num(inp.value);if(v>0)store[inp.dataset.key]=v;else delete store[inp.dataset.key];save();updateCounts();rank();});}
function updateCounts(){$('pantryCount').textContent=Object.keys(pantry).length+' entered';$('priceCount').textContent=Object.keys(prices).length+' priced';}
function openRecipe(id){const x=current.find(a=>a.recipe.id===id)||assess(D.recipes.find(r=>r.id===id),settings()); const r=x.recipe; const method=r.method.split(' | ').map(s=>s.replace(/^\d+\.\s*/,'')); const rows=x.lines.map(i=>{const sw=D.swapMap[i.swapGroup]||[];return `<div class="ingredient-line ${i.shortage<=1e-9?'have':'missing'}"><span><b>${esc(i.ingredient)}</b>${sw.length?`<div class="swap-note">Swap ideas: ${sw.slice(0,5).map(esc).join(', ')}</div>`:''}</span><span>Need<br><b>${i.required.toFixed(2)} ${esc(i.unit)}</b></span><span>Have<br><b>${i.have.toFixed(2)}</b></span><span>Short<br><b>${i.shortage.toFixed(2)}</b>${i.shortage>0&&i.price>0?`<br>${money(i.missingCost)}`:''}</span></div>`}).join('');
 $('recipeDetail').innerHTML=`<div class="detail"><h2>${esc(r.name)}</h2><div class="detail-sub">${esc(r.mealType)} · base serves ${r.baseServes} · scaled for ${settings().size} · prep ${r.prepMin} min · cook ${r.cookMin} min</div><div class="budget-note"><b>${pct(x.coverage)} pantry coverage</b> · ${x.missing} missing required line${x.missing===1?'':'s'} · ${x.pricingComplete?`estimated shopping gap ${money(x.cost)}`:'some missing ingredients still need prices'} · <b>${esc(x.budgetStatus)}</b></div>${!x.pricingComplete?'<div class="warning">Affordability is not claimed until every missing required ingredient has a price. GENEVIEVE does not guess prices.</div>':''}<div class="detail-grid"><div class="detail-box"><h3>Scaled ingredients</h3>${rows}</div><div class="detail-box"><h3>Method</h3><ol class="method-list">${method.map(m=>`<li>${esc(m)}</li>`).join('')}</ol><h3>Mix & change</h3><p>${esc(r.swapNotes||'Use the Swap Matrix options shown beside ingredients.')}</p></div></div></div>`; $('recipeDialog').showModal();}
$('closeDialog').onclick=()=>$('recipeDialog').close();$('rankBtn').onclick=rank; controls.forEach(id=>$(id).onchange=rank);$('pantrySearch').oninput=e=>renderEntryList('pantry',e.target.value);$('priceSearch').oninput=e=>renderEntryList('price',e.target.value);$('clearPantry').onclick=()=>{if(confirm('Clear all pantry quantities?')){Object.keys(pantry).forEach(k=>delete pantry[k]);save();renderEntryList('pantry',$('pantrySearch').value);updateCounts();rank();}};$('clearPrices').onclick=()=>{if(confirm('Clear all saved prices?')){Object.keys(prices).forEach(k=>delete prices[k]);save();renderEntryList('price',$('priceSearch').value);updateCounts();rank();}};
$('recipeCount').textContent=D.recipes.length;renderEntryList('pantry');renderEntryList('price');updateCounts();rank();
})();'''
(outdir/'engine.js').write_text(js, encoding='utf-8')

readme = '''# GENEVIEVE Family Budget Cookbook™ — Household Decision Engine

This package is a working browser prototype built around the 800-recipe V1 recipe bank.

## What it does
- scales every recipe to the number of people being fed;
- records pantry quantities by ingredient + recipe unit;
- records local prices without inventing prices;
- calculates shortages and estimated missing-ingredient cost;
- filters by meal type, vegetarian, GF-adaptable, DF-adaptable, lunchbox, freezer and one-pan/pot requirements;
- ranks all 800 recipes using pantry coverage (60 points), affordability (30), and low missing-item count (10);
- shows `Cook now`, `Need prices`, `Within budget`, or `Over budget` actions;
- opens each recipe with scaled ingredient requirements, pantry quantities, shortages, cost gaps, methods and swap suggestions;
- stores pantry and price data locally in the browser using localStorage.

## Run it
Open `index.html` in a browser. No server is required because the recipe data is bundled in `data.js`.

## Production boundary
This is the decision-engine prototype, not yet the final production data architecture. For the production GENEVIEVE app, move pantry, household, price-book, favourites and planner state into authenticated Cloudflare/Neon-backed user data. Retail pack-size/unit conversion is the next pricing layer before live supermarket-price automation.

## Important food note
GF/DF flags mean the recipe structure is adaptable. They are not allergen guarantees. Ingredient labels and cross-contamination requirements still need to be checked by the user.
'''
(outdir/'README.md').write_text(readme, encoding='utf-8')

contract = '''# GENEVIEVE Household Recipe Decision Engine — Contract

## Inputs
`household_size`, `meal_budget`, meal/diet/use filters, pantry quantities, and price-per-recipe-unit.

## Ingredient calculation
`scale_factor = household_size / base_serves`

For every required ingredient:
`required_qty = base_qty * scale_factor`
`shortage_qty = max(0, required_qty - pantry_qty)`
`missing_cost = shortage_qty * price_per_recipe_unit`

Optional ingredient lines do not reduce pantry coverage or force a purchase.

## Recipe calculation
`pantry_coverage = covered_required_lines / required_lines`
`estimated_missing_cost = sum(missing_cost)`
`pricing_complete = all missing required lines have a positive price`

A recipe is not labelled affordable until pricing is complete.

## Ranking
- Pantry coverage: 60 points
- Affordability: 30 points
- Missing-item bonus: 10 points
- Required user filters are hard gates before ranking.

## Next production layer
Add canonical ingredient IDs, pack sizes, unit conversion, current retail/source prices, shopping-basket rounding, household accounts and Neon persistence.
'''
(outdir/'ENGINE_CONTRACT.md').write_text(contract, encoding='utf-8')

# Add a simple manifest for archive/build control.
manifest = {
    'product':'GENEVIEVE Family Budget Cookbook™',
    'component':'Household Decision Engine',
    'recipes':len(recipe_objs),
    'ingredient_lines':len(ingredients),
    'ingredient_unit_keys':len(pairs),
    'files':['index.html','styles.css','engine.js','data.js','README.md','ENGINE_CONTRACT.md'],
    'persistence':'browser localStorage prototype',
    'production_stack_target':'GitHub + Cloudflare + Neon'
}
(outdir/'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')

zip_path = Path('/mnt/data/GENEVIEVE_Family_Budget_Cookbook_Household_Engine_V1.zip')
with zipfile.ZipFile(zip_path,'w',zipfile.ZIP_DEFLATED) as z:
    for p in outdir.iterdir():
        z.write(p, arcname=p.name)
print(json.dumps(manifest, indent=2))
print(zip_path)
