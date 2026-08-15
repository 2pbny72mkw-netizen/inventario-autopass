AUTOPASS — HOTFIX V4.1.1

CORRIGE
1. WhatsApp: NameError SequenceMatcher.
2. Centro de Evidências: KPI "Itens confrontados" mostrava método interno do dict.
3. Adiciona botão "Expandir mapa" / "Sair da tela cheia".
4. ESC sai do mapa em tela cheia.
5. Versionamento do manager.js para dashboard-v4-1-1.

IMPORTANTE SOBRE /r2-status
Não digite /r2-status no Console JavaScript.
Abra o endereço /r2-status diretamente no navegador.
A tela de importação mostrou "armazenamento local temporário", portanto o R2 ainda
não está configurado/validado. Para fotos e vídeos persistirem entre deploys, configure
Cloudflare R2 antes da importação definitiva.

TESTE
window.AUTOPASS_MANAGER_VERSION
Esperado: dashboard-v4-1-1

Depois:
- /importar-whatsapp -> Analisar e confrontar
- /evidencias-campo -> KPI Itens deve mostrar número
- /gerencial -> botão Expandir mapa
