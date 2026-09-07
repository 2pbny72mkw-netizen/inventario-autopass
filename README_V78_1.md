# Sistema de Gestão — V78.1 ENXUTA

Evolução do módulo Engenharia sobre a V78.

- BOM separada visualmente em Itens Nacionais e Itens Importados.
- Cadastro Mestre governa origem, fornecedor, PN do fornecedor e moeda.
- Preço de referência no Cadastro Mestre e preço aplicado/editável na BOM, preparando simulações futuras por volume.
- Edição da BOM restrita às variáveis operacionais: quantidade, grupo, lead time e preço aplicado; dados mestres ficam bloqueados.
- Formação comercial com duas linhas de Big Numbers: unitário e total da quantidade de produção.
- Estudos salvos: abrir e duplicar estudos anteriores; Novo estudo inicia uma nova simulação.
- Excel de formação comercial com índices tributários, percentual/parâmetro, base de cálculo e valor calculado, além da memória de resultados.
- Histórico Sobre atualizado para V78.1.

Arquivos alterados: app.py, templates/engineering.html, templates/about.html, static/engineering_v72.js, static/app.css.
