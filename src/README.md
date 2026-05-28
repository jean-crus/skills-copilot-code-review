# API de Atividades da Mergington High School

Uma aplicação FastAPI para visualizar atividades extracurriculares e administrar anúncios exibidos na página inicial.

## Funcionalidades

- Visualizar todas as atividades extracurriculares disponíveis
- Filtrar atividades por dia e faixa de horário
- Autenticar professores e validar sessão
- Registrar e remover estudantes de atividades
- Exibir anúncios ativos com vigência baseada em datas
- Gerenciar anúncios com criação, edição e exclusão para usuários autenticados

## Como começar

1. Instale as dependências:

   ```
   pip install -r requirements.txt
   ```

2. Execute a aplicação:

   ```
   python -m uvicorn src.app:app --reload
   ```

3. Abra seu navegador e acesse:
   - Documentação da API: http://localhost:8000/docs
   - Documentação alternativa: http://localhost:8000/redoc

## Endpoints da API

| Método | Endpoint | Descrição |
| ------ | -------- | --------- |
| GET | `/activities` | Obtém todas as atividades com detalhes e número atual de participantes |
| GET | `/activities/days` | Lista os dias com atividades cadastradas |
| POST | `/activities/{activity_name}/signup?email=student@mergington.edu&teacher_username=principal` | Registra um estudante em uma atividade com autenticação de professor |
| POST | `/activities/{activity_name}/unregister?email=student@mergington.edu&teacher_username=principal` | Remove um estudante de uma atividade com autenticação de professor |
| POST | `/auth/login?username=principal&password=admin789` | Realiza login de professor ou administrador |
| GET | `/auth/check-session?username=principal` | Valida uma sessão salva no frontend |
| GET | `/announcements` | Lista apenas anúncios ativos para exibição pública |
| GET | `/announcements?include_all=true&teacher_username=principal` | Lista todos os anúncios para gestão autenticada |
| POST | `/announcements?teacher_username=principal` | Cria um anúncio com `title`, `message`, `expires_at` e `starts_at` opcional |
| PUT | `/announcements/{announcement_id}?teacher_username=principal` | Atualiza um anúncio existente |
| DELETE | `/announcements/{announcement_id}?teacher_username=principal` | Exclui um anúncio |

## Modelo de Dados

A aplicação usa um modelo de dados simples com identificadores significativos:

1. **Atividades** - Usa o nome da atividade como identificador:
   - Descrição
   - Horário
   - Número máximo de participantes permitidos
   - Lista de e-mails dos alunos inscritos

2. **Professores** - Usa o nome de usuário como identificador:
   - Nome de exibição
   - Senha com hash Argon2
   - Papel do usuário

3. **Anúncios** - Usa um identificador derivado do título:
   - Título
   - Mensagem
   - Data opcional de início
   - Data obrigatória de expiração
   - Usuário criador e último usuário que atualizou

Os dados são persistidos em MongoDB. Na inicialização, a aplicação semeia atividades, contas de professor e um anúncio de exemplo quando as coleções estão vazias.
