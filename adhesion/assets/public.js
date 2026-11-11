(() => {
  const { api } = LNH;
  const form = document.querySelector('#application'), status = document.querySelector('#status');
  const button = document.querySelector('#submit'), photo = document.querySelector('#photo');
  const preview = document.querySelector('#photo-preview');
  let config, imageURL, lang = new URLSearchParams(location.search).get('lang') === 'en' ? 'en' : 'fr';
  const english = {
    topbar: 'International association · Biodiversity · Climate · Sustainable development', home: 'Back to website', eyebrow: 'Membership', title: 'Join the association',
    intro: 'Submit your application and photo. The association reviews your application and assigns your role. Your card is issued after approval and payment confirmation.',
    formTitle: 'Your membership application', required: 'Fields marked * are required.', first: 'First name *', last: 'Last name *', email: 'Email *', phone: 'Phone *', address: 'Address (optional)', city: 'City (optional)', country: 'Country (optional)', profession: 'Profession (optional)', roleHint: 'The role printed on your card is assigned by the association.', category: 'Requested membership category *', loading: 'Loading…', photo: 'Identity photo *', photoHint: 'Recent portrait with an unobstructed face. JPEG or PNG, up to 3 MB, at least 240 × 320 pixels. The photo will be cropped to portrait format.', motivation: 'Message or motivation (optional)', consent: 'I consent to the processing of my data to review my application, manage my membership and issue my card. *', privacy: 'Read the privacy notice', submit: 'Submit my application', next: 'What happens next', cardTitle: 'Your membership card', step1: 'Submit your details and photo.', step2: 'The association reviews your application and assigns your role.', step3: 'Payment of the membership fee is confirmed.', step4: 'Your number and card are created after approval.', noInstant: 'Submitting this form does not constitute acceptance of membership.'
  };
  const french = Object.fromEntries([...document.querySelectorAll('[data-t]')].map(x => [x.dataset.t, x.textContent]));
  function translate() {
    document.documentElement.lang = lang;
    document.title = (lang === 'en' ? 'Join us' : 'Adhérer') + ' | La Nature et l’Humain';
    document.querySelector('[data-t="home"]').href = '../?lang=' + lang;
    document.querySelector('.brand').href = '../?lang=' + lang;
    document.querySelector('[data-t="privacy"]').href = 'confidentialite.html?lang=' + lang;
    preview.alt = lang === 'en' ? 'Your photo preview' : 'Aperçu de ta photo';
    document.querySelectorAll('[data-t]').forEach(x => { x.textContent = lang === 'en' ? english[x.dataset.t] : french[x.dataset.t]; });
    document.querySelector('#language').textContent = lang === 'en' ? 'FR' : 'EN';
    document.querySelector('#language').setAttribute('aria-label', lang === 'en' ? 'Passer en français' : 'Switch to English');
    if (config) {
      const labels = { actif: ['Actif', 'Active member'], sympathisant: ['Sympathisant', 'Supporter'], institutionnel: ['Institutionnel', 'Institutional member'] };
      document.querySelectorAll('#category option').forEach(option => {
        option.textContent = option.value ? (labels[option.value]?.[lang === 'en' ? 1 : 0] || option.value) : (lang === 'en' ? 'Choose a category' : 'Choisir une catégorie');
      });
    }
    if (config) document.querySelector('#fee').textContent = config.fee_minor === null
      ? (lang === 'en' ? 'The fee and payment instructions will be provided after review.' : 'Le montant et les modalités de paiement te seront communiqués après examen.')
      : (lang === 'en' ? 'Membership fee: ' : 'Droit d’adhésion : ') + new Intl.NumberFormat(lang, { style: 'currency', currency: config.currency }).format(config.fee_minor / 10 ** new Intl.NumberFormat(lang, { style: 'currency', currency: config.currency }).resolvedOptions().maximumFractionDigits);
  }
  document.querySelector('#language').addEventListener('click', () => { lang = lang === 'fr' ? 'en' : 'fr'; translate(); });
  translate();
  photo.addEventListener('change', () => {
    if (imageURL) URL.revokeObjectURL(imageURL);
    preview.hidden = true;
    const file = photo.files[0];
    if (!file) return;
    if (!['image/jpeg', 'image/png'].includes(file.type) || file.size > 3_000_000) {
      photo.value = '';
      status.className = 'status error';
      status.textContent = lang === 'en' ? 'Choose a JPEG or PNG image, maximum 3 MB.' : 'Choisis une photo JPEG ou PNG de 3 Mo maximum.';
      return;
    }
    imageURL = URL.createObjectURL(file);
    preview.src = imageURL; preview.hidden = false;
    status.textContent = '';
  });
  form.addEventListener('submit', async event => {
    event.preventDefault();
    if (!config || !form.reportValidity()) return;
    button.disabled = true; status.className = 'status';
    status.textContent = lang === 'en' ? 'Sending…' : 'Envoi en cours…';
    try {
      const file = photo.files[0];
      const encoded = await new Promise((resolve, reject) => {
        const reader = new FileReader(); reader.onload = () => resolve(reader.result.split(',')[1]); reader.onerror = reject; reader.readAsDataURL(file);
      });
      const data = Object.fromEntries(new FormData(form));
      data.photo = { name: file.name, mime: file.type, base64: encoded };
      data.consent = document.querySelector('#consent').checked;
      data.consent_version = config.consent_version;
      const result = await api('/api/membership/applications', { data });
      form.reset(); preview.hidden = true;
      if (imageURL) URL.revokeObjectURL(imageURL);
      status.className = 'status success';
      status.textContent = lang === 'en' ? 'Your application has been received. The association will review the information provided. If this email has already been used, contact us to follow up.' : result.message;
    } catch (error) {
      status.className = 'status error'; status.textContent = error.message;
    } finally { button.disabled = false; }
  });
  api('/api/membership/config').then(result => {
    config = result;
    const select = document.querySelector('#category');
    select.replaceChildren(new Option(lang === 'en' ? 'Choose a category' : 'Choisir une catégorie', ''));
    config.categories.forEach(value => select.add(new Option(value, value)));
    select.disabled = false; button.disabled = false; translate();
  }).catch(error => { status.className = 'status error'; status.textContent = error.message; });
})();
