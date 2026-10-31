# Apresentação HTML da wiki

Abra `index.html` em um navegador com acesso à internet. Não é necessário iniciar a API ou instalar dependências. Reveal.js 5.2.1, Marked 15.0.12, DOMPurify 3.2.6 e Mermaid 11.4.1 são carregados pelo CDN jsDelivr. Sem conexão, a página oferece uma leitura contínua dos textos, sem os recursos completos da apresentação.

A capa é seguida por um menu com quatro etapas: introdução, stack, arquitetura e regras de negócio. O índice da wiki, o modelo de dados e o relatório de conformidade não integram a apresentação. Cada etapa abre o conteúdo do arquivo, com rolagem, índice de tópicos, tabelas e diagramas estáticos integrados à página, com fundo transparente. Os links entre capítulos navegam pela apresentação, e os links para o índice retornam ao menu. Referências ao código abrem os arquivos locais em outra aba, conforme o suporte do navegador.

- Clique nas etapas ou use os botões e as setas esquerda/direita para mudar de slide.
- Pressione **M** ou clique em **Menu** para voltar ao roteiro.
- Use a rolagem sobre o texto para ler capítulos longos.
- Os diagramas preservam a escala original para manter os rótulos legíveis. Em desenhos largos, use a barra horizontal ou selecione o diagrama com Tab e use as setas.
- Use **Tela cheia** para apresentar e **Esc** para a visão geral de slides.

A fonte da apresentação são os arquivos Markdown diretamente na pasta `docs/apresentacao/`: `01-introducao.md`, `02-stack.md`, `03-arquitetura.md` e `05-regras-de-negocio.md`. O gerador não lê os capítulos da pasta pai `docs/`. Este README não é incluído como slide.

O HTML contém uma cópia desses documentos. Depois de editar os Markdown de `docs/apresentacao/`, atualize a apresentação, a partir da raiz do repositório, com:

```powershell
node scripts/build_wiki_presentation.mjs
```

Edite `template.html`, `presentation.css` e `presentation.js` para mudar a apresentação. `index.html` é gerado. A geração usa apenas módulos nativos do Node.js.

A apresentação preserva as afirmações e datas dos documentos, incluindo diferenças entre análises. Não representa uma nova auditoria do código.

Referências das bibliotecas: [inicialização do Reveal.js](https://revealjs.com/initialization/), [configuração](https://revealjs.com/config/) e [renderização Mermaid](https://mermaid.js.org/config/usage.html).
