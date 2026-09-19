# Android A0.3 REV1 + backend V82.36 — integração de observações (pré-homologação)

Pacote incremental. **Não é A0.3 final / fotos offline não implementadas.**

Backend: substituir app.py e templates/arrow_v75.html na raiz do projeto atual. Preserve banco e demais arquivos. Android: abrir o projeto fonte no Android Studio, compilar e instalar por cima, sem limpar dados.

Alterações: Iniciar Arrow também permite observação; observações das ações Mobile são persistidas sem prefixo no histórico Arrow, com captured_at em created_at; retorno por evento inclui observation_saved para diagnóstico; modal Web identifica #ID e esclarece que o campo é para a próxima ação, enquanto textos anteriores estão no histórico. Build 9.

Não executado: compilação Android, deploy Render, teste de foto/evidência, teste integrado de gravação com banco de produção. Não distribuir aos técnicos.
