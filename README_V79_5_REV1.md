# Sistema de Gestão Autopass — V79.5 REV1

Base: V79.5.

## Correção RH / APT
Na V79.5 a tela `/rh/apt` continuava sendo construída somente a partir dos registros existentes em `apt_records`. Por isso, ao filtrar uma empresa como **Arrow IT Soluções**, apareciam apenas colaboradores que já possuíam APT cadastrada.

### Ajuste
- A tela passa a considerar também os colaboradores ativos do **Cadastro de Usuários**.
- Colaborador ativo sem APT aparece com situação **SEM APT / Cadastro pendente**.
- O filtro de empresa passa a utilizar também as empresas do Cadastro de Usuários, não somente as existentes em registros de APT.
- Para colaborador sem APT, foi incluída ação **Cadastrar APT**, abrindo o modal já vinculado ao usuário e empresa corretos.
- Nenhuma APT é criada automaticamente.
- Registros existentes, PDFs, datas, status e histórico permanecem preservados.
- Filtros específicos de documento/linha continuam trabalhando sobre registros efetivos de APT; linhas “SEM APT” aparecem apenas quando o contexto permite esse tipo de pendência.

## Observação
Este ajuste é coerente com a V79.5, em que APT válida deixou de ser obrigatória para a alocação inicial Arrow. A tela de RH passa a mostrar também quem ainda precisa regularizar/cadastrar APT.
