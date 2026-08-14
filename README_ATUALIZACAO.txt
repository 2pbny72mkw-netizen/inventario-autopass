PACOTE AUTOPASS - ATUALIZAÇÃO CONSOLIDADA

Substituir no GitHub:
- app.py
- static/technician.js
- static/manager.js
- static/autopass-logo.png
- templates/technician.html

Principais avanços:
- Validador de Recarga com campos específicos (Aplicação, BOM, BU, TOP, Versão)
- preenchimento automático a partir do ativo-base
- ATM / Validador / POS filtrados por tipo
- edição e exclusão de inventário por Gestor
- salvamento local/GPS robusto
- pendências mostram previstos, ativos detalhados, realizados e faltantes
- mapa gerencial V2 preservado
- migrações de banco idempotentes no app.py

Após upload: commit -> Render Live -> Ctrl+F5.
Testes: /health, Técnico ATM, Validador, Editar/Excluir, mapa gerencial.
