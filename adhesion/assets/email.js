/* Pure helpers shared by the public form and its checks. No network or storage. */
(() => {
  function prepare(application, recipient, language) {
    if (!/^[^\s<>@\r\n]+@[^\s<>@\r\n]+\.[^\s<>@\r\n]+$/.test(recipient)) throw new Error('Adresse de réception indisponible.');
    if (!application || application.consent !== true || !application.photo?.base64) throw new Error('Dossier incomplet.');
    if (!/^[^\s<>@\r\n]+@[^\s<>@\r\n]+\.[^\s<>@\r\n]+$/.test(application.email || '')) throw new Error('E-mail incorrect.');
    const envelope = { format: 'lnh-membership-request', version: 1, application };
    const en = language === 'en';
    const subject = en ? 'Membership application | La Nature et l’Humain' : 'Demande d’adhésion | La Nature et l’Humain';
    const body = en
      ? `Hello,\n\nI would like to join La Nature et l’Humain. My details and photo are included in the attached membership file.\n\nE-mail: ${application.email}\n\nI consent to the processing of these details to review my application, manage my membership and issue my card.\n\n${application.first_name} ${application.last_name}`
      : `Bonjour,\n\nJe souhaite adhérer à La Nature et l’Humain. Mes informations et ma photo figurent dans le dossier d’adhésion joint à ce message.\n\nE-mail : ${application.email}\n\nJ’accepte le traitement de ces données pour examiner ma demande, gérer mon adhésion et établir ma carte.\n\n${application.first_name} ${application.last_name}`;
    return { envelope, text: JSON.stringify(envelope, null, 2), body,
      mailto: 'mailto:' + recipient + '?subject=' + encodeURIComponent(subject) + '&body=' + encodeURIComponent(body) };
  }
  if (typeof module !== 'undefined') module.exports = { prepare };
  else window.LNH_EMAIL = { prepare };
})();
