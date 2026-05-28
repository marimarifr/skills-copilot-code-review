# API de Atividades da Mergington High School

Uma aplicação FastAPI super simples que permite aos alunos visualizar e se inscrever em atividades extracurriculares.

## Funcionalidades

- Visualizar todas as atividades extracurriculares disponíveis
- Inscrever-se em atividades
- Autenticar professores para operacoes administrativas
- Exibir anuncios ativos no topo da interface
- Gerenciar anuncios (listar, criar, editar e excluir) para usuarios autenticados

## Como começar

1. Instale as dependências:

   ```
   pip install fastapi uvicorn
   ```

2. Execute a aplicação:

   ```
   python app.py
   ```

3. Abra seu navegador e acesse:
   - Documentação da API: http://localhost:8000/docs
   - Documentação alternativa: http://localhost:8000/redoc

## Endpoints da API

| Método | Endpoint                                                          | Descrição                                                            |
| ------ | ----------------------------------------------------------------- | -------------------------------------------------------------------- |
| GET    | `/activities`                                                     | Obtém todas as atividades com detalhes e número atual de participantes |
| POST   | `/activities/{activity_name}/signup?email=student@mergington.edu` | Inscreve-se em uma atividade                                         |
| POST   | `/auth/login?username=...&password=...`                          | Autentica usuario de professor/direcao                               |
| GET    | `/announcements`                                                  | Lista anuncios ativos para exibicao publica                          |
| GET    | `/announcements/all?teacher_username=...`                         | Lista todos os anuncios para gerenciamento (requer login)            |
| POST   | `/announcements?message=...&expires_on=YYYY-MM-DD&teacher_username=...` | Cria um novo anuncio (inicio opcional via starts_on)            |
| PUT    | `/announcements/{announcement_id}?message=...&expires_on=YYYY-MM-DD&teacher_username=...` | Edita um anuncio existente |
| DELETE | `/announcements/{announcement_id}?teacher_username=...`           | Exclui um anuncio                                                    |

## Modelo de Dados

A aplicação usa um modelo de dados simples com identificadores significativos:

1. **Atividades** - Usa o nome da atividade como identificador:
   - Descrição
   - Horário
   - Número máximo de participantes permitidos
   - Lista de e-mails dos alunos inscritos

2. **Alunos** - Usa o e-mail como identificador:
   - Nome
   - Série

Os dados sao persistidos em MongoDB local (colecoes de atividades, professores e anuncios).
