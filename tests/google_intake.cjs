/* Offline Apps Script harness. No Google calls and no email delivery. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const crypto = require('node:crypto');
const source = fs.readFileSync('google-apps-script/Code.gs','utf8');
const png = Buffer.alloc(45); Buffer.from([137,80,78,71,13,10,26,10]).copy(png);
png.writeUInt32BE(13,8); png.write('IHDR',12); png.writeUInt32BE(600,16); png.writeUInt32BE(800,20);
function harness() {
  const properties = {}, sent = [], folders = new Map(); let serial = 0;
  const controls = {owner:'lanaturetlhumain@gmail.com', mailFail:false, storageFail:false, quota:100, locked:false};
  const iterator = values => {let i=0;return {hasNext:()=>i<values.length,next:()=>values[i++]};};
  const blob = (value,type,name) => ({value,name,type,getDataAsString:()=>String(value),setName(n){this.name=n;return this;},setContentType(t){this.type=t;return this;}});
  function folder(name) {
    const f = {name,id:String(++serial),children:[],files:[],trashed:false,sharing:'private',
      getId(){return this.id;},setSharing(){this.sharing='private';},setTrashed(v){this.trashed=v;},
      createFolder(n){const child=folder(n);this.children.push(child);return child;},
      getFoldersByName(n){return iterator(this.children.filter(x=>x.name===n&&!x.trashed));},getFolders(){return iterator(this.children.filter(x=>!x.trashed));},
      createFile(n,value){if(controls.storageFail)throw Error('Drive failed');const b=typeof n==='object'?n:blob(value,'text/plain',n);const item={name:b.name,value:b.value,getBlob(){return blob(this.value,b.type,this.name);},setContent(v){this.value=v;}};this.files.push(item);return item;},
      getFilesByName(n){return iterator(this.files.filter(x=>x.name===n));}};
    folders.set(f.id,f);return f;
  }
  const context = vm.createContext({Date,JSON,Error,Number,String,Object,Array,Math,RegExp,
    Session:{getEffectiveUser:()=>({getEmail:()=>controls.owner})},
    PropertiesService:{getScriptProperties:()=>({getProperty:k=>properties[k],setProperty:(k,v)=>properties[k]=v})},
    DriveApp:{createFolder:folder,getFolderById:id=>folders.get(id),Access:{PRIVATE:'private'},Permission:{NONE:'none'}},
    ScriptApp:{getProjectTriggers:()=>[],newTrigger:()=>({timeBased(){return this;},everyHours(){return this;},create(){}})},
    LockService:{getScriptLock:()=>({tryLock:()=>!controls.locked,releaseLock(){}})},
    MimeType:{PLAIN_TEXT:'text/plain'},
    Utilities:{base64Decode:v=>[...Buffer.from(v,'base64')],newBlob:blob,DigestAlgorithm:{SHA_256:'sha256'},Charset:{UTF_8:'utf8'},computeDigest:(_,v)=>[...crypto.createHash('sha256').update(v).digest()]},
    MailApp:{getRemainingDailyQuota:()=>controls.quota,sendEmail:v=>{if(controls.mailFail)throw Error('Mail failed');sent.push(v);controls.quota--; }},
    HtmlService:{createHtmlOutput:html=>({html,setTitle(){return this;},addMetaTag(){return this;}})}});
  vm.runInContext(source,context);
  context.installer();
  const application = {first_name:'Amina',last_name:'Test',email:'applicant@example.org',phone:'+229 00000000',category:'actif',profession:'Biologiste',consent:true,consent_version:'2026-11-11-v2',photo:{mime:'image/png',base64:png.toString('base64')},function:'Présidente',payment:true};
  const payload = a=>({format:'lnh-membership-request',version:1,application:a||application});
  const post = (a=application,id='a'.repeat(32))=>context.doPost({postData:{length:JSON.stringify(a).length},parameter:{request:JSON.stringify(payload(a)),requestId:id,startedAt:String(Date.now()-2000),language:'fr'}}).html;
  return {context,application,payload,post,controls,sent,folders,properties};
}
let h = harness();
const clean = h.context.validate_(h.payload());
assert.equal(clean.profession,'Biologiste'); assert.equal(clean.function,undefined);assert.equal(clean.payment,undefined);
for (const change of [{email:''},{email:'a@example.org\r\nBcc:evil@example.org'},{consent:false},{consent_version:'old'},{category:'president'},{website:'robot'},{photo:{mime:'image/jpeg',base64:'eHh4eA=='}}]) {
  assert.throws(()=>h.context.validate_(h.payload({...h.application,...change})));
}
assert.match(h.post(),/Ton dossier et ta photo ont été enregistrés/);
assert.equal(h.sent.length,2);
assert.equal(h.sent[0].to,'lanaturetlhumain@gmail.com');assert.equal(h.sent[0].replyTo,'applicant@example.org');
assert.equal(h.sent[1].to,'applicant@example.org');assert.equal(h.sent[0].attachments.length,1);
assert.equal(JSON.parse(h.sent[0].attachments[0].value).application.function,undefined);
assert.match(h.post(),/Ton dossier et ta photo ont été enregistrés/);assert.equal(h.sent.length,2);
assert.match(h.post({...h.application,profession:'Changed'}),/L’envoi n’a pas pu être confirmé/);
assert.equal([...h.folders.values()].filter(f=>f.name.startsWith('demande-')&&!f.trashed).length,1);
h = harness();h.controls.mailFail=true;assert.match(h.post(),/notifications par email sont en attente/);assert.equal(h.sent.length,0);
h.controls.mailFail=false;h.context.relancerNotifications();assert.equal(h.sent.length,2);h.context.relancerNotifications();assert.equal(h.sent.length,2);
h = harness();h.controls.quota=0;assert.match(h.post(),/notifications par email sont en attente/);h.controls.quota=2;h.context.relancerNotifications();assert.equal(h.sent.length,2);
h = harness();h.controls.storageFail=true;assert.match(h.post(),/L’envoi n’a pas pu être confirmé/);assert.equal(h.sent.length,0);
h.controls.storageFail=false;assert.match(h.post(),/Ton dossier et ta photo ont été enregistrés/);
h = harness();h.controls.locked=true;assert.match(h.post(),/L’envoi n’a pas pu être confirmé/);assert.equal(h.sent.length,0);
h = harness();h.controls.owner='wrong@example.org';assert.match(h.post(),/L’envoi n’a pas pu être confirmé/);assert.throws(()=>h.context.installer());
h = harness();h.post();h.post(h.application,'b'.repeat(32));assert.match(h.post(h.application,'c'.repeat(32)),/L’envoi n’a pas pu être confirmé/);assert.equal(h.sent.length,4);
for (const cap of [{total:30,hourly:0},{total:10,hourly:10}]) {
  h=harness();const now=new Date().toISOString();h.properties.LNH_RATE=JSON.stringify({day:now.slice(0,10),hour:now.slice(0,13),emails:{},...cap});
  assert.match(h.post(),/L’envoi n’a pas pu être confirmé/);assert.equal(h.sent.length,0);
}
h=harness();
assert.match(h.context.doPost({postData:{length:4400001},parameter:{}}).html,/L’envoi n’a pas pu être confirmé/);
assert.match(h.context.doPost({postData:{length:100},parameter:{request:JSON.stringify(h.payload()),requestId:'a'.repeat(32),startedAt:Date.now(),language:'en'}}).html,/Sending could not be confirmed/);
assert.doesNotMatch(h.context.doGet().html,/Application received|Demande reçue/);
const direct=require('../adhesion/assets/direct.js');
assert.equal(direct.validEndpoint('https://script.google.com/macros/s/TEST/exec'),true);
for(const url of ['https://evil.org/exec','https://script.google.com.evil.org/macros/s/TEST/exec','https://script.google.com/macros/s/TEST/dev','javascript:alert(1)'])assert.equal(direct.validEndpoint(url),false);
let posted;
global.document={createElement(tag){return {tag,append(input){(this.inputs||=[]).push(input);},submit(){posted=this;},remove(){}};},body:{append(){}}};
direct.submit({email:'applicant@example.org'},'https://script.google.com/macros/s/TEST/exec','en','d'.repeat(32),Date.now()-2000);
assert.equal(posted.target,'_self');assert.equal(posted.method,'POST');assert.equal(JSON.parse(posted.inputs.find(x=>x.name==='request').value).application.email,'applicant@example.org');
assert.throws(()=>direct.submit({},'https://evil.org','fr','x',0));
console.log('Google intake: validation, private storage, idempotency, retries, limits, ownership and direct POST passed. No email sent.');
