# V74.1 — Pessoas, Configuração em Massa e Governança Documental

## Escopo consolidado

1. Dashboard EMV
- Progresso por estação e produtividade por técnico passam a usar barras horizontais legíveis, com nomes, volumes e percentuais alinhados.

2. Cadastro / Configurações de Usuários
- O grande formulário deixa de ocupar a tela principal e abre pelo botão **Incluir novo colaborador** em modal.
- Lista de colaboradores ganha **Recolher / Expandir lista**.
- Novos controles no perfil: **Acesso Metrô**, **Acesso CPTM** e **Acesso Motiva (APT)**.
- `user_id` permanece a chave mestre.
- Novas permissões: visualizar e gerenciar configurações de usuários.

3. Matriz Excel de configurações
- Exportação dinâmica de todos os colaboradores e permissões atuais.
- Colunas de Metrô/CPTM/Motiva, GPS, histórico GPS, jornada e matriz de permissões.
- Importação por `user_id` com regra: **SIM ativa / NÃO desativa / vazio não altera**.
- Prévia obrigatória Atual -> Planilha antes da confirmação.
- Auditoria da importação.

4. Documentos de Acesso Metrô / CPTM
- Não existe mais necessidade de aba administrativa separada "Autorizações de Acesso".
- Participantes vêm dos ticks do cadastro mestre.
- Criação da lista permite revisar/desmarcar participantes da emissão.
- Excel gerado contém user_id, código, nome, empresa, cargo e foto quando disponível.
- Cada emissão cria uma revisão histórica congelada.

5. Pendências e evidência
- Novo Técnico Field com acesso Metrô/CPTM abre pendência de atualização.
- Alteração dos ticks Metrô/CPTM abre pendência.
- Desligamento/arquivamento de colaborador elegível abre pendência.
- Acesso Motiva (APT) sem APT válida cria pendência preventiva.
- Pendência Metrô/CPTM não é encerrada ao gerar o Excel: exige anexar evidência do envio (print/PDF do e-mail), com responsável e data/hora.

6. Arrow
- Matriz passa a ter permissões separadas: Visualizar Arrow, Gerenciar Arrow, Dashboard Arrow e Atendimento Remoto/TeamViewer.
- Menu Arrow depende de permissão e a rota principal também é protegida no backend.

## Checklist pós-deploy
1. Abrir Dashboard EMV e validar os dois gráficos inferiores.
2. Abrir RH > Usuários e confirmar que o formulário não ocupa a tela até clicar em "Incluir novo colaborador".
3. Editar um Técnico Field e marcar Acesso Metrô/CPTM/Motiva.
4. Exportar a matriz Excel, alterar um tick e importar; conferir a prévia antes de aplicar.
5. Abrir Documentos & Materiais > Listas de Acesso Metrô / CPTM.
6. Gerar uma revisão e conferir foto/nome/código no Excel.
7. Anexar uma evidência e confirmar que a pendência correspondente é encerrada.
8. Em Perfis & Permissões, conferir o novo grupo Arrow e as permissões de Configurações de Usuários.
9. Regressão: ATM, EMV, APT, Equipes/GPS, Usuários e Sobre.
