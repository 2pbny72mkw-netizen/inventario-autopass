# Sistema de Gestão — V73.1 ENXUTA

Correção e estabilização da V73 após testes operacionais.

## Recarga / TDI
- Base detalhada passa a ser a fonte canônica da atividade e dashboard; não soma mais `Location.expected_validator` à base detalhada.
- Deduplicação operacional de Validador/TDI por tipo, empresa, linha, localidade e identificador.
- Referência esperada para o inventário atual: 629 Validadores + 42 TDI = 671.
- Dashboard devolve também a composição Validador/TDI no resumo para diagnóstico.
- Removido o bloco de tendência/previsão da Dashboard Recarga.

## RH · Equipes
- Filtro de colaborador permanece aplicado após atualizar/consultar a Operação do Dia; só sai ao limpar/trocar o filtro.
- Técnico mais próximo corrigido para consumir corretamente o payload em lista da malha ferroviária e preencher Operadora > Linha > Estação.
- Mapa operacional ampliado, com laterais reduzidas e sem criar scroll horizontal.

## Gestão · Rastreabilidade & Jornada
- Mapa de histórico passa a ocupar a largura útil, no mesmo padrão dimensional do mapa de Equipes.
- Filtros Técnico + Data permanecem acima do mapa e a linha do tempo fica abaixo.
- Autorizações continuam aprováveis/rejeitáveis na mesma tela, acessível pelas notificações.

## Gestão · Resumo dos Links
- Ações explícitas Abrir, Editar e Inativar/Reativar.
- Formulário reutilizado para edição e filtro Ativos/Inativos/Todos.

## RH · APT 2.0
- Importar CSV/XLSX/XLSM e atualizar registros existentes sem duplicar.
- Exportar respeitando os filtros atuais.
- Editar por linha, anexar/substituir PDF e Inativar/Reativar preservando histórico.
- Filtros por colaborador/APT, empresa, linha, vencimento, status do processo e situação Ativo/Inativo/Todos.
- Cards de vencimento clicáveis.
- No módulo Documentos & Materiais do próprio colaborador foi adicionada a aba APT, mostrando nº APT, linha, validade, situação/status e PDF quando disponível.

## Cache / release
- Release `V73.1` e cache-busting atualizado para CSS, GPS, Equipes, Manager e Recarga.
