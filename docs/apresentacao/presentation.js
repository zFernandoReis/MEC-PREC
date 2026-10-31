/* Content is embedded at build time so index.html also opens over file://. */
(async () => {
  const chapters = JSON.parse(document.querySelector('#wiki-data').textContent);
  const labels = ['Introdução', 'Stack utilizada', 'Arquitetura do projeto', 'Regras de negócio'];
  const descriptions = ['Contexto, motivação e escopo', 'Tecnologias e justificativas', 'Estrutura, camadas e responsabilidades', 'Disponibilidade do técnico e cálculo do prazo'];
  const slides = document.querySelector('.slides');
  const status = document.querySelector('#load-status');
  const escape = text => text.replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;').replaceAll('"', '&quot;');
  const ids = new Map(chapters.map((chapter, i) => [chapter.file, `wiki-${i}`]));
  chapters.forEach((chapter, i) => {
    const title = labels[i] || chapter.file;
    const step = document.createElement('a');
    step.className = 'step'; step.href = `#/${ids.get(chapter.file)}`;
    step.innerHTML = `<span class="step-number">${String(i + 1).padStart(2, '0')}</span><span><strong>${escape(title)}</strong><small>${escape(descriptions[i] || chapter.file)}</small></span><span class="step-arrow">↗</span>`;
    document.querySelector('#steps').append(step);
    const section = document.createElement('section'); section.id = ids.get(chapter.file); section.className = 'chapter'; section.dataset.title = title;
    section.innerHTML = `<header class="chapter-header"><div><p class="eyebrow">ETAPA ${String(i + 1).padStart(2, '0')} / ${String(chapters.length).padStart(2, '0')}</p><h2>${escape(title)}</h2></div><a class="source-link" href="./${encodeURIComponent(chapter.file)}" target="_blank" rel="noopener">Arquivo original ↗</a></header><div class="chapter-layout"><nav class="chapter-toc" aria-label="Tópicos de ${escape(title)}"><a class="back-menu" href="#/menu">← Voltar ao menu</a></nav><article class="reading-pane" tabindex="0" aria-label="Conteúdo de ${escape(title)}"></article></div>`;
    const pane = section.querySelector('.reading-pane');
    if (window.marked && window.DOMPurify) pane.innerHTML = DOMPurify.sanitize(marked.parse(chapter.markdown));
    else pane.innerHTML = `<pre>${escape(chapter.markdown)}</pre>`;
    pane.querySelector('h1')?.remove();
    pane.querySelectorAll('h2,h3').forEach((heading, n) => {
      heading.id = `${section.id}-topic-${n}`;
      const link = document.createElement('a'); link.href = `#${heading.id}`; link.textContent = heading.textContent;
      if (heading.tagName === 'H3') link.className = 'subtopic';
      link.addEventListener('click', event => { event.preventDefault(); pane.scrollTop = heading.offsetTop - pane.offsetTop; heading.tabIndex = -1; heading.focus({ preventScroll: true }); });
      section.querySelector('.chapter-toc').append(link);
    });
    pane.querySelectorAll('a[href]').forEach(link => {
      const href = link.getAttribute('href');
      const [file] = href.split('#');
      if (file === 'README.md') { link.href = '#/menu'; link.textContent = 'Menu da apresentação'; }
      else if (ids.has(file)) link.href = `#/${ids.get(file)}`;
      else if (!href.startsWith('#')) {
        if (!/^[a-z][a-z\d+.-]*:/i.test(href) && !href.startsWith('/')) link.setAttribute('href', '../' + href);
        link.target = '_blank'; link.rel = 'noopener noreferrer';
      }
    });
    pane.querySelectorAll('table').forEach(table => { const wrapper = document.createElement('div'); wrapper.className = 'table-scroll'; wrapper.tabIndex = 0; table.replaceWith(wrapper); wrapper.append(table); });
    if (chapter.file === '01-introducao.md' || chapter.file === '03-arquitetura.md') {
      const note = document.createElement('aside'); note.className = 'source-note';
      note.textContent = 'Texto preservado da wiki. As informações refletem a data de elaboração de cada documento e podem não incluir alterações posteriores do projeto.';
      pane.prepend(note);
    }
    slides.append(section);
  });
  document.querySelector('.cover-bottom strong').textContent = chapters.length;
  document.querySelector('#fullscreen').onclick = async () => {
    try { if (document.fullscreenElement) await document.exitFullscreen(); else await document.documentElement.requestFullscreen(); }
    catch { status.hidden = false; status.textContent = 'Tela cheia indisponível neste navegador. Use F11.'; }
  };
  if (window.Reveal) {
    await Reveal.initialize({ width:1280, height:720, margin:.025, hash:true, controls:false, progress:true, center:false, transition:matchMedia('(prefers-reduced-motion: reduce)').matches ? 'none' : 'fade', backgroundTransition:'none', disableLayout:false, overview:true, touch:false, keyboard:{77:() => Reveal.slide(1)}, help:true });
    function update() {
      const index = Reveal.getIndices().h;
      document.querySelector('#page-number').textContent = `${String(index + 1).padStart(2,'0')} / ${String(chapters.length + 2).padStart(2,'0')}`;
      document.querySelector('#location').textContent = Reveal.getCurrentSlide().dataset.title || (index === 0 ? 'MEC System / Apresentação' : 'Wiki / Roteiro de leitura');
      document.querySelector('#previous').disabled = Reveal.isFirstSlide();
      document.querySelector('#next').disabled = Reveal.isLastSlide();
    }
    document.querySelector('#previous').onclick = () => Reveal.prev();
    document.querySelector('#next').onclick = () => Reveal.next();
    Reveal.on('slidechanged', update); update();
    status.hidden = true;
  } else {
    document.body.classList.add('fallback');
    document.querySelectorAll('a[href^="#/"]').forEach(link => link.href = link.getAttribute('href').replace('#/', '#'));
    document.querySelector('.toolbar').hidden = true;
    status.textContent = 'Sem conexão com as bibliotecas. Conteúdo disponível em leitura contínua; conecte-se e recarregue para apresentar.';
  }
  if (!window.marked || !window.DOMPurify || !window.mermaid) {
    status.hidden = false; status.textContent = 'Algumas bibliotecas não carregaram. O conteúdo está disponível; conecte-se e recarregue para a formatação e os diagramas.';
  }
  if (window.mermaid) {
    mermaid.initialize({ startOnLoad:false, securityLevel:'strict', theme:'neutral', themeVariables:{background:'transparent'}, suppressErrorRendering:true });
    // Render in a visible staging area: hidden Reveal slides have no usable SVG dimensions.
    const staging = document.createElement('div'); staging.style.cssText = 'position:absolute;left:-20000px;top:0;width:1100px;'; document.body.append(staging);
    let n = 0;
    for (const code of document.querySelectorAll('code.language-mermaid')) {
      const source = code.textContent;
      const figure = document.createElement('figure'); figure.className = 'diagram';
      let heading = code.parentElement.previousElementSibling;
      while (heading && !heading.matches('h2,h3')) heading = heading.previousElementSibling;
      const diagramTitle = heading?.textContent || 'Diagrama da wiki';
      try {
        const { svg } = await mermaid.render(`wiki-diagram-${n++}`, source, staging);
        const viewport = document.createElement('div');
        viewport.className = 'diagram-scroll';
        viewport.tabIndex = 0;
        viewport.setAttribute('role', 'region');
        viewport.setAttribute('aria-label', `${diagramTitle}. Área com rolagem horizontal.`);
        viewport.innerHTML = svg;
        const drawing = viewport.querySelector('svg');
        drawing.setAttribute('role', 'img');
        drawing.setAttribute('aria-label', diagramTitle);
        // Keep the native drawing scale instead of shrinking dense labels to fit the column.
        const nativeWidth = drawing.viewBox.baseVal.width;
        if (nativeWidth > 0) drawing.style.minWidth = `${Math.ceil(nativeWidth)}px`;
        const caption = document.createElement('figcaption');
        caption.textContent = `${diagramTitle} · Para desenhos largos, use a barra de rolagem abaixo ou as setas com o diagrama selecionado.`;
        figure.append(caption, viewport);
      } catch (error) {
        const message = document.createElement('p'); message.textContent = 'Não foi possível renderizar este diagrama. Consulte a definição abaixo.'; figure.append(message);
        console.warn('Diagrama não renderizado:', error);
      }
      if (!figure.querySelector('svg')) {
        const fallback = document.createElement('pre'); fallback.textContent = source; figure.append(fallback);
      }
      code.parentElement.replaceWith(figure);
    }
    staging.remove();
  }
})();
