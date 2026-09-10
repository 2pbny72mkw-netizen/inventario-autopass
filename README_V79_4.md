# V79.4 — Coleta de Valores

## Escopo
- Monitoramento no padrão Dash 2.0, com linhas coloridas por situação/criticidade.
- ATM clicável abre modal compacto para editar data/hora, declarado, apurado, status e observação.
- Diferença permanece calculada automaticamente como Apurado - Declarado.
- Reagendamento e composição de cédulas recolhidos no mesmo modal.
- Importação de reporte diário por colagem, com prévia antes da gravação, correlação à base mestre e extração de GTV/GTVe.
- Tratamento de recolhido e não recolhido sem criar ATM fora da base mestre.
- Fila de Prioridades com criticidade, dias sem coleta, reincidência, motivo e ação recomendada.
- Mantidos filtros, próxima previsão, Big Numbers financeiros, 10 linhas + Mostrar mais/Recolher linhas e exportação filtrada.

## Implantação
Aplicar os arquivos deste pacote sobre a versão imediatamente anterior. A migração de schema é idempotente e registrada como V79.4-001.
