# Deploy do Topaí no VPS

Runbook. As decisões e o porquê estão no [PLAN.md](PLAN.md) — seção 10 (deploy),
11 (variáveis) e 13 (armadilhas). Aqui só a ordem dos comandos.

Pressupõe Ubuntu com **PostgreSQL** e **Nginx** já instalados, e o subdomínio
escolhido (o exemplo usa `gestao.topai.com.br`). Troque onde aparecer.

---

## 1. Base e usuário no Postgres

```bash
sudo -u postgres psql -c "CREATE DATABASE topai;"
sudo -u postgres psql -c "CREATE USER topai_app WITH PASSWORD 'senha_forte_aqui';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE topai TO topai_app;"
```

> **PG 15+:** o `GRANT` acima não dá permissão no schema `public`. Se o app
> falhar ao criar as tabelas com erro de permissão, rode:
> ```bash
> sudo -u postgres psql -d topai -c "GRANT ALL ON SCHEMA public TO topai_app;"
> ```

## 2. Código e ambiente

```bash
cd /var/www
sudo git clone https://github.com/mmalvezi/topai-gestao.git
sudo chown -R www-data:www-data /var/www/topai-gestao
cd topai-gestao/backend

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 3. Configurar o `.env`

```bash
cp .env.example .env
openssl rand -hex 32          # copie a saída para JWT_SECRET
nano .env
```

Preencha `DATABASE_URL` (senha do passo 1), `JWT_SECRET`, `CORS_ORIGINS`.

> **Defina `SEED_MATHEUS_PASSWORD` e `SEED_GEOVANNY_PASSWORD` AGORA, antes do
> passo 4.** O seed aborta sem elas, de propósito: o repositório é público e a
> senha de exemplo está no código. Não use `SEED_ALLOW_DEV_PASSWORD` no VPS.

Proteja o arquivo — ele tem as credenciais do banco e o segredo do JWT:

```bash
chmod 600 .env
sudo chown www-data:www-data .env
```

## 4. Seed (uma vez)

Cria as tabelas, os dois usuários e o conteúdo inicial. É idempotente: rodar de
novo não duplica nada.

```bash
python -m app.seed
```

Se faltar alguma senha, ele para com `SEED ABORTADO` e **não grava nada**.
Volte ao passo 3.

## 5. Serviço systemd

```bash
# ainda em /var/www/topai-gestao/backend, vindo do passo 4
sudo cp ../deploy/topai.service.example /etc/systemd/system/topai.service
sudo nano /etc/systemd/system/topai.service     # confira os caminhos
sudo systemctl daemon-reload
sudo systemctl enable --now topai
sudo systemctl status topai
```

A API sobe em `127.0.0.1:8000`, sem exposição direta à internet.

```bash
curl -s http://127.0.0.1:8000/api/health        # {"status":"ok"}
```

## 6. Nginx

```bash
cd /var/www/topai-gestao
sudo cp deploy/nginx.conf.example /etc/nginx/sites-available/topai
sudo nano /etc/nginx/sites-available/topai      # server_name e root
sudo ln -s /etc/nginx/sites-available/topai /etc/nginx/sites-enabled/topai
sudo nginx -t && sudo systemctl reload nginx    # o -t valida a sintaxe
```

## 7. DNS

Aponte um registro **A** de `gestao.topai.com.br` para o IP do VPS. Espere
propagar antes do passo 8 — o certbot valida pelo domínio.

```bash
dig +short gestao.topai.com.br
```

## 8. SSL

```bash
sudo certbot --nginx -d gestao.topai.com.br
```

O certbot reescreve o arquivo do Nginx, cria o bloco 443 e renova sozinho.

---

## 9. Smoke test

```bash
# health pela internet, já em HTTPS
curl -s https://gestao.topai.com.br/api/health
# -> {"status":"ok"}

# login com a senha que você definiu no passo 3
curl -s -X POST https://gestao.topai.com.br/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"matheus@topai.com.br","password":"A_SENHA_QUE_VOCE_DEFINIU"}'
# -> {"token":"eyJ...","user":{...,"initials":"MA"}}

# o estado exige o token
TOKEN=$(curl -s -X POST https://gestao.topai.com.br/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"matheus@topai.com.br","password":"A_SENHA_QUE_VOCE_DEFINIU"}' \
  | python3 -c 'import sys,json;print(json.load(sys.stdin)["token"])')

curl -s https://gestao.topai.com.br/api/state -H "Authorization: Bearer $TOKEN" | head -c 200
# -> {"settings":{"appName":"Topaí",...

curl -s -o /dev/null -w '%{http_code}\n' https://gestao.topai.com.br/api/state
# -> 401  (sem token)
```

Por fim, abra `https://gestao.topai.com.br` no navegador: deve aparecer a tela
de login, e o app deve carregar depois de entrar.

---

## Operação

```bash
# logs ao vivo
sudo journalctl -u topai -f

# reiniciar após um deploy
cd /var/www/topai-gestao && sudo git pull
sudo systemctl restart topai

# backup do banco
pg_dump -U topai_app topai > backup_$(date +%F).sql
```

## Se algo falhar

| Sintoma | Onde olhar |
|---|---|
| `502 Bad Gateway` no `/api/` | `systemctl status topai` — o Uvicorn caiu |
| Erro de permissão ao criar tabelas | o `GRANT ... SCHEMA public` do passo 1 |
| `SEED ABORTADO` | faltam as `SEED_*_PASSWORD` no `.env` |
| Login sempre 401 | senha errada, ou o seed nunca rodou |
| Todos deslogados de repente | o `JWT_SECRET` mudou |
| Front carrega mas `/api` dá 404 | o `location /api/` do Nginx, ou o proxy_pass |
