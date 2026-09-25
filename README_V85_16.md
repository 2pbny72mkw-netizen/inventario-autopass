# V85.16 — QR Trilhos + Consolidação

Base: V85.15 homologada.

## Entregas
- Gerador de QR – Trilhos com fluxo Empresa → Linha → Estação → Bloqueio.
- Cadastro mestre de configuração técnica por bloqueio.
- Permissões `implantation.qr.view` e `implantation.qr.manage` na Matriz.
- Auditoria de criação/alteração da configuração (antes/depois, usuário e data).
- Executor visualiza a configuração, mas não a edita no gerador.
- AES-256-CBC/PKCS7, IV aleatório e Protobuf preservados; chave apenas em variável de ambiente.
- Histórico/Sobre e identificação da versão atualizados.
- Diagnóstico V85.15 preservado, sem exclusão automática de evidências.

## Homologação obrigatória
A conversão IPv4 para uint32 permanece pendente de validação física no equipamento/leitor. Não promover o QR para produção sem esse teste.
