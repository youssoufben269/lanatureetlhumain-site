(() => {
  const { api, node, labels, money } = LNH;
  const status = document.querySelector('#status'), detail = document.querySelector('#detail');
  let csrf, offset = 0, current, config, busy = false, photoURL, cardURL;
  const display = (message, error = false) => { status.className = 'status ' + (error ? 'error' : 'success'); status.textContent = message; };
  const release = () => { if (photoURL) URL.revokeObjectURL(photoURL); if (cardURL) URL.revokeObjectURL(cardURL); };
  async function loadList() {
    const list = await api('/api/admin/applications?offset=' + offset);
    document.querySelector('#count').textContent = `${list.total} dossier(s) · ${offset + 1} à ${offset + list.items.length}`;
    document.querySelector('#previous').disabled = offset === 0;
    document.querySelector('#next').disabled = offset + 50 >= list.total;
    const container = document.querySelector('#requests'); container.replaceChildren();
    if (!list.items.length) container.append(node('p', 'Aucune demande reçue.', 'hint'));
    list.items.forEach(item => {
      const button = node('button', undefined, 'request' + (current?.id === item.id ? ' selected' : ''));
      button.type = 'button';
      button.append(node('strong', item.first_name + ' ' + item.last_name), node('small', item.email), node('span', labels[item.status], 'badge'));
      button.addEventListener('click', () => select(item.id).catch(error => display(error.message, true)));
      container.append(button);
    });
  }
  async function enter() {
    config = await api('/api/membership/config');
    document.querySelector('#login').hidden = true; document.querySelector('#workspace').hidden = false; document.querySelector('#logout').hidden = false;
    await loadList();
  }
  async function act(action, values = {}) {
    if (busy) return;
    busy = true; detail.querySelectorAll('button').forEach(x => { x.disabled = true; });
    display('Enregistrement en cours…');
    try {
      const result = await api('/api/admin/applications/' + current.id + '/action', { data: { action, version: current.version, ...values }, csrf });
      display(result.card_error || (result.status === 'carte_generee' ? 'Dossier enregistré. La carte est disponible.' : 'Dossier enregistré.'), !!result.card_error);
      await select(result.id); await loadList();
    } catch (error) {
      display(error.message, true);
      if (current) await select(current.id).catch(() => {});
    } finally { busy = false; detail.querySelectorAll('button').forEach(x => { x.disabled = false; }); }
  }
  function actionButton(label, action, values, danger = false) {
    const button = node('button', label, danger ? 'danger' : 'secondary'); button.type = 'button';
    button.addEventListener('click', () => act(action, typeof values === 'function' ? values() : values));
    return button;
  }
  async function select(id) {
    release(); current = await api('/api/admin/applications/' + id);
    const selected = current;
    detail.replaceChildren(node('h2', current.first_name + ' ' + current.last_name));
    detail.append(node('span', labels[current.status], 'badge'));
    const picture = node('img'); picture.className = 'detail-photo'; picture.alt = 'Photo transmise par le demandeur'; detail.prepend(picture);
    try {
      const blob = await api('/api/admin/applications/' + id + '/photo', { binary: true });
      if (current !== selected) return;
      photoURL = URL.createObjectURL(blob); picture.src = photoURL;
    } catch (error) { display(error.message, true); }
    const dl = node('dl');
    const fields = [['Email', current.email], ['Téléphone', current.phone], ['Adresse', current.address], ['Ville / pays', [current.city, current.country].filter(Boolean).join(', ')], ['Profession déclarée', current.profession], ['Fonction attribuée', current.function], ['Catégorie', current.category], ['Motivation', current.motivation], ['Consentement', current.consent_at + ' · ' + current.consent_version], ['Décision', current.approved_at ? 'Approbation enregistrée le ' + current.approved_at : 'À examiner'], ['Paiement', current.payment ? `Confirmé · ${money(current.payment.amount_minor, current.payment.currency)} · ${current.payment.reference}` : 'Non confirmé'], ['Numéro', current.member_number], ['Adhésion / expiration', current.joined_on ? current.joined_on + ' / ' + current.expires_on : 'À attribuer']];
    fields[0][0] = 'E-mail';
    fields.forEach(([title, value]) => { dl.append(node('dt', title), node('dd', value || 'Non renseigné')); }); detail.append(dl);
    if (current.card_error) detail.append(node('p', current.card_error, 'notice'));
    if (current.refusal_reason) detail.append(node('p', 'Motif du refus : ' + current.refusal_reason, 'notice'));
    if (current.status !== 'refusee') {
      if (!current.card_path) {
        const functionForm = node('form');
        const label = node('label', 'Fonction attribuée par l’association *'); label.htmlFor = 'assigned-function';
        const field = node('input'); field.id = 'assigned-function'; field.maxLength = 80; field.required = true; field.value = current.function;
        const save = node('button', 'Enregistrer la fonction', 'secondary'); save.type = 'submit';
        functionForm.append(label, field, node('p', 'Cette fonction sera imprimée sur la carte. La profession déclarée reste distincte.', 'hint'), save);
        functionForm.addEventListener('submit', event => { event.preventDefault(); if (functionForm.reportValidity()) act('function', { function: field.value }); });
        detail.append(functionForm);
      }
      const actions = node('div', undefined, 'actions');
      if (!current.member_number) actions.append(actionButton('Marquer le dossier examiné', 'review'));
      if (!current.approved_at) actions.append(actionButton('Valider la demande', 'approve'));
      if (current.status === 'validee' && !current.card_path) actions.append(actionButton('Réessayer la génération', 'generate'));
      detail.append(actions);
      if (!current.payment) {
        const form = node('form', undefined, 'panel'); form.append(node('h3', 'Confirmer le paiement reçu'));
        if (config.fee_minor === null) form.append(node('p', 'Le droit et la devise doivent être configurés côté serveur avant confirmation.', 'notice'));
        else {
          const label = node('label', `Référence du paiement reçu · ${money(config.fee_minor, config.currency)} *`);
          label.htmlFor = 'payment-reference';
          const field = node('input'); field.id = 'payment-reference'; field.required = true; field.maxLength = 160;
          const checkLabel = node('label');
          const check = node('input'); check.type = 'checkbox'; check.required = true;
          checkLabel.append(check, document.createTextNode(' Je confirme avoir vérifié la réception du paiement.'));
          const submit = node('button', 'Enregistrer le paiement'); submit.type = 'submit';
          form.append(label, field, node('p', 'Indique un numéro de reçu ou de transaction. Cette action ne prélève aucun montant.', 'hint'), checkLabel, submit);
          form.addEventListener('submit', event => { event.preventDefault(); if (form.reportValidity()) act('payment', { reference: field.value, amount_minor: config.fee_minor, currency: config.currency }); });
        }
        detail.append(form);
      }
      const refuseForm = node('form'); refuseForm.append(node('h3', current.member_number ? 'Désactiver cette adhésion' : 'Refuser la demande'));
      const reasonLabel = node('label', 'Motif communiqué au demandeur *'); reasonLabel.htmlFor = 'reason';
      const reason = node('textarea'); reason.id = 'reason'; reason.maxLength = 1000; reason.required = true;
      const confirmLabel = node('label'); const confirm = node('input'); confirm.type = 'checkbox'; confirm.required = true;
      confirmLabel.append(confirm, document.createTextNode(' Je confirme cette décision et la désactivation des accès à la carte.'));
      const refuse = node('button', current.member_number ? 'Désactiver l’adhésion' : 'Refuser la demande', 'danger'); refuse.type = 'submit';
      refuseForm.append(reasonLabel, reason, confirmLabel, refuse);
      refuseForm.addEventListener('submit', event => { event.preventDefault(); if (refuseForm.reportValidity()) act('refuse', { reason: reason.value }); });
      detail.append(refuseForm);
    }
    if (current.card_path && current.status === 'carte_generee') {
      const section = node('section'); section.append(node('h3', 'Carte recto-verso'));
      section.append(node('p', 'Gabarit provisoire : comparer avec la maquette validée avant impression en série.', 'notice'));
      const show = node('button', 'Afficher l’aperçu et télécharger le PDF', 'secondary'); show.type = 'button';
      show.addEventListener('click', async () => {
        try {
          const blob = await api('/api/admin/applications/' + id + '/card', { binary: true });
          if (cardURL) URL.revokeObjectURL(cardURL); cardURL = URL.createObjectURL(blob);
          section.querySelectorAll('.card-gallery,a').forEach(x => x.remove());
          const link = node('a', 'Télécharger le PDF', 'button'); link.href = cardURL; link.download = current.member_number + '.pdf';
          await LNH.preview(blob, section);
          section.append(link);
        } catch (error) { display(error.message, true); }
      }); section.append(show); detail.append(section);
    }
    detail.append(node('h3', 'Historique'));
    const history = node('ol', undefined, 'history');
    current.history.forEach(x => history.append(node('li', x.created_at + ' · ' + (x.action === 'import_email' ? 'Dossier reçu par email' : x.action) + ' · ' + (labels[x.old_status] || 'Création') + ' → ' + labels[x.new_status] + ' · ' + x.actor)));
    detail.append(history);
  }
  document.querySelector('#login').addEventListener('submit', async event => {
    event.preventDefault();
    const button = event.target.querySelector('button'); button.disabled = true;
    try {
      const result = await api('/api/login', { data: { email: document.querySelector('#login-email').value, password: document.querySelector('#login-password').value } });
      csrf = result.csrf; document.querySelector('#login-password').value = ''; display('Connexion établie.'); await enter();
    } catch (error) { display(error.message, true); } finally { button.disabled = false; }
  });
  document.querySelector('#import-form').addEventListener('submit', async event => {
    event.preventDefault();
    const form = event.target, button = form.querySelector('button');
    if (!form.reportValidity()) return;
    button.disabled = true;
    try {
      const file = document.querySelector('#import-file').files[0];
      if (file.size > 4_400_000) throw new Error('Le dossier dépasse la taille maximale autorisée.');
      let request;
      try { request = JSON.parse(await file.text()); } catch { throw new Error('Le fichier ne contient pas un dossier lisible.'); }
      const member = await api('/api/admin/applications/import', {data:{request},csrf});
      form.reset(); offset = 0;
      await loadList(); await select(member.id);
      display('Dossier importé. Vérifie les informations et la photo avant toute validation.');
    } catch (error) { display(error.message, true); } finally { button.disabled = false; }
  });
  document.querySelector('#logout').addEventListener('click', async () => {
    try { await api('/api/logout', { data: {}, csrf }); release(); location.reload(); } catch (error) { display(error.message, true); }
  });
  document.querySelector('#refresh').addEventListener('click', () => loadList().catch(error => display(error.message, true)));
  document.querySelector('#previous').addEventListener('click', () => { offset = Math.max(0, offset - 50); loadList().catch(error => display(error.message, true)); });
  document.querySelector('#next').addEventListener('click', () => { offset += 50; loadList().catch(error => display(error.message, true)); });
  api('/api/session').then(async result => { if (result.authenticated) { csrf = result.csrf; await enter(); } }).catch(error => display(error.message, true));
})();
