/* Normal HTTPS form POST: never treat an opaque no-cors response as success. */
(() => {
  const pattern = /^https:\/\/script\.google\.com\/macros\/s\/[A-Za-z0-9_-]+\/exec$/;
  function submit(application, endpoint, language, requestId, startedAt) {
    if (!pattern.test(endpoint)) throw new Error('Service d’envoi indisponible.');
    const form = document.createElement('form');
    form.method = 'POST'; form.action = endpoint; form.target = '_self'; form.hidden = true;
    const values = {request:JSON.stringify({format:'lnh-membership-request',version:1,application}),
      language:language === 'en' ? 'en' : 'fr', requestId, startedAt:String(startedAt)};
    for (const [name,value] of Object.entries(values)) {
      const input = document.createElement('input'); input.type = 'hidden'; input.name = name; input.value = value;
      form.append(input);
    }
    document.body.append(form);
    form.submit();
    form.remove();
  }
  const helpers = {submit, validEndpoint:value => pattern.test(value)};
  if (typeof module !== 'undefined') module.exports = helpers;
  else window.LNH_DIRECT = helpers;
})();
