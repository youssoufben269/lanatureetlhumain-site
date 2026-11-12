const englishNotice = new URLSearchParams(location.search).get('lang') === 'en';
if (englishNotice) {
  const texts = {
    back: 'Back to the form', eyebrow: 'Membership form privacy notice', title: 'Your personal data',
    intro: 'La Nature et l’Humain uses the information provided to review your application, verify payment, manage your membership, produce your card and keep you informed about your application.',
    fieldsTitle: 'Information requested',
    fields: 'Your first and last names, email, phone number, requested category, motivation and a photo are required for review. Address, city, country and profession are optional. The role printed on your card is assigned by the association. Do not send a national identity document or bank details through this form.',
    accessTitle: 'Access and security',
    access: 'Your contact details and photo are restricted to authorised administrators. Files are stored in private server storage. The QR code opens the official website; if individual verification is enabled, it shows only the number and whether the card is active. The PDF is accessible to the administration and through a temporary private link.',
    retentionTitle: 'Retention and requests',
    retention: 'Applications are retained for membership management. Contact the association for its applicable retention policy.',
    rights: 'You may request access to, correction or deletion of your data, or withdraw consent, by writing to',
    obligations: 'The association will explain which records may need to be retained for its management obligations.',
    scope: 'This notice covers the membership form.'
  };
  document.documentElement.lang = 'en';
  document.title = 'Personal data | La Nature et l’Humain';
  document.querySelectorAll('[data-t]').forEach(node => { node.textContent = texts[node.dataset.t]; });
}
document.querySelector('#back').href = './?lang=' + (englishNotice ? 'en' : 'fr');
document.querySelector('.brand').href = '../?lang=' + (englishNotice ? 'en' : 'fr');
if (['email','google'].includes(window.LNH_MEMBERSHIP_MODE)) {
  document.querySelector('[data-t="intro"]').textContent = englishNotice
    ? 'La Nature et l’Humain uses the application sent by email to review your request, manage membership and produce your card. Completing the form alone sends nothing: you download the application file and send it through your own email app.'
    : 'La Nature et l’Humain utilise le dossier transmis par email pour examiner votre demande, gérer votre adhésion et produire votre carte. Remplir le formulaire ne transmet rien : vous téléchargez votre dossier et l’envoyez depuis votre propre messagerie.';
  document.querySelector('[data-t="access"]').textContent = englishNotice
    ? 'Your details and photo are contained in the application file prepared on your device. Once you attach and send it, they are transmitted through email to the association. Authorised staff import the file into their private local administration. Your card is sent to you by the association after approval and payment confirmation. The QR code opens the official website.'
    : 'Vos informations et votre photo figurent dans le dossier préparé sur votre appareil. Lorsque vous le joignez et l’envoyez, elles sont transmises par email à l’association. Les responsables autorisés importent ce dossier dans leur administration locale privée. L’association vous transmet votre carte après validation et paiement confirmé. Le QR renvoie au site officiel.';
  if (window.LNH_MEMBERSHIP_MODE === 'google') {
    document.querySelector('[data-t="intro"]').textContent = englishNotice
      ? 'Clicking Send transmits your application and photo to the association through Google Apps Script. They are saved in its private Google Drive space to review your application, manage membership and produce your card.'
      : 'Le bouton Envoyer transmet votre dossier et votre photo à l’association par Google Apps Script. Ils sont enregistrés dans son espace Google Drive privé pour examiner votre demande, gérer votre adhésion et produire votre carte.';
    document.querySelector('[data-t="access"]').textContent = englishNotice
      ? 'Google processes the transfer, storage and email notices on behalf of the association. Access to files is restricted to authorised staff. The association receives an email with your file, and a receipt is sent to your email address. Staff import the file into the private local administration. No application or photo is published on GitHub. Your card is issued after approval and confirmed payment. The QR opens the official website.'
      : 'Google assure la transmission, le stockage et les notifications par email pour le compte de l’association. Les fichiers sont réservés aux responsables autorisés. L’association reçoit votre dossier par email et un accusé est adressé à votre adresse email. Les responsables importent le dossier dans l’administration locale privée. Aucun dossier ni aucune photo n’est publié sur GitHub. La carte est délivrée après validation et paiement confirmé. Le QR ouvre le site officiel.';
  }
  fetch('settings.json', {cache:'no-store'}).then(response => response.json()).then(settings => {
    document.querySelector('#contact').textContent = settings.emailRecipient;
    document.querySelector('#contact').href = 'mailto:' + settings.emailRecipient;
    document.querySelector('#version').textContent = window.LNH_MEMBERSHIP_MODE === 'google' ? settings.directConsentVersion : settings.consentVersion;
  }).catch(() => {});
} else LNH.api('/api/membership/config').then(config => {
  const link = document.querySelector('#contact');
  link.textContent = config.privacy_contact; link.href = 'mailto:' + config.privacy_contact;
  document.querySelector('#version').textContent = config.consent_version;
  document.querySelector('#retention').textContent = englishNotice
    ? `Accepted applications are retained for membership management. Rejected applications become eligible for deletion after ${config.retention_days} days, according to the association’s configured policy. Deletion is carried out by its administrator.`
    : `Les dossiers acceptés sont conservés pour le suivi de l’adhésion. Les dossiers refusés sont éligibles à la suppression après ${config.retention_days} jours, selon la politique configurée par l’association. La suppression est effectuée par son administrateur.`;
}).catch(() => {});
