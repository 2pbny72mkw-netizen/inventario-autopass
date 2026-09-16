# V82.2 — Hotfix Mapeamento ATM

- Corrige a disponibilização da atividade **Field > Mapeamento ATM** no menu.
- ADM/Gestor administrativo mantém acesso integral ao módulo, inclusive para perfis legados que ainda não possuem a nova chave gravada na matriz.
- Demais perfis continuam controlados pela Matriz de Permissões (`field.atm_mapping` / `field.atm_mapping_manage`).
- Preserva a atividade completa da V82: base oficial filtrada inicialmente para ATMs com venda em dinheiro, furos/tampões, acesso interno/externo, observações, GPS e múltiplas fotos por câmera ou galeria.
- Preserva integralmente a correção financeira da V82.1 para `source_hash` duplicado e NULL x zero.
- Release da aplicação atualizado para V82.2.
