/* La Nature et l'Humain: private intake only. No membership/card issuance. */
const LNH_GOOGLE = Object.freeze({
  owner: 'lanaturetlhumain@gmail.com', recipient: 'lanaturetlhumain@gmail.com',
  site: 'https://www.lanatureetlhumain.org', consent: '2026-11-11-v2',
  categories: ['actif', 'sympathisant', 'institutionnel'], dailyLimit: 30, hourlyLimit: 10
});

// Run once, as the association account. No email is sent by this setup.
function installer() {
  owner_();
  const properties = PropertiesService.getScriptProperties();
  if (!properties.getProperty('LNH_FOLDER_ID')) {
    const folder = DriveApp.createFolder('LNH - Demandes adhesion - PRIVE');
    folder.setSharing(DriveApp.Access.PRIVATE, DriveApp.Permission.NONE);
    properties.setProperty('LNH_FOLDER_ID', folder.getId());
  }
  if (!ScriptApp.getProjectTriggers().some(t => t.getHandlerFunction() === 'relancerNotifications')) {
    ScriptApp.newTrigger('relancerNotifications').timeBased().everyHours(1).create();
  }
  return 'Service prêt. Déployer une application Web exécutée en tant que propriétaire, accessible à tous.';
}

function owner_() {
  if (Session.getEffectiveUser().getEmail().toLowerCase() !== LNH_GOOGLE.owner) {
    throw new Error('Utiliser le compte Google de l’association.');
  }
}

function doGet() {
  return receipt_(true, 'fr', '', '');
}

function doPost(e) {
  let language = 'fr';
  try {
    owner_();
    if (!e || !e.postData || e.postData.length > 4400000 || !e.parameter) throw new Error('Dossier invalide.');
    language = e.parameter.language === 'en' ? 'en' : 'fr';
    const raw = JSON.parse(e.parameter.request || 'null');
    const application = validate_(raw);
    const id = e.parameter.requestId || '';
    if (!/^[a-f0-9]{32}$/.test(id)) throw new Error('Référence incorrecte.');
    const started = Number(e.parameter.startedAt);
    if (!Number.isFinite(started) || Date.now() - started < 1500 || Date.now() - started > 7200000) {
      throw new Error('Recharge le formulaire avant de réessayer.');
    }
    const result = receive_(id, application, language);
    return receipt_(true, language, result.reference, result.notifications);
  } catch (error) {
    // Never expose exception details, folder IDs, applicant data or stack traces.
    return receipt_(false, language, '', '');
  }
}

function field_(value, maximum, required) {
  if (typeof value !== 'string') value = '';
  value = value.trim();
  if ((required && !value) || value.length > maximum || /[\u0000-\u0008\u000b\u000c\u000e-\u001f\u007f]/.test(value)) {
    throw new Error('Champ invalide.');
  }
  return value;
}

function validate_(envelope) {
  if (!envelope || envelope.format !== 'lnh-membership-request' || envelope.version !== 1) throw new Error('Format invalide.');
  const input = envelope.application;
  if (!input || input.consent !== true || input.consent_version !== LNH_GOOGLE.consent || input.website) throw new Error('Consentement requis.');
  const data = {};
  [['first_name',80,true],['last_name',80,true],['email',254,true],['phone',40,true],
   ['address',250,false],['city',100,false],['country',100,false],['profession',120,false],
   ['motivation',2000,true],['category',60,true]].forEach(spec => {
    data[spec[0]] = field_(input[spec[0]], spec[1], spec[2]);
  });
  if (/[\r\n\t]/.test(data.first_name + data.last_name) ||
      !/^[^\s<>@\r\n]+@[^\s<>@\r\n]+\.[^\s<>@\r\n]+$/.test(data.email) ||
      !LNH_GOOGLE.categories.includes(data.category)) throw new Error('Coordonnées invalides.');
  data.email = data.email.toLowerCase();
  const photo = input.photo;
  if (!photo || !['image/jpeg','image/png'].includes(photo.mime) || typeof photo.base64 !== 'string' ||
      photo.base64.length > 4000000 || !/^(?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?$/.test(photo.base64)) {
    throw new Error('Photo invalide.');
  }
  const bytes = Utilities.base64Decode(photo.base64).map(b => b & 255);
  const size = imageSize_(bytes, photo.mime);
  if (bytes.length > 3000000 || size[0] < 240 || size[1] < 320 || size[0] * size[1] > 16000000) throw new Error('Dimensions invalides.');
  data.photo = {name:photo.mime === 'image/png' ? 'photo.png' : 'photo.jpg', mime:photo.mime, base64:photo.base64};
  data.consent = true;
  data.consent_version = LNH_GOOGLE.consent;
  // Unknown keys, especially function/status/payment/number, are discarded.
  return data;
}

function imageSize_(bytes, mime) {
  const u32 = i => bytes[i]*16777216 + bytes[i+1]*65536 + bytes[i+2]*256 + bytes[i+3];
  if (mime === 'image/png') {
    if (bytes.length < 33 || bytes.slice(0,8).join(',') !== '137,80,78,71,13,10,26,10' ||
        bytes.slice(12,16).join(',') !== '73,72,68,82') throw new Error('PNG invalide.');
    return [u32(16),u32(20)];
  }
  if (bytes[0] !== 255 || bytes[1] !== 216 || bytes[bytes.length-2] !== 255 || bytes[bytes.length-1] !== 217) throw new Error('JPEG invalide.');
  let offset = 2;
  while (offset + 4 < bytes.length) {
    if (bytes[offset++] !== 255) throw new Error('JPEG invalide.');
    while (bytes[offset] === 255) offset++;
    const marker = bytes[offset++];
    if (marker === 218 || marker === 217) break;
    const length = bytes[offset]*256 + bytes[offset+1];
    if (length < 2 || offset + length > bytes.length) break;
    if ([192,193,194].includes(marker) && length >= 8) return [bytes[offset+5]*256+bytes[offset+6],bytes[offset+3]*256+bytes[offset+4]];
    offset += length;
  }
  throw new Error('Dimensions JPEG absentes.');
}

function hash_(value) {
  return Utilities.computeDigest(Utilities.DigestAlgorithm.SHA_256, value, Utilities.Charset.UTF_8)
    .map(b => ('0' + (b & 255).toString(16)).slice(-2)).join('');
}

function read_(folder, name) {
  const files = folder.getFilesByName(name);
  return files.hasNext() ? JSON.parse(files.next().getBlob().getDataAsString()) : null;
}

function write_(folder, name, value) {
  const files = folder.getFilesByName(name);
  const text = JSON.stringify(value);
  if (files.hasNext()) files.next().setContent(text);
  else folder.createFile(name, text, MimeType.PLAIN_TEXT);
}

function receive_(id, application, language) {
  const lock = LockService.getScriptLock();
  if (!lock.tryLock(25000)) throw new Error('Service occupé.');
  try {
    const properties = PropertiesService.getScriptProperties();
    const rootId = properties.getProperty('LNH_FOLDER_ID');
    if (!rootId) throw new Error('Installer le service.');
    const root = DriveApp.getFolderById(rootId);
    const folders = root.getFoldersByName('demande-' + id);
    let folder, state;
    const payloadHash = hash_(JSON.stringify(application));
    if (folders.hasNext()) {
      folder = folders.next();
      state = read_(folder, 'etat.json');
      if (!state || state.hash !== payloadHash) throw new Error('Référence déjà utilisée.');
    } else {
      const current = new Date().toISOString();
      const day = current.slice(0,10), hour = current.slice(0,13);
      let rate = JSON.parse(properties.getProperty('LNH_RATE') || '{}');
      if (rate.day !== day) rate = {day:day, hour:hour, total:0, hourly:0, emails:{}};
      if (rate.hour !== hour) { rate.hour = hour; rate.hourly = 0; }
      const emailHash = hash_(application.email);
      if (rate.total >= LNH_GOOGLE.dailyLimit || rate.hourly >= LNH_GOOGLE.hourlyLimit || (rate.emails[emailHash] || 0) >= 2) throw new Error('Limite atteinte.');
      // Count attempts before writing, so storage failures cannot bypass limits.
      rate.total++; rate.hourly++; rate.emails[emailHash] = (rate.emails[emailHash] || 0) + 1;
      properties.setProperty('LNH_RATE', JSON.stringify(rate));
      folder = root.createFolder('demande-' + id);
      state = {hash:payloadHash, reference:'LNH-D-' + id, receivedAt:current, language:language, admin:false, applicant:false};
      try {
        folder.createFile(Utilities.newBlob(Utilities.base64Decode(application.photo.base64),application.photo.mime,application.photo.name));
        write_(folder, 'demande-adhesion-lnh.json', {format:'lnh-membership-request', version:1, application:application, received_at:current});
        write_(folder, 'etat.json', state);
      } catch (error) {
        folder.setTrashed(true); // Incomplete record, recoverable by the account owner.
        throw error;
      }
    }
    notify_(folder, state);
    return {reference:state.reference, notifications:state.admin && state.applicant ? 'sent' : 'pending'};
  } finally { lock.releaseLock(); }
}

function notify_(folder, state) {
  const envelope = read_(folder, 'demande-adhesion-lnh.json');
  if (!envelope) return;
  const data = envelope.application;
  try {
    if (!state.admin && MailApp.getRemainingDailyQuota() > 0) {
      const attachment = applicationPdf_(folder, data, state);
      const photo = Utilities.newBlob(Utilities.base64Decode(data.photo.base64), data.photo.mime,
        'photo-' + state.reference + (data.photo.mime === 'image/png' ? '.png' : '.jpg'));
      MailApp.sendEmail({to:LNH_GOOGLE.recipient, replyTo:data.email, name:'La Nature et l’Humain',
        subject:'Nouvelle demande d’adhésion | ' + state.reference,
        body:'Une demande a été enregistrée depuis le site officiel.\n\nRéférence : ' + state.reference +
          '\nNom : ' + data.first_name + ' ' + data.last_name + '\nE-mail : ' + data.email +
          '\nTéléphone : ' + data.phone + '\nCatégorie souhaitée : ' + data.category +
          '\n\nPièces jointes : dossier de demande en PDF et photo du demandeur en fichier image séparé.' +
          '\nLe PDF est destiné à l’examen administratif. La demande reste en attente de décision ; aucune carte ni aucun numéro de membre ne sont délivrés.' +
          '\n\nDossier privé (compte de l’association uniquement) : ' + folder.getUrl() +
          '\nPour l’import dans l’administration locale, le fichier technique demande-adhesion-lnh.json reste disponible dans ce dossier privé. Il n’est pas nécessaire pour lire le dossier PDF.',
        attachments:[attachment, photo]});
      state.admin = true; write_(folder, 'etat.json', state);
    }
  } catch (error) {
    // A PDF/conversion or mail failure must not prevent the applicant receipt.
    // The saved application is retained; the hourly trigger retries this notice.
  }
  try {
    if (!state.applicant && MailApp.getRemainingDailyQuota() > 0) {
      const en = state.language === 'en';
      MailApp.sendEmail({to:data.email, replyTo:LNH_GOOGLE.recipient, name:'La Nature et l’Humain',
        subject:en ? 'Membership application received | La Nature et l’Humain' : 'Demande d’adhésion reçue | La Nature et l’Humain',
        body:en ? 'Your membership application has been recorded.\nReference: ' + state.reference + '\n\nThe association will review it and contact you. This receipt does not constitute membership approval.\n\nLa Nature et l’Humain\n' + LNH_GOOGLE.site
          : 'Ta demande d’adhésion a été enregistrée.\nRéférence : ' + state.reference + '\n\nL’association examinera ton dossier et te contactera. Cet accusé de réception ne vaut pas validation de ton adhésion.\n\nLa Nature et l’Humain\n' + LNH_GOOGLE.site});
      state.applicant = true; write_(folder, 'etat.json', state);
    }
  } catch (error) {
    // Record stays safe; hourly trigger retries unsent notices. No private logs.
  }
}

function escapeHtml_(value) {
  return String(value).replace(/[&<>"']/g, ch => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));
}

// Two parts, normally two A4 pages; long entries may flow onto additional pages.
// Technical import data stays in private Drive. Whitespace is normalized only
// for print, so repeated newlines cannot force hundreds of near-empty pages.
function applicationHtml_(data, state) {
  const text = value => escapeHtml_(String(value || 'Non renseigné').replace(/\s+/g, ' ').trim());
  const row = (label, value) => '<tr><th>' + label + '</th><td>' + text(value) + '</td></tr>';
  const categories = {actif:'Membre actif', sympathisant:'Membre sympathisant', institutionnel:'Membre institutionnel'};
  const date = Utilities.formatDate(new Date(state.receivedAt), 'Africa/Porto-Novo', 'dd/MM/yyyy à HH:mm') + ' (Bénin, UTC+1)';
  const header = '<table class="brand"><tr><td style="width:65px"><img width="58" height="58" src="' + LNH_GOOGLE.site + '/adhesion/assets/logo.png" alt=""></td><td><strong>La Nature et l’Humain</strong><div class="slogan">RÉSEAUX · PARTENARIATS · SOLUTIONS</div></td></tr></table>';
  const reference = '<div class="ref">Référence du dossier : ' + escapeHtml_(state.reference) + '<br>Date de réception : ' + escapeHtml_(date) + '</div>';
  const footer = part => '<div class="footer">Document confidentiel · Usage interne à l’association · Partie ' + part + ' / 2<br>www.lanatureetlhumain.org · ' + LNH_GOOGLE.recipient + '</div>';
  return '<!doctype html><html lang="fr"><head><meta charset="utf-8"><style>' +
    '@page{size:A4;margin:16mm 17mm}body{font:10pt/1.4 Arial,sans-serif;color:#252525;margin:0}' +
    'table{border-collapse:collapse;width:100%;table-layout:fixed}td,th{vertical-align:top;word-wrap:break-word;overflow-wrap:break-word}' +
    '.brand{border-bottom:1px solid #dedbd4;margin-bottom:18px}.brand td{padding:0 0 12px}.brand strong{font-size:18pt;font-weight:normal;color:#202020}.slogan{font-size:8pt;color:#666660;letter-spacing:1.3px;margin-top:5px}' +
    'h1{font-size:23pt;font-weight:normal;color:#202020;margin:0 0 10px}h2{font-size:12pt;color:#303030;margin:19px 0 8px;border-bottom:1px solid #dedbd4;padding-bottom:5px;page-break-after:avoid}tr{page-break-inside:avoid}' +
    '.ref{font-size:8pt;color:#555550;word-wrap:break-word}.status{background:#f6f4ef;border-left:3px solid #4b9824;padding:10px 12px;margin:14px 0;font-size:9pt}' +
    '.fields th{width:30%;text-align:left;font-weight:normal;color:#555550}.fields th,.fields td{border-bottom:1px solid #e5e3de;padding:7px 8px 7px 0}' +
    '.portrait{text-align:right;width:100px}.portrait img{max-width:90px;max-height:120px}.small{font-size:8pt;color:#555550}' +
    '.message{white-space:normal;word-wrap:break-word;overflow-wrap:break-word;font-size:10pt;line-height:1.4;min-height:48px}' +
    '.footer{font-size:8pt;color:#555550;border-top:1px solid #dedbd4;margin-top:22px;padding-top:8px}.page2{page-break-before:always}.note{font-size:9pt}.admin{font-size:9pt;border:1px solid #dedbd4;padding:10px 12px;margin-top:17px;page-break-inside:avoid}' +
    '</style></head><body>' + header + '<h1>Demande d’adhésion</h1>' + reference +
    '<div class="status">Demande enregistrée · En attente d’examen<br>L’adhésion est soumise à l’examen du dossier et à la validation de l’association.</div>' +
    '<h2>01. Identité du demandeur</h2><table><tr><td><table class="fields">' + row('Nom', data.last_name) + row('Prénom(s)', data.first_name) + '</table></td>' +
    '<td class="portrait"><img src="data:' + data.photo.mime + ';base64,' + data.photo.base64 + '" alt="Photographie du demandeur"><div class="small">Photographie fournie</div></td></tr></table>' +
    '<h2>02. Coordonnées</h2><table class="fields">' + row('E-mail', data.email) + row('Téléphone', data.phone) + row('Adresse', data.address) + row('Ville', data.city) + row('Pays', data.country) + '</table>' +
    '<h2>03. Catégorie d’adhésion sollicitée</h2><table class="fields">' + row('Catégorie sollicitée', categories[data.category] || data.category) + row('Profession déclarée', data.profession) + '</table>' +
    '<p class="small">L’association détermine la fonction figurant sur la carte de membre, indépendamment de la profession déclarée.</p>' + footer(1) +
    '<div class="page2">' + header + '<h1>Examen de la demande</h1>' + reference +
    '<h2>04. Motivation</h2><div class="message">' + text(data.motivation) + '</div>' +
    '<h2>05. Consentement et pièces du dossier</h2><p class="note">Le demandeur a exprimé son consentement au traitement de ses données personnelles aux fins d’examen de sa demande, de gestion de son adhésion et d’établissement de sa carte de membre.</p>' +
    '<table class="fields">' + row('Consentement recueilli', 'Confirmé dans le formulaire') + row('Notice de confidentialité', data.consent_version) + row('Date de réception', date) +
    row('Pièces du dossier', 'Formulaire de demande au format PDF et photographie jointe à l’email.') + '</table>' +
    '<p class="small">Le consentement est recueilli par déclaration dans le formulaire. Il ne constitue ni une signature manuscrite ni une vérification de l’identité du demandeur.</p>' +
    '<div class="admin"><strong>Examen réservé à l’association</strong><p>Fonction attribuée : __________________________________________</p><p>Décision et observations : _____________________________________</p><p>Nom du responsable et date : __________________________________</p><span class="small">À compléter par un responsable habilité. La décision et, le cas échéant, la confirmation du paiement sont enregistrées dans l’administration privée. Ce document n’attribue aucun numéro de membre.</span></div>' + footer(2) + '</div></body></html>';
}

function applicationPdf_(folder, data, state) {
  const name = 'demande-adhesion-' + state.reference + '.pdf';
  const existing = folder.getFilesByName(name);
  if (existing.hasNext()) return existing.next().getBlob();
  const pdf = HtmlService.createHtmlOutput(applicationHtml_(data, state)).getAs('application/pdf').setName(name);
  return folder.createFile(pdf).getBlob();
}

function relancerNotifications() {
  owner_();
  const lock = LockService.getScriptLock();
  if (!lock.tryLock(1000)) return;
  try {
    const id = PropertiesService.getScriptProperties().getProperty('LNH_FOLDER_ID');
    if (!id) return;
    const folders = DriveApp.getFolderById(id).getFolders();
    let attempted = 0;
    const start = Date.now();
    while (folders.hasNext() && attempted < 20 && Date.now() - start < 120000 && MailApp.getRemainingDailyQuota() > 0) {
      const folder = folders.next();
      const state = read_(folder, 'etat.json');
      if (state && (!state.admin || !state.applicant)) { notify_(folder, state); attempted++; }
    }
  } finally { lock.releaseLock(); }
}

function receipt_(ok, language, reference, notifications) {
  const en = language === 'en';
  const recorded = ok && reference;
  const title = recorded ? (en ? 'Application received' : 'Demande reçue') : ok ? (en ? 'Membership' : 'Adhésion') : (en ? 'Sending could not be confirmed' : 'L’envoi n’a pas pu être confirmé');
  const text = recorded ? (en ? 'Your application and photo have been recorded. The association will review your application.' : 'Ton dossier et ta photo ont été enregistrés. L’association examinera ta demande.')
    : ok ? (en ? 'Use the membership form on our official website.' : 'Utilise le formulaire d’adhésion sur notre site officiel.')
    : (en ? 'Return to the form and try again. If you have already received a receipt email, do not send it again. Otherwise contact the association if the problem persists.' : 'Reviens au formulaire et réessaie. Si tu as déjà reçu un accusé par email, ne renvoie pas le dossier. Sinon, contacte l’association si le problème persiste.');
  const escape = value => String(value).replace(/[&<>"']/g, ch => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));
  const notification = !recorded ? '' : notifications === 'sent' ? (en ? 'A receipt email has been sent. Check your spam folder if needed.' : 'Un accusé de réception a été envoyé par email. Vérifie les courriers indésirables si nécessaire.')
    : (en ? 'Your application is saved. Email notices are pending and will be retried automatically.' : 'Ton dossier est enregistré. Les notifications par email sont en attente et seront réessayées automatiquement.');
  const html = '<!doctype html><html lang="' + (en?'en':'fr') + '"><head><base target="_top"><meta name="viewport" content="width=device-width,initial-scale=1"><style>body{margin:0;font:16px/1.6 Arial,sans-serif;color:#263331;background:#f6f4ef}header{background:#075889;color:white;padding:20px}main{max-width:650px;margin:40px auto;background:white;padding:30px}h1{font-weight:400;font-size:30px}a{color:#075889}small{display:block;letter-spacing:.08em}p{overflow-wrap:anywhere}@media(max-width:700px){main{margin:20px 12px;padding:22px}}</style></head><body><header>La Nature et l’Humain<small>RÉSEAUX · PARTENARIATS · SOLUTIONS</small></header><main><img src="' + LNH_GOOGLE.site + '/adhesion/assets/logo.png" width="70" height="70" alt="Logo La Nature et l’Humain"><h1>' + title + '</h1><p>' + text + '</p>' + (recorded ? '<p>' + (en?'Reference: ':'Référence : ') + escape(reference) + '</p><p>' + notification + '</p>' : '') + '<p><a href="mailto:' + LNH_GOOGLE.recipient + '">' + LNH_GOOGLE.recipient + '</a></p><p><a href="' + LNH_GOOGLE.site + '/adhesion/?lang=' + (en?'en':'fr') + '">' + (en?'Back to form':'Retour au formulaire') + '</a> · <a href="' + LNH_GOOGLE.site + '/">' + (en?'Website':'Site internet') + '</a></p></main></body></html>';
  return HtmlService.createHtmlOutput(html).setTitle(title).addMetaTag('viewport','width=device-width, initial-scale=1');
}
