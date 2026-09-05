# Sistema de Gestão — V77.1

## Bobinas / Bobinômetro
- Dashboard visual alinhada ao esboço aprovado, com cards coloridos e leitura executiva.
- ATM selecionada por Operadora > Linha > Estação > Terminal.
- Percentual da bobina instalada em passos de 10% (100% = nova/completa).
- Reserva controlada por ATM, não por estação.
- Foto obrigatória por leitura, com retenção configurável (padrão 7 dias).
- Importação da planilha atual de bobinas e preservação de saldo legado não localizado.
- Conciliação por inventário permite zerar formalmente saldo legado não encontrado, mantendo auditoria.

## Armários e Estoque Field
- Armários são pontos de estoque existentes apenas em localidades cadastradas/importadas.
- Aba `Armários` da planilha de bobinas: 1 caixa = 6 bobinas; bobinas avulsas são somadas.
- M16 tratado como Estoque Central Field.
- Importação da planilha `Controle de estoque field.xlsx`, incluindo M16 e estoques por localidade.
- Saldos BOM/RUIM por item e ponto de estoque.

## Carga do Técnico
- Retirada de material transfere saldo do estoque para a carga individual do técnico.
- A carga permanece pendente até destino/devolução/regularização.
- Uso/destinação exige local, justificativa e foto; pode registrar destino da peça retirada.
- Regularização excepcional é solicitada pelo técnico e depende de aprovação do gestor.

## Ocorrências
- Armário/estoque pode receber ocorrência com foto obrigatória: fechadura, porta, falta de acesso/chave, segurança/avaria ou outro.
