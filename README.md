# Inventário Central do Parque Instalado — SP

Aplicação web estruturada para equipes de campo e gestão do inventário.

## O que já está implementado
- Login por usuário e perfil (`manager` e `technician`).
- Banco central SQLite no servidor.
- 207 localidades importadas da aba **VISÃO GERAL** da planilha fornecida.
- 554 ATMs da base detalhada importados para auxiliar a identificação.
- Painel do técnico com Empresa → Linha → Estação/Localidade.
- Lista do que já foi feito antes de lançar um novo item.
- Bloqueio no servidor contra duplicidade por `local + tipo + identificação`.
- Estados de localidade: `PENDENTE`, `EM ANDAMENTO`, `CONCLUIDA`.
- Botão para o técnico encerrar a localidade.
- Painel gerencial para ver o que falta, o que está em andamento e o que foi concluído.
- Comparação do parque esperado com quantidade levantada.
- Upload de fotos e vídeos para pasta central do servidor.
- Reabertura de localidade pelo gestor.

## Credenciais iniciais
Gestor:
- usuário: `admin`
- senha: `Admin@123`

Técnico:
- usuário: `tecnico`
- senha: `Tecnico@123`

**Altere as credenciais antes de disponibilizar na internet.**

## Executar em um computador/servidor
1. Instale Python 3.11+.
2. Na pasta do projeto:
   `pip install -r requirements.txt`
3. Recomenda-se configurar uma chave de sessão:
   Windows PowerShell:
   `$env:INVENTARIO_SECRET_KEY="uma-chave-longa-e-aleatoria"`
   Linux:
   `export INVENTARIO_SECRET_KEY="uma-chave-longa-e-aleatoria"`
4. Execute:
   `python app.py`
5. Acesse no navegador:
   `http://localhost:5000`

Para acesso por celulares na mesma rede, use o IP do computador, por exemplo:
`http://192.168.1.20:5000`

## Produção / Internet
Para várias equipes externas, hospede esta aplicação em um servidor HTTPS. Para um piloto pequeno, SQLite atende. Para operação permanente com muitas equipes, substitua o SQLite por PostgreSQL e armazene fotos/vídeos em storage de objetos (S3, Azure Blob, Cloud Storage etc.).

## Regra para não repetir
O banco possui uma restrição única por:
`localidade + tipo de equipamento + identificação do ativo`.

Se alguém tentar lançar o mesmo ativo novamente, recebe aviso com o técnico e a data do registro anterior.

## Critério de acompanhamento
A localidade começa como `PENDENTE`. Ao primeiro registro vira `EM ANDAMENTO`. Somente quando o técnico usa **Concluir levantamento desta localidade** ela vira `CONCLUIDA`. Portanto, o gestor consegue separar locais visitados parcialmente de locais encerrados.


## Dashboard gerencial
O painel gerencial foi ampliado para apresentar:
- Total de localidades, pendentes, em andamento e concluídas.
- Quantidade de equipamentos levantados e parque esperado.
- Indicador percentual de conclusão geral.
- Indicadores de inoperantes e divergências.
- Cobertura do parque previsto.
- Progresso por empresa.
- Tabela operacional com filtros rápidos para identificar exatamente o que falta fazer.
- Atualização automática a cada 60 segundos.
- Identidade visual Autopass no cabeçalho e tela de login.

O pacote está pronto para ser hospedado em um servidor web. Para acesso externo real, publique atrás de HTTPS e substitua as credenciais iniciais.
