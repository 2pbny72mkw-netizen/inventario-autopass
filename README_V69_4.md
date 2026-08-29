# Sistema de Gestão — V69.4

Versão de consolidação de dashboards, Raio-X e perfis/permissões.

## Principais entregas
- Dashboard Garagem integrado à Central `/gerencial?view=garage` e JS isolado para evitar conflito do identificador `$`.
- Central lateral sem a atividade operacional "Troca Chips Garagem"; permanece apenas Dashboard Garagem.
- Gestão > Configuração de Dashboards: visibilidade, ordem e perfis autorizados para dashboards nativas.
- Gestão > Perfis & Permissões: perfil-base opcional (inclusive Nenhum), edição, ativação/inativação e exclusão quando sem vínculos.
- Perfis personalizados integrados ao cadastro/edição de usuários.
- Raio-X dos Colaboradores: busca, filtros Empresa/Cargo/Situação, cards clicáveis, exportação Excel e modal de detalhamento ao clicar REGULAR/PENDENTE.
- RH > Usuários > Exportar Excel: agora exporta dados cadastrais + todas as subcategorias/permissões efetivas por colaborador (SIM/NÃO), com aba "Legenda de Permissões" e resumo.
- Mantidas correções de schema de `collaborator_documents` e pending-count da V69.3.2.
- Identidade institucional: Sistema de Gestão.

## Testes prioritários após deploy
1. Dashboard > Dashboard Garagem: confirmar preenchimento de KPIs/gráficos e ausência de erro `Identifier '$' has already been declared`.
2. Confirmar que "Troca Chips Garagem" não aparece na lateral da Central.
3. Gestão > Configuração de Dashboards: ocultar/reordenar uma dashboard e validar a lateral.
4. Gestão > Perfis & Permissões: criar perfil com base Nenhum, editar e vincular a usuário permitido.
5. RH > Usuários: confirmar perfil personalizado no combo e exportar Excel; conferir colunas SIM/NÃO até o nível de subcategoria.
6. Documentos & Materiais > Raio-X: testar Cargo/Empresa/Situação, Exportar Excel e clique em PENDENTE para abrir detalhamento.
