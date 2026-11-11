(() => {
  const token = new URLSearchParams(location.hash.slice(1)).get('token');
  history.replaceState(null, '', location.pathname); // Keep the private link out of browser history after opening.
  document.querySelector('#download').addEventListener('click', async event => {
    event.target.disabled = true;
    const status = document.querySelector('#status');
    try {
      const blob = await LNH.api('/api/card-download', { data: { token }, binary: true });
      const url = URL.createObjectURL(blob);
      const link = LNH.node('a', 'Télécharger le PDF', 'button'); link.href = url; link.download = 'carte-membre.pdf';
      const container = document.querySelector('#preview'); container.replaceChildren();
      await LNH.preview(blob, container); container.append(link);
      status.textContent = 'Imprime à 100 %, sans ajustement à la page. Le PDF contient le recto puis le verso.';
      window.addEventListener('pagehide', () => URL.revokeObjectURL(url), { once: true });
    } catch (error) { status.className = 'status error'; status.textContent = error.message; event.target.disabled = false; }
  });
})();
