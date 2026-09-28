# V85.23 REV3 — patch enxuto
Base: V85.23 REV2.

Arquivos alterados:
- app.py
- templates/base.html

Correção:
- reconhece também `administrador` no helper central de acesso;
- exibe Gestão > Organização do Menu Principal para esse perfil;
- mantém /gestao/organizacao-menu;
- não altera banco, dados, CSS, JS ou outros módulos.
