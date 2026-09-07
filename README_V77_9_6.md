# V77.9.6 — Performance, dashboards e gestão de estoque

## Performance
- Dashboard de Bobinas: elimina consultas N+1 de estoque/fotos por leitura.
- Saldos de armários/estoques são carregados em lote.
- Mantém as regras funcionais e a base oficial ATM validadas na V77.9.5.

## Dashboards
- Dashboard Bobinas incluída no cadastro de dashboards nativos e na Configuração de Dashboards, podendo ser ordenada junto às demais.
- Inclusão de versão embed da Dashboard Bobinas para a Central de Inteligência.
- Dashboard ATM: botão Exportar ATM reforçado e associado ao exportador já existente.
- POS e Bloqueio mantêm o botão Exportar com respeito aos filtros do recorte.

## Estoque Field / Armários
- Nova permissão: `field.stock_manage` — Alterar estoque consolidado / armários / bobinas.
- ADM e Gestor recebem a permissão por padrão; ela também aparece na matriz de permissões de usuários/perfis.
- Usuários com a permissão podem incluir itens não existentes diretamente na Visão de Estoque.
- Campos de inclusão: código, descrição, categoria, unidade, ponto de estoque, quantidade boa, quantidade ruim e observação.
- Usuários autorizados podem editar diretamente os saldos de cada item em cada estoque/armário.
- Ajustes exigem justificativa e geram movimento/auditoria.
- O mesmo controle de permissão protege os ajustes administrativos de bobinas em ATM e armários.

## Sobre / histórico
- Histórico recente reorganizado para eliminar blocos desalinhados e duplicações visuais.
