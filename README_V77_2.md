# V77.2 — Bobinas + Estoque Field — Estabilização

## Correções críticas
- Corrige o bloco de rotas V77.1 que havia sido empacotado com quebras de linha escapadas, fazendo `/api/field-stock/importar` responder 404.
- Importadores passam a validar resposta JSON e exibem erro legível quando o servidor responder HTML/404/500.
- Terminal ATM passa a ser alimentado pela base mestre do sistema (`BaseAsset` e `Inventory`), com histórico de Bobinas apenas como fallback complementar.

## Atividade Bobinas
- GPS capturado no momento do salvamento, com fallback para a última posição da sessão.
- Grava latitude, longitude, precisão, horário da captura e distância até a referência da localidade quando disponível.
- Foto continua obrigatória e com retenção configurável.
- Reserva continua sendo quantidade física dentro da própria ATM.
- Troca de bobina fica registrada explicitamente como evento `TROCA`; inspeção sem troca como `LEITURA`.

## Dashboard
- Mantém o desenho colorido aprovado, com tons mais leves e todo o texto dos cards em branco.
- KPIs de 30 dias: atendimentos, com troca, sem troca e taxa de troca.
- Filtro `Com troca / Sem troca` e histórico identificando quais ATMs tiveram troca.
- Histórico mostra vínculo de GPS quando existente.

## Importação de virada
- `Controle de quantidade de bobinas`: prévia + confirmação; importa leituras das ATMs, saldo legado não localizado e aba `Armários` na mesma operação.
- Regra de armário: 1 caixa = 6 bobinas.
- `Controle de estoque field`: prévia + confirmação; importa M16 e estoques por localidade.
- Armários/localidades são conciliados com o cadastro mestre quando possível.

## Deploy
Pacote ENXUTA: substituir os arquivos enviados, instalar dependências já existentes e reiniciar o serviço. A migração V77.2-001 é aditiva e cria as colunas GPS da tabela de leituras de bobina sem apagar dados.
