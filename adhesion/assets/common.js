window.LNH = (() => {
  const base = (window.LNH_API_BASE || '').replace(/\/$/, '');
  async function api(path, { data, csrf, binary = false } = {}) {
    let response;
    try {
      response = await fetch(base + path, {
        method: data === undefined ? 'GET' : 'POST', credentials: 'include', cache: 'no-store',
        headers: { ...(data === undefined ? {} : { 'Content-Type': 'application/json' }), ...(csrf ? { 'X-CSRF-Token': csrf } : {}) },
        body: data === undefined ? undefined : JSON.stringify(data)
      });
    } catch {
      throw new Error('Le service est indisponible. Veuillez réessayer plus tard ou contacter l’association. / Service unavailable. Please try again later.');
    }
    if (!response.ok || !binary) {
      if (!(response.headers.get('content-type') || '').includes('application/json')) {
        throw new Error('Le service d’adhésion doit être activé par l’association. / The membership service is not yet available.');
      }
      const result = await response.json();
      if (!response.ok) throw new Error(result.error || 'La demande a échoué.');
      return result;
    }
    return response.blob();
  }
  const labels = {
    soumise: 'Soumise', en_attente_de_paiement: 'En attente de paiement',
    en_attente_de_validation: 'En attente de validation', validee: 'Validée',
    refusee: 'Refusée', carte_generee: 'Carte générée'
  };
  const node = (tag, value, className) => {
    const element = document.createElement(tag);
    if (value !== undefined) element.textContent = value;
    if (className) element.className = className;
    return element;
  };
  const money = (amount, currency, language = 'fr') => {
    const formatter = new Intl.NumberFormat(language, { style: 'currency', currency });
    return formatter.format(amount / 10 ** formatter.resolvedOptions().maximumFractionDigits);
  };
  async function preview(blob, container) {
    const pdfjs = await import('./pdf.mjs');
    pdfjs.GlobalWorkerOptions.workerSrc = new URL('./pdf-worker.mjs', document.currentScript?.src || new URL('adhesion/assets/common.js', location.origin)).href;
    const pdf = await pdfjs.getDocument({ data: new Uint8Array(await blob.arrayBuffer()), isEvalSupported: false }).promise;
    const gallery = node('div', undefined, 'card-gallery');
    for (let pageNumber = 1; pageNumber <= pdf.numPages; pageNumber++) {
      const page = await pdf.getPage(pageNumber);
      const viewport = page.getViewport({ scale: 2.5 });
      const canvas = node('canvas'); canvas.width = viewport.width; canvas.height = viewport.height;
      canvas.setAttribute('role', 'img'); canvas.setAttribute('aria-label', pageNumber === 1 ? 'Recto de la carte' : 'Verso de la carte');
      const figure = node('figure'); figure.append(canvas, node('figcaption', pageNumber === 1 ? 'Recto' : 'Verso')); gallery.append(figure);
      await page.render({ canvasContext: canvas.getContext('2d'), viewport }).promise;
    }
    container.append(gallery);
    await pdf.destroy();
  }
  return { api, base, labels, node, money, preview };
})();
