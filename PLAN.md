# Topaí · Central do app — Plano de conclusão e deploy

> Documento de trabalho para o Claude Code. Mantenha ele na raiz do projeto.
> Se quiser que o Claude Code carregue isso automaticamente como contexto,
> salve uma cópia como `CLAUDE.md`. As decisões e convenções aqui valem para
> todo o desenvolvimento deste repositório.

## 1. Onde estamos

Hoje o projeto é um **único arquivo HTML** (`index.html`) que roda 100% no navegador. Ele é o front completo de uma central de founder para o Topaí, com seis áreas: Visão geral, Tarefas (kanban com fluxo de validação entre sócios), Roadmap, Metas, Funcionalidades (matriz impacto x esforço), Feedback e Decisões.

Toda a persistência passa por um único objeto `store` que grava em `localStorage`. Por isso cada navegador tem os próprios dados. **Falta o que este plano resolve:** um backend com banco de dados para acesso simultâneo real e o deploy no VPS.

O `store` foi feito de propósito como ponto único de troca. A integração com a API acontece ali e nas funções de CRUD, sem reescrever a renderização.

## 2. Objetivo (definition of done)

- Matheus e Geovanny fazem login e veem **o mesmo estado**, ao vivo.
- Toda alteração (tarefa, meta, marco, feature, feedback, decisão, configuração) é salva no banco e aparece para o outro em poucos segundos.
- App publicado no VPS com HTTPS, em um subdomínio do Topaí.
- Sem perda de dado ao dois editarem ao mesmo tempo (edições granulares por item, não um blob único).

## 3. Stack

Mesma linha do EPR Gestão, para reaproveitar o que já dominamos:

- **Backend:** FastAPI + Uvicorn
- **Banco:** PostgreSQL
- **ORM:** SQLModel (Pydantic + SQLAlchemy num pacote só, menos boilerplate)
- **Driver:** psycopg (v3)
- **Auth:** JWT (bearer token), hash de senha com `bcrypt` usado direto
- **Front:** o `index.html` atual, servido como estático. Sem framework, sem build.
- **Servidor:** VPS Hostinger (Ubuntu), Nginx como proxy reverso, systemd para o processo, Let's Encrypt para SSL.

Fora de escopo por agora (deixar para depois): WebSocket para tempo real fino (polling resolve para 2-3 pessoas), app mobile nativo, múltiplos workspaces, migrations com Alembic (as tabelas são criadas no start; Alembic entra quando o schema começar a evoluir em produção).

## 4. Arquitetura alvo

```
Navegador (index.html)
    |  fetch com Authorization: Bearer <jwt>
    v
Nginx (443, SSL)
    |-- /            -> arquivos estáticos (index.html)
    |-- /api/*       -> Uvicorn 127.0.0.1:8000
                          |
                          v
                     FastAPI  ->  PostgreSQL
```

Front e API no **mesmo domínio** (subdomínio do Topaí). Isso simplifica CORS e evita dor de cabeça com cookie e origem.

## 5. Estrutura de pastas proposta

```
topai-gestao/
  index.html                # front atual (mover para cá se ainda não estiver)
  PLAN.md                   # este arquivo
  .gitignore
  backend/
    app/
      main.py               # cria o app, monta routers, CORS, cria tabelas no start
      config.py             # lê variáveis de ambiente (pydantic-settings)
      db.py                 # engine + sessão do SQLModel
      models.py             # tabelas (User, Task, Goal, Milestone, Feature, Feedback, Decision, Settings)
      schemas.py            # payloads de entrada (create/update)
      security.py           # hash de senha (bcrypt) + JWT + dependency get_current_user
      seed.py               # cria usuários iniciais e importa os dados semente uma vez
      routers/
        auth.py
        state.py            # GET /api/state (tudo de uma vez, para o load inicial)
        tasks.py
        goals.py
        milestones.py
        features.py
        feedback.py
        decisions.py
        settings.py
    requirements.txt
    .env.example
  deploy/
    nginx.conf.example
    topai.service.example
```

## 6. Modelo de dados

Convenções: PK `id` como texto (uuid4 em string, igual ao front que usa ids curtos), `created_at` e `updated_at` em toda tabela. **Atenção:** `column` é palavra reservada no SQL. A etapa da tarefa vai na coluna **`stage`** (o front chama de `col`; mapear na serialização).

- **users**: id, name, email (único), password_hash, role (`owner`/`member`), active (bool)
- **tasks**: id, title, description, category, priority, assignee, **stage**, due (date, nullable), feedback (text), position (float, para ordenar no kanban)
- **goals**: id, title, current (int), target (int), color, position
- **milestones**: id, title, description, date (date, nullable), status (`todo`/`doing`/`done`), position
- **features**: id, title, description, impact (1-3), effort (1-3), status (`ideia`/`planejado`/`construindo`/`pronto`), position
- **feedback**: id, text, source (`prestador`/`cliente`/`condominio`/`outro`), type (`elogio`/`problema`/`ideia`), author, date (date)
- **decisions**: id, title, decision (text), rationale (text), date (date), status (`ativa`/`revisada`)
- **settings**: id fixo `1`, app_name, launch_date (date), launch_city

`assignee` guarda o identificador do usuário (ou `none`). Para atribuição de verdade, usar o `id`/apelido do usuário logado. Manter também Matheus e Geovanny como usuários reais no seed.

## 7. API

Prefixo `/api`. Tudo protegido por JWT, exceto o login.

**Auth**
- `POST /api/auth/login` recebe `{email, password}`, devolve `{token, user}`
- `GET  /api/auth/me` devolve o usuário logado

**Carga inicial**
- `GET  /api/state` devolve tudo de uma vez: `{settings, tasks, goals, milestones, features, feedback, decisions, users}` (users só com id, name, initials, color). É o que o front chama no lugar do `localStorage`. Também é usado no polling de sincronização.

**CRUD por entidade** (mesmo padrão para as seis)
- `POST   /api/tasks`            cria
- `PATCH  /api/tasks/{id}`       atualiza parcial (inclui mover: `{stage, position}`)
- `DELETE /api/tasks/{id}`       remove
- idem para `/api/goals`, `/api/milestones`, `/api/features`, `/api/feedback`, `/api/decisions`
- `PUT    /api/settings`         atualiza o registro único

Regras de negócio que já existem no front e o backend deve respeitar:
- Ao mover tarefa para `concluido`, limpar o campo `feedback`.
- "Pedir ajuste" = `PATCH` com `stage=fazendo` e `feedback` preenchido.
- `position` calculado no cliente ao arrastar; o backend só persiste o valor.

## 8. Autenticação (detalhe importante)

**Usar `bcrypt` direto, não passlib.** No EPR Gestão batemos no conflito de versão entre `passlib` e `bcrypt` (erro do `__about__`). Para evitar de novo:

```python
import bcrypt
def hash_senha(p: str) -> str:
    return bcrypt.hashpw(p.encode(), bcrypt.gensalt()).decode()
def confere_senha(p: str, h: str) -> bool:
    return bcrypt.checkpw(p.encode(), h.encode())
```

JWT com `pyjwt`, expiração longa (ex.: 30 dias, é ferramenta interna). Segredo forte via `JWT_SECRET`. O token vai no header `Authorization: Bearer`. `get_current_user` é uma dependency do FastAPI aplicada nos routers.

Se em algum momento preferirmos passlib mesmo assim, fixar `bcrypt==4.0.1`.

## 9. Integração do frontend

O front muda em pontos bem localizados. **Não mexer na renderização.**

1. **Cliente de API.** Criar um objeto `api` com `get/post/patch/put/del` que injeta o token e trata `401` (redireciona para login). O token fica em `localStorage` (só o token; os dados saem de lá).
2. **Login.** Tela simples antes do app (email + senha) chamando `POST /api/auth/login`. Guardar token e usuário. Botão de sair.
3. **Load inicial.** `load()` deixa de ler `localStorage` e passa a chamar `GET /api/state`, populando o objeto `data` em memória (que continua sendo a fonte da renderização).
4. **Trocar as mutações por chamadas de API.** Mapa direto de função para endpoint:

   | Função no front | Chamada |
   |---|---|
   | `openTaskForm` (criar/editar) | `POST` / `PATCH /api/tasks` |
   | `removeTask` | `DELETE /api/tasks/{id}` |
   | `moveTo`, `dropCard`, `approve`, `openAdjust` | `PATCH /api/tasks/{id}` |
   | `openGoalForm`, `removeGoal`, `stepGoal` | `POST` / `PATCH` / `DELETE /api/goals` |
   | `openMsForm`, `removeMs`, `cycleMs` | `POST` / `PATCH` / `DELETE /api/milestones` |
   | `openFeatForm`, `removeFeat` | `POST` / `PATCH` / `DELETE /api/features` |
   | `openFbForm`, `removeFb` | `POST` / `PATCH` / `DELETE /api/feedback` |
   | `openDecForm`, `removeDec` | `POST` / `PATCH` / `DELETE /api/decisions` |
   | `openSettings` | `PUT /api/settings` |

   Padrão: atualização otimista (altera `data` e renderiza na hora) e, em caso de erro da API, reverte e mostra um toast. A função `save()` de blob some (ou vira no-op).
5. **Sincronização (acesso simultâneo).** Um `syncState()` chama `GET /api/state` a cada ~15s e no `focus` da janela. Atualiza `data` e re-renderiza a view atual. **Trava importante:** não re-renderizar enquanto um modal estiver aberto (checar `#backdrop.is-open`) para não fechar o formulário do usuário no meio da digitação.
6. **Responsável real.** Preencher `assignee` com o usuário logado por padrão; a lista de responsáveis vem de `users`.

## 10. Deploy no VPS

Assumindo Ubuntu com PostgreSQL e Nginx já instalados (mesmo servidor ou um novo, como no EPR Gestão).

1. **Banco.** Criar base e usuário dedicados:
   ```bash
   sudo -u postgres psql -c "CREATE DATABASE topai;"
   sudo -u postgres psql -c "CREATE USER topai_app WITH PASSWORD 'trocar_isto';"
   sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE topai TO topai_app;"
   ```
2. **Código + venv.**
   ```bash
   cd /var/www && git clone https://github.com/mmalvezi/topai-gestao.git
   cd topai-gestao/backend
   python3 -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
   cp .env.example .env   # editar com dados reais
   ```
3. **Env de produção** (`backend/.env`): ver seção 11. Gerar `JWT_SECRET` forte (`openssl rand -hex 32`).
4. **Seed dos usuários** (uma vez): `python -m app.seed` cria Matheus e Geovanny. Trocar as senhas iniciais.
5. **Serviço systemd** (`deploy/topai.service.example` -> `/etc/systemd/system/topai.service`):
   ```ini
   [Unit]
   Description=Topai API
   After=network.target postgresql.service

   [Service]
   WorkingDirectory=/var/www/topai-gestao/backend
   EnvironmentFile=/var/www/topai-gestao/backend/.env
   ExecStart=/var/www/topai-gestao/backend/.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
   Restart=always
   User=www-data

   [Install]
   WantedBy=multi-user.target
   ```
   ```bash
   sudo systemctl daemon-reload && sudo systemctl enable --now topai
   ```
6. **Nginx** (`deploy/nginx.conf.example` -> `/etc/nginx/sites-available/topai`, depois `ln -s` em sites-enabled):
   ```nginx
   server {
     server_name gestao.topai.com.br;

     root /var/www/topai-gestao;
     index index.html;

     location /api/ {
       proxy_pass http://127.0.0.1:8000;
       proxy_set_header Host $host;
       proxy_set_header X-Real-IP $remote_addr;
     }
     location / {
       try_files $uri /index.html;
     }
   }
   ```
   ```bash
   sudo nginx -t && sudo systemctl reload nginx
   ```
7. **DNS.** Apontar um registro A do subdomínio escolhido (ex.: `gestao.topai.com.br`) para o IP do VPS.
8. **SSL.** `sudo certbot --nginx -d gestao.topai.com.br` (renova sozinho depois).

## 11. Variáveis de ambiente (`.env.example`)

```
DATABASE_URL=postgresql+psycopg://topai_app:senha@localhost:5432/topai
JWT_SECRET=gerar_com_openssl_rand_hex_32
JWT_EXPIRE_DAYS=30
CORS_ORIGINS=https://gestao.topai.com.br
```

## 12. requirements.txt (backend)

```
fastapi
uvicorn[standard]
sqlmodel
psycopg[binary]
bcrypt==4.1.3
pyjwt
pydantic-settings
python-dotenv
```

## 13. Armadilhas conhecidas

- **bcrypt x passlib:** usar bcrypt direto (seção 8). Já nos pegou uma vez.
- **`column` é reservado no SQL:** usar `stage` no banco, mapear para/de `col` do front.
- **Campo `date` no Python 3.14:** com a avaliação preguiçosa de anotações (PEP 649), um campo chamado `date` sombreia o tipo `date` importado e o Pydantic quebra com `unevaluable-type-annotation`. Usar `import datetime as dt` e anotar `dt.date` (feito em `models.py` e `schemas.py`).
- **`CORS_ORIGINS` como lista:** o pydantic-settings tenta `json.loads` em campos de tipo lista, o que quebra `a,b` vindo do `.env`. O campo é lido como texto e exposto por `settings.cors_origins_list`.
- **Datas:** guardar como `date` (formato `YYYY-MM-DD`, igual o front já usa). Cuidado com fuso ao serializar.
- **Sync x modal aberto:** o polling não pode re-renderizar com formulário aberto.
- **Otimista com rollback:** se a API falhar, reverter o estado local e avisar.
- **Segredos fora do git:** `.env` no `.gitignore`. Nunca commitar senha nem `JWT_SECRET`.
- **Permissões do Postgres:** no PG 15+ pode faltar permissão no schema `public`; se der erro de permissão, rodar `GRANT ALL ON SCHEMA public TO topai_app;` dentro da base `topai`.

## 14. Fases (checklist)

**Fase 0 — Preparação**
- [ ] Commitar o `index.html` atual na raiz
- [x] Criar `.gitignore` (`.venv/`, `__pycache__/`, `.env`, `*.pyc`)
- [x] Criar a estrutura `backend/` e o `.env.example`

**Fase 1 — Backend base**
- [x] App FastAPI, config por env, CORS pelo `CORS_ORIGINS`
- [x] Conexão Postgres e criação das tabelas no start
- [x] Models e schemas das 8 tabelas (7 entidades + users + settings)
- [x] `GET /api/health`

**Fase 2 — Auth**
- [ ] Tabela users + `seed.py` com Matheus e Geovanny
- [ ] `POST /api/auth/login` (bcrypt) e `GET /api/auth/me`
- [ ] Dependency `get_current_user` protegendo os routers

**Fase 3 — CRUD e estado**
- [ ] Routers de tasks, goals, milestones, features, feedback, decisions
- [ ] `PUT /api/settings`
- [ ] `GET /api/state` agregando tudo
- [ ] Importar os dados semente atuais (uma vez, via seed)

**Fase 4 — Integração do front**
- [ ] Objeto `api` com token e tratamento de 401
- [ ] Tela de login e botão de sair
- [ ] `load()` usando `GET /api/state`
- [ ] Trocar cada mutação pela chamada correspondente (tabela da seção 9)
- [ ] `syncState()` por foco e intervalo, com a trava do modal
- [ ] Responsável usando o usuário logado

**Fase 5 — Deploy**
- [ ] Base e usuário do Postgres no VPS
- [ ] venv + requirements + `.env` de produção
- [ ] Serviço systemd rodando o Uvicorn
- [ ] Nginx servindo estático + proxy `/api`
- [ ] DNS do subdomínio apontado
- [ ] SSL via certbot
- [ ] Rodar o seed de usuários e trocar as senhas

**Fase 6 — Fechamento**
- [ ] Teste com dois usuários ao mesmo tempo (criar, mover, editar, aprovar)
- [ ] Backup agendado (`pg_dump` diário)
- [ ] Rate limit simples no login

## 15. Comandos úteis

```bash
# rodar local
cd backend && source .venv/bin/activate
uvicorn app.main:app --reload --port 8000

# ver logs em produção
sudo journalctl -u topai -f

# backup do banco
pg_dump -U topai_app topai > backup_$(date +%F).sql
```

---

**Como tocar com o Claude Code:** ir por fase, na ordem. Ao terminar cada fase, marcar os itens e commitar. Começar pela Fase 0 e Fase 1 (backend de pé rodando local) antes de encostar no front.
