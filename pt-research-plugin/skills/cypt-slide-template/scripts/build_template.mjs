import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const SKILL_ROOT = path.resolve(HERE, "..");
const REPO = path.resolve(process.env.PT_WORKSPACE_ROOT ?? process.cwd());
const PRESENTATIONS_SKILL = process.env.PRESENTATIONS_SKILL ?? "/Users/vold/.codex/plugins/cache/openai-primary-runtime/presentations/26.915.20218/skills/presentations";
const RUNTIME_PYTHON = process.env.RUNTIME_PYTHON ?? "/Users/vold/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3";
const NODE_MODULES = process.env.RUNTIME_NODE_MODULES ?? "/Users/vold/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules";
process.env.RUNTIME_NODE_MODULES = NODE_MODULES;
const { Presentation, PresentationFile } = await import(pathToFileURL(path.join(NODE_MODULES,"@oai/artifact-tool/dist/artifact_tool.mjs")).href);
const { applyPresentationChartFont } = await import(pathToFileURL(path.join(PRESENTATIONS_SKILL,"container_tools/artifact_tool_utils.mjs")).href);
const configPath = path.resolve(process.argv[2] ?? path.join(SKILL_ROOT, "assets/template-config.json"));
const outputPath = path.resolve(process.argv[3] ?? path.join(REPO, "deliverables/cypt-slide-template/CYPT_editable_template.pptx"));
const cfg = JSON.parse(await fs.readFile(configPath, "utf8"));
if (!Array.isArray(cfg.sections) || cfg.sections.length < 1 || cfg.sections.length > 8) throw new Error("sections must contain 1-8 entries");
const themePath = path.resolve(path.dirname(configPath), cfg.themeFile ?? "singapore-cypt-theme.json");
const theme = JSON.parse(await fs.readFile(themePath, "utf8"));
const requiredColors = ["bg","ink","muted","red","yellow","orange","blue","purple","green","cyan","olive","slovakGreen"];
for (const key of requiredColors) if (!/^#[0-9a-fA-F]{6}$/.test(theme.colors?.[key] ?? "")) throw new Error(`invalid theme color: ${key}`);
if (!theme.fonts?.primary) throw new Error("theme primary font is required");
const C = theme.colors;
const F = theme.fonts.primary;
const SOURCE_IMAGES = path.join(SKILL_ROOT,"assets/source-images");
const P = Presentation.create({ slideSize:{ width:960, height:720 } });
const noLine = { fill:"none", width:0 };
const pos = (x,y,w,h)=>({left:x,top:y,width:w,height:h});
function shape(s,g,x,y,w,h,fill="none",stroke="none",sw=0,name){return s.shapes.add({geometry:g,name,position:pos(x,y,w,h),fill,line:{style:"solid",fill:stroke,width:sw}})}
function text(s,t,x,y,w,h,size=22,opt={}){
 const q=shape(s,"textbox",x,y,w,h,opt.fill??"none",opt.stroke??"none",opt.sw??0,opt.name);
 q.text=Array.isArray(t)?t:String(t); q.text.style={typeface:F,fontSize:size,bold:!!opt.bold,italic:!!opt.italic,color:opt.color??C.ink,alignment:opt.align??"left",verticalAlignment:opt.valign??"middle",autoFit:"shrinkText",wrap:true}; return q;
}
function line(s,x1,y1,x2,y2,color=C.ink,w=2){return s.shapes.add({geometry:"line",position:{left:Math.min(x1,x2),top:Math.min(y1,y2),width:Math.abs(x2-x1)||0.01,height:Math.abs(y2-y1)||0.01,verticalFlip:(x2-x1)*(y2-y1)<0},fill:"none",line:{style:"solid",fill:color,width:w}})}
function rect(s,x,y,w,h,fill="none",stroke="none",sw=0){return shape(s,"rect",x,y,w,h,fill,stroke,sw)}
function circle(s,cx,cy,r,fill,stroke="none",sw=0){return shape(s,"ellipse",cx-r,cy-r,2*r,2*r,fill,stroke,sw)}
function header(s,n){
 text(s,cfg.eventLabel,74,25,118,25,15,{bold:true});rect(s,165,34,684,10,C.ink);text(s,n,866,24,28,23,15,{align:"right"});
}
function footer(s,active){
 const n=cfg.sections.length, left=40,right=922,gap=27,barW=(right-left-gap*(n-1))/n;
 cfg.sections.forEach((x,i)=>{const xx=left+i*(barW+gap);text(s,x.title,xx,647,barW,29,n>5?14:17,{italic:true,align:"center",color:i<active?C.muted:C.ink});rect(s,xx,686,barW,10,i<active?C.muted:i===active?C.red:C.ink);});
}
function slide(title,section=null,{n=true,foot=true}={}){const s=P.slides.add();s.background.fill=C.bg;if(n)header(s,P.slides.items.length);if(title)text(s,title,72,69,820,70,52);if(foot&&section!==null){const active=typeof section==="string"?cfg.pageSections?.[section]:section;if(!Number.isInteger(active)||active<0||active>=cfg.sections.length)throw new Error(`invalid section for ${section}: ${active}`);footer(s,active)}return s;}
function notes(s,t){s.speakerNotes.textFrame.setText(t)}
function prompt(s,x,y,w,h,size){const emphasis=/(identical fidget spinners|neodymium magnets|side by side on a plane|remaining ones start to rotate)/g;const strong=/^(identical fidget spinners|neodymium magnets|side by side on a plane|remaining ones start to rotate)$/;const parts=cfg.problemStatement.split(emphasis).filter(Boolean);return text(s,parts.map(p=>({run:p,textStyle:{italic:true,bold:strong.test(p)}})),x,y,w,h,size,{italic:true})}
function label(s,t,x,y,w,h,fill=C.yellow,stroke=C.ink,size=15){rect(s,x,y,w,h,fill,stroke,1);text(s,t,x+4,y+1,w-8,h-2,size,{bold:true,italic:true,align:"center"})}
async function photo(s,name,x,y,w,h,alt,rotation=0){const im=s.images.add({blob:new Uint8Array(await fs.readFile(path.join(SOURCE_IMAGES,name))),contentType:"image/png",alt,fit:"contain",position:pos(x,y,w,h)});im.rotation=rotation;return im}
function dot(s,x,y,color=C.red,r=13){circle(s,x,y,r,color)}
function dash(s,x1,y1,x2,y2,color=C.olive){for(let i=0;i<9;i+=2){const a=i/9,b=Math.min(1,(i+1)/9);line(s,x1+(x2-x1)*a,y1+(y2-y1)*a,x1+(x2-x1)*b,y1+(y2-y1)*b,color,2)}}
function plotLine(s,x,y,w,h,values,color=C.red){line(s,x,y+h,x+w,y+h,C.ink,1);line(s,x,y,x,y+h,C.ink,1);for(let i=0;i<values.length-1;i++)line(s,x+i*w/(values.length-1),y+h-values[i]*h,x+(i+1)*w/(values.length-1),y+h-values[i+1]*h,color,2.5)}
function spinner(s,cx,cy,r=48,rot=0,arms=4,colors=["#F50000","#003DFF"]){
 const rad=rot*Math.PI/180;for(let i=0;i<arms;i++){const a=rad+i*2*Math.PI/arms,x=cx+Math.cos(a)*r,y=cy+Math.sin(a)*r;line(s,cx,cy,x,y,C.olive,2);circle(s,x,y,10,colors[i%colors.length]);}circle(s,cx,cy,3,C.ink);
}
function sampleChart(s,{x=91,y=171,w=780,h=429,banner=false}={}){
 const chart=s.charts.add("line",{position:pos(x,y,w,h),categories:["x₁","x₂","x₃","x₄","x₅"],series:[
  {name:"Experiment",values:[1.1,1.6,2.1,2.7,3.2],line:{fill:C.blue,width:3},marker:{symbol:"circle",size:7}},
  {name:"Theory",values:[1.0,1.7,2.2,2.6,3.1],line:{fill:C.red,width:2},marker:{symbol:"none"}}
 ],hasLegend:true,legend:{position:"top"},xAxis:{title:"Independent variable / unit"},yAxis:{title:"Observable / unit",minimumScale:0,maximumScale:4},chartFill:C.bg,plotAreaFill:C.bg,chartLine:{fill:"none",width:0},plotAreaLine:{fill:C.ink,width:1}});
 chart.title="";
 applyPresentationChartFont(chart,{fontFamily:F});
 text(s,"ILLUSTRATIVE DATA — replace values, labels and units",95,602,700,24,13,{italic:true,color:"#555555"});
 if(banner){rect(s,0,331,960,112,`${C.slovakGreen}/88`);text(s,"State the supported conclusion here",65,351,830,73,39,{bold:true,color:"#FFFFFF",align:"center"});}
 return chart;
}

// 1 Cover — Singapore's restrained cover composition.
{
 const s=slide("",null,{foot:false});
 text(s,cfg.problemTitle,188,127,690,76,55);text(s,cfg.teamLine,190,207,650,41,29);
 rect(s,74,276,810,10,C.ink);text(s,cfg.problemStatement,75,315,425,255,27,{italic:true});
 spinner(s,648,425,76);spinner(s,810,425,76);rect(s,74,641,810,10,C.ink);
 notes(s,"Editable cover. Replace title, presenter, event label and prompt. Source composition: Team Singapore Magnetic Gear PDF, page 1.");
}
// 2 Problem statement — concise prompt and parameter callouts.
{
 const s=slide("Problem Statement",0,{foot:false});prompt(s,72,158,820,115,27);
 label(s,"Parameters",58,278,145,33);spinner(s,353,424,58);spinner(s,579,424,58);line(s,421,424,511,424,C.olive,2);
 label(s,"Spinner parameters",670,303,228,31,C.bg,C.orange,15);text(s,"• Number of arms\n• Magnet arrangement",687,339,206,84,17,{italic:true});
 label(s,"Magnet parameters",670,443,228,31,C.bg,C.blue,15);text(s,"• Orientation\n• Magnetization",687,480,206,84,17,{italic:true});
 notes(s,"Source prompt and layout based on Team Singapore PDF, pages 2–3. Prompt wording is retained as reference content.");
}
// 3 The requested colored parameter inventory, rebuilt as editable shapes.
{
 const s=slide("Problem Statement",0,{foot:false});
 prompt(s,72,151,820,134,25);label(s,"Parameters",72,311,166,37);
 rect(s,20,388,282,154,C.bg,C.purple,3);text(s,"Spinner positions",68,374,204,33,22,{italic:true,color:C.purple,align:"center",fill:C.bg});
 text(s,"Distance between spinners\n\nNumber of spinners\n\nArrangement of spinners",43,413,245,120,17,{italic:true,color:"#555555"});
 rect(s,20,580,282,112,C.bg,C.green,3);text(s,"Initial conditions",69,566,202,33,22,{italic:true,color:C.green,align:"center",fill:C.bg});
 text(s,"Initial angular positions\nInitial angular velocities",45,613,245,57,17,{italic:true,color:"#555555"});
 rect(s,614,379,256,96,C.bg,C.orange,3);text(s,"Spinner parameters",638,364,222,36,21,{italic:true,color:C.orange,align:"center",fill:C.bg});
 dot(s,647,420,C.orange,5);dot(s,647,451,C.orange,5);text(s,"Number of arms",682,421,168,31,18,{italic:true,color:"#555555"});
 rect(s,674,490,234,190,C.bg,C.blue,3);text(s,"Magnet parameters",685,476,204,36,21,{italic:true,color:C.blue,align:"center",fill:C.bg});
 dot(s,716,544,"#003DFF",14);dot(s,735,554,C.red,14);text(s,"Orientation of\nmagnets",771,522,115,61,17,{italic:true,color:"#555555"});
 spinner(s,725,626,23,15,4,[C.red,"#003DFF"]);text(s,"Magnetization",772,607,118,37,17,{italic:true,color:"#555555"});
 [[418,344],[528,394],[418,466],[325,499],[436,542],[529,505],[326,613],[437,606],[626,606]].forEach(([x,y])=>dot(s,x,y));
 [[418,344,456,413],[456,413,528,394],[456,413,418,466],[325,499,365,570],[365,570,436,542],[365,570,326,613],[436,542,480,605],[480,605,529,505],[480,605,437,606],[529,505,577,572],[577,572,626,606]].forEach(a=>line(s,...a,C.olive,2));
 notes(s,"Team Singapore PDF page 4. Colored parameter groups and diagram are editable native shapes; the four category labels and original parameter wording are retained. Verify prompt wording and replace the sample diagram when converting a different problem.");
}
// 4 Overview — section count and footer share the same config list.
{
 const s=slide("Overview",null,{foot:false});const rowH=Math.min(112,455/cfg.sections.length),font=cfg.sections.length>5?21:27;cfg.sections.forEach((sec,i)=>{const yy=170+i*rowH;text(s,i+1,150,yy,60,rowH-4,font+5,{italic:true,align:"right"});rect(s,240,yy+9,6,rowH-25,C.ink);text(s,sec.title,328,yy,505,rowH/2,font,{bold:true,italic:true});text(s,sec.subtitle,328,yy+rowH/2-6,505,rowH/2-5,font-6,{italic:true});});notes(s,"Edit sections in assets/template-config.json and rerun the builder. The overview and every roadmap footer are generated from the same section list.");
}
// 5 Section divider.
{
 const s=slide("",0,{foot:false});text(s,cfg.sections[0].title,72,506,720,90,57);notes(s,"Duplicate this divider for any section; update its section index in the build configuration.");
}
// 6 Model/diagram page.
{
 const s=slide("Current Cylinder Model","model");spinner(s,272,359,118,8,12,["#D9E4D1", "#A4B993"]);circle(s,699,359,118,"#DCE4D6",C.ink,3);text(s,"≡",468,307,70,100,67,{align:"center"});label(s,"Model assumption",153,523,245,43,C.yellow);text(s,"Replace this diagram and statement with the model used in the new problem.",417,521,465,88,23,{italic:true});notes(s,"Diagram is editable. This is a layout exemplar based on Team Singapore PDF page 7, not a validated model for another problem.");
}
// 7 Source characterization pattern: three apparatus images above three compact plots.
{
 const s=slide("Characterization","characterization");
 const imgs=["p10-image1.png","p10-image0.png","p10-image2.png"], names=["Moment of inertia","Air drag & friction","Magnetization"];
 for(let i=0;i<3;i++){const x=43+i*319;await photo(s,imgs[i],x,168,211,165,`Team Singapore apparatus photograph: ${names[i]}`);rect(s,x,166,211,167,"none",C.ink,3);label(s,names[i],x-5,342,221,38,C.yellow,C.ink,18)}
 plotLine(s,40,411,243,136,[0.04,0.22,0.40,0.58,0.76,0.94]);
 plotLine(s,359,411,243,136,[0,0.34,0.59,0.76,0.89,0.97]);
 plotLine(s,678,411,243,136,[0.99,0.49,0.24,0.12,0.05,0.01]);
 label(s,"I = 1.72 × 10⁻⁴ kg m²",32,566,261,38,C.bg,C.ink,16);
 label(s,"cdrag = 2.41 × 10⁻⁵ kg m² s⁻¹",346,566,270,38,C.bg,C.ink,15);
 label(s,"M = (6.5 ± 0.5) × 10⁵ A/m",668,566,270,38,C.bg,C.ink,15);
 text(s,"Schematic plots — replace data",40,608,250,25,12,{italic:true,color:"#555555"});
 label(s,"τfriction = 1.48 × 10⁻⁴ N m",346,606,270,30,C.bg,C.ink,14);
 notes(s,"Layout and retained example values: Team Singapore Magnetic Gear PDF page 10. Photos are embedded replaceable image objects. Plot lines are editable schematic redraws for layout only; obtain original data before using the graphs as evidence. Numerical values also require source verification before reuse in a new presentation.");
}
// 8 Equation + diagram page.
{
 const s=slide("Small oscillations","equations");
 text(s,"m₁, m₂ – Magnetic dipole moment",590,138,300,31,17,{italic:true});
 spinner(s,345,288,65,13,3,[C.red,"#003DFF",C.red]);spinner(s,663,288,65,41,3,["#003DFF",C.red,C.red]);
 dot(s,317,231,"#FFC4C4",16);dot(s,610,216,"#C3C2FF",16);line(s,352,401,663,401,C.olive,1.5);text(s,"d₀",491,381,43,30,18,{italic:true,align:"center"});
 text(s,"Dipole approximation",92,445,300,31,21,{italic:true,align:"center"});
 text(s,"Linearized equations of motion",504,445,390,31,21,{italic:true,align:"center"});
 text(s,"Fmag(d) = 3 μ₀m₁m₂ / (4πd⁴)",91,500,318,58,25,{italic:true,align:"center"});
 text(s,"→",432,507,77,51,39,{align:"center"});
 text(s,"Iθ̈₁ = K[(R − d₀)θ₁ + Rθ₂]",519,493,377,42,22,{italic:true});
 text(s,"Iθ̈₂ = K[Rθ₁ + (R − d₀)θ₂]",519,539,377,42,22,{italic:true});
 text(s,"K = 3 μ₀m₁m₂R / [4π(d₀ − 2R)⁵]",519,583,385,35,18,{italic:true});
 notes(s,"Editable interpretation of Team Singapore PDF page 21: two perturbed spinner diagrams and the dipole-to-linearized-equation hierarchy. The compact K substitution is for template readability; verify equations, assumptions, symbols and typesetting against the original before citing or presenting them.");
}
// 9 Apparatus / evidence page.
{
 const s=slide("Experimental Set-up","apparatus");
 await photo(s,"p14-image0.png",72,126,535,535,"Team Singapore photograph of two magnetic spinners",270);
 rect(s,72,249,535,288,"none",C.ink,3);
 await photo(s,"p14-image1.png",700,327,162,162,"Team Singapore close-up of ceramic bearing");
 circle(s,781,408,85,"none",C.olive,4);
 rect(s,246,175,206,70,"#ECEAE4",C.ink,2);text(s,"3D printed\nfidget spinners",264,181,172,58,22,{italic:true,align:"center"});
 rect(s,641,174,261,101,"#ECEAE4",C.ink,2);text(s,"Non-magnetic\nceramic bearings to\nreduce friction",660,182,222,85,21,{italic:true,align:"center"});
 dash(s,604,340,702,359);dash(s,604,469,702,458);circle(s,314,601,24,"none",C.ink,2);text(s,"✓",295,578,40,45,27,{align:"center"});text(s,"Two bearings for each spinner\nto prevent wobbling",352,581,360,54,20,{italic:true});
 notes(s,"Team Singapore PDF page 14. Both photographs are user-supplied source images and remain replaceable image objects. Callout boxes, connectors and checkmark are editable. Ensure the photo orientation/crop and component labels fit the apparatus when reusing this layout.");
}
// 9 Editable graph page.
{
 const s=slide("Graph and comparison","graph");sampleChart(s);notes(s,"Native editable chart with illustrative values only. Replace every value, axis label, unit and legend before presenting. Layout based on Team Singapore graph pages 17–24.");
}
// 10 Optional Slovakia-style graph conclusion banner.
{
 const s=slide("Graph with conclusion","graphBanner");sampleChart(s,{banner:true});notes(s,"Optional translucent banner adapted from Team Slovakia Wet Scroll PDF page 26. Rewrite the statement to a conclusion supported by the plotted data; remove the banner where it hides important evidence.");
}
// 11 Theory/experiment comparison.
{
 const s=slide("Theory and experiment","comparison");label(s,"Experiment",57,154,392,39);label(s,"Theory",510,154,392,39);rect(s,57,207,392,340,C.bg,C.ink,2);rect(s,510,207,392,340,C.bg,C.ink,2);text(s,"Insert measured graph, photo or video still",93,318,320,99,23,{italic:true,align:"center"});text(s,"Insert model prediction or mechanism diagram",550,318,309,99,23,{italic:true,align:"center"});text(s,"State the agreement and the disagreement, including uncertainty.",84,570,795,59,22,{italic:true,align:"center"});notes(s,"Comparison layout based on Team Singapore pages 29–30. Preserve measured values and uncertainty when transforming a source deck.");
}
// 12 Summary card with retained style, flexible content.
{
 const s=slide("Summary","summary");text(s,cfg.problemStatement,54,143,845,99,21,{italic:true});label(s,"Main model",54,265,354,36,C.cyan);label(s,"Key observation",552,265,354,36,C.cyan);text(s,"• Physical mechanism\n• Assumptions and limits\n• Parameter dependence",73,320,343,176,23);text(s,"• Measured trend\n• Theory comparison\n• Remaining discrepancy",569,320,343,176,23);notes(s,"Summary layout based on Team Singapore pages 63–65. Bullet content is instructional placeholder text, not a finding.");
}
// 13 References.
{
 const s=slide("References",null,{foot:false});text(s,"1. Author, title, publication, year.\n\n2. Data or apparatus source, locator, date.\n\n3. Figure and image credits, where applicable.",74,173,806,345,24);notes(s,"Editable reference page. Replace every placeholder with traceable citations from the source presentation and any new material.");
}
// 14 Closing.
{
 const s=slide("",null,{foot:false});text(s,"Thank you!",189,146,610,65,46);text(s,cfg.teamLine,190,217,595,36,25);rect(s,50,287,860,6,C.ink);spinner(s,684,439,78);text(s,cfg.problemTitle,54,351,520,56,32);rect(s,50,608,860,6,C.ink);notes(s,"Closing layout based on Team Singapore PDF page 67. Replace title and presenter.");
}

await fs.mkdir(path.dirname(outputPath),{recursive:true});
const staging=path.join(REPO,"tmp/cypt-template/build");await fs.mkdir(staging,{recursive:true});
const draft=path.join(staging,"candidate.pptx");await (await PresentationFile.exportPptx(P)).save(draft);
const {finalizePresentation}=await import(pathToFileURL(path.join(PRESENTATIONS_SKILL,"container_tools/artifact_tool_utils.mjs")).href);
const result=await finalizePresentation({workspaceDir:REPO,candidatePath:draft,finalPath:outputPath,pythonExecutable:RUNTIME_PYTHON,integrityValidatorPath:path.join(PRESENTATIONS_SKILL,"container_tools/inspect_presentation_package_integrity.py"),layoutValidatorPath:path.join(PRESENTATIONS_SKILL,"container_tools/inspect_presentation_layout_geometry.py"),layoutArgs:["--expected-slide-size-emu","9144000,6858000","--validate-heading-fit"],explicitTotalSlideCount:15,requiredNativeChartOwnerSlides:[10,11],requiredNativeTableOwnerSlides:[],materializeLiteralChartWorkbooks:true,nativeChartTargetApplication:"powerpoint",fontPolicy:{basis:"design",families:[F]},verifyArtifactToolImport:true,receiptPath:path.join(staging,`${path.basename(outputPath)}.validation.json`)});
console.log(JSON.stringify({outputPath,slides:P.slides.items.length,result},null,2));
