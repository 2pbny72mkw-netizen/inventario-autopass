# Autopass Web V85.23 REV4 — patch enxuto

Correção estrutural de Organização do Menu Principal.

Causa confirmada: o link físico existia, mas o menuLayoutV8522 salvo/gerado não continha
a funcionalidade. O JavaScript reconstruía o menu e descartava o link.

Correção:
- release V85.23 REV4;
- inclui Organização do Menu Principal na estrutura padrão de Gestão;
- repara em memória layouts antigos salvos sem essa identidade;
- preserva ordem, nomes, grupos e permissões existentes;
- mantém /gestao/organizacao-menu;
- não altera a Matriz de Permissões.

Arquivos: app.py, templates/base.html e este README.
