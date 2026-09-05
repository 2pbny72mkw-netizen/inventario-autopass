# V75 CONSOLIDADA — Operação, Pessoas & Materiais

Base: V74.1 validada em campo.

## Fechamento V74.1 REV1
- Locais de atuação por habilita/desabilita (Metrô, CPTM, Linha 4, Linha 5, Outros).
- Acessos Metrô, CPTM e Motiva (APT) no perfil do colaborador.
- CPF e RG adicionados ao cadastro mestre para documentos operacionais.
- Matriz Excel com perfil em português, CPF, RG, locais e configurações.
- Lista oficial Metrô/CPTM em PDF com logo Autopass.
- PDF obrigatório para todos os habilitados; geração bloqueada se FORNECEDOR, NOME, CPF, RG ou FOTO estiverem faltando.
- Revisão histórica e evidência obrigatória de envio preservadas.

## Arrow V75
- Agenda e atividades Arrow.
- Alocação por técnico/user_id.
- Elegibilidade por acesso Metrô/CPTM/Motiva (APT).
- Status Planejada / Em andamento / Concluída / Cancelada.
- Atendimento remoto com ID TeamViewer.
- Dashboard com totais, planejadas, em andamento, concluídas e remotas.
- Permissões separadas: visualizar, gerenciar, dashboard e remoto.

## Materiais integrados
- Reutiliza o catálogo, kits, entrega/devolução e carga individual já existentes.
- Permite vincular material a uma atividade Arrow.
- Consumíveis geram movimento de consumo ligado à atividade; devolvíveis permanecem rastreados sem baixa automática.

## Banco
Migrações são aditivas. Não remove a tabela antiga de autorizações; ela permanece dormente para compatibilidade.

## Pós-deploy obrigatório
1. Login/menu.
2. Editar usuário e conferir locais/acessos/CPF/RG.
3. Exportar matriz Excel e confirmar perfis em português.
4. Gerar PDF Metrô/CPTM com usuário completo e testar bloqueio com cadastro incompleto.
5. Criar atividade Arrow para Metrô/CPTM/Motiva e validar bloqueio por elegibilidade.
6. Alterar status Arrow e conferir dashboard.
7. Vincular material consumível e devolvível.
8. Regressão: ATM, EMV, Equipes/GPS, APT, Documentos & Materiais, Portal e Financeiro.
