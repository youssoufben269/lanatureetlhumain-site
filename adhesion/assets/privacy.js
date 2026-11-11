const englishNotice = new URLSearchParams(location.search).get('lang') === 'en';
if (englishNotice) {
  const texts = {
    back: 'Back to the form', eyebrow: 'Membership form privacy notice', title: 'Your personal data',
    intro: 'La Nature et l’Humain uses the information provided to review your application, verify payment, manage your membership, produce your card and keep you informed about your application.',
    fieldsTitle: 'Information requested',
    fields: 'Your first and last names, email, phone number, requested category and a photo are required for review. Address, city, country, profession and motivation are optional. The role printed on your card is assigned by the association. Do not send a national identity document or bank details through this form.',
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
LNH.api('/api/membership/config').then(config => {
  const link = document.querySelector('#contact');
  link.textContent = config.privacy_contact; link.href = 'mailto:' + config.privacy_contact;
  document.querySelector('#version').textContent = config.consent_version;
  document.querySelector('#retention').textContent = englishNotice
    ? `Accepted applications are retained for membership management. Rejected applications become eligible for deletion after ${config.retention_days} days, according to the association’s configured policy. Deletion is carried out by its administrator.`
    : `Les dossiers acceptés sont conservés pour le suivi de l’adhésion. Les dossiers refusés sont éligibles à la suppression après ${config.retention_days} jours, selon la politique configurée par l’association. La suppression est effectuée par son administrateur.`;
}).catch(() => {});
