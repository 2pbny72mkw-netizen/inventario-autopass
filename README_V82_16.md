# Inventário Autopass — V82.16 ENXUTA

## Visão Panorâmica
- Reposiciona **Abrir localidade** imediatamente abaixo do bloco de filtros.
- Mantém o mesmo seletor e comportamento existente; alteração apenas de organização da interface.
- **Importar ZIP do WhatsApp** passa a ser exibido somente para o ADM principal.
- O endpoint `POST /api/panoramas/import-whatsapp` também valida ADM no backend e retorna HTTP 403 para outros usuários, inclusive outros perfis Gestor.

## Base
- Continuidade integral da V82.15.
- `APP_RELEASE = V82.16`.
