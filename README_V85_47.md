# V85.47 — Lista de Presença Digital
Base: V85.46 REV4 homologada.
Menu: Implantação de Hardware > Lista de Presença Digital.
Recursos: criação de lista, edição de rascunho, assinatura individual no mesmo aparelho, data/hora de cada assinatura, conclusão com PDF A4 paisagem e arquivamento na pasta escolhida do Drive Técnico.
Permissões na Matriz: implantation.attendance.view, implantation.attendance.manage. Para concluir e gravar o PDF também é exigida implantation.repository.manage.
Banco: criação aditiva de implantation_attendance e implantation_attendance_participants no fluxo existente de db.metadata.create_all; sem migração destrutiva.
Observação operacional importante: PDFs são salvos pelo mecanismo de arquivos local do Drive Técnico (UPLOAD_DIR). Confirmar armazenamento persistente em produção no Render antes de considerar o repositório definitivo. A assinatura capturada é eletrônica simples, não ICP-Brasil. Dados pessoais e assinaturas exigem acesso restrito e política de retenção.
Teste: habilitar permissões, criar lista, preencher atividade, abrir Assinar presença, capturar assinatura, concluir em pasta válida do Drive, verificar PDF e bloqueio de edição. Não altera dados históricos.
