# Inventário Autopass — V82.13 ENXUTA

Correções de estabilização de perfis e permissões:

- Importação de configurações aceita tanto o modelo `COLABORADORES_CONFIG` quanto a planilha `Usuários e acessos`.
- Correlação de usuário por `user_id`; fallback por `Código` (user_code) e depois `Login/Usuário`.
- Reconhece permissões nos cabeçalhos `PERM | ...` e também `Grupo > Permissão`.
- Arquivo incompatível deixa de provocar HTTP 500; a tela informa o motivo da rejeição.
- Importação de permissões individuais desvincula perfil configurável quando necessário, evitando que o perfil sobrescreva imediatamente a alteração importada.
- Edição individual de permissões deixa de depender do nome hardcoded `manager`; usuários com `users.config.manage` podem persistir a matriz conforme a permissão concedida.
- Salvamento de Perfis & Permissões confirma a persistência no banco antes de informar sucesso e registra auditoria.
- Mantidas as correções da V82.12 para múltiplas APT/PT e herança de NR10/NR35/ASO/Integração.
