"""Cria os usuários iniciais e o conteúdo semente. Idempotente: rodar de novo não duplica.

    python -m app.seed

Usuários: criados um a um, se o email ainda não existir.
Conteúdo: cada coleção entra só se a tabela dela estiver vazia.

A fonte do conteúdo é a `seedData()` do `index.html` na raiz, traduzida aqui para o
vocabulário do banco (seção 13 do PLAN: desc->description, col->stage, order->position,
appName->app_name...). Os ids são uuid novos; os `uid()` de runtime do front são
descartados de propósito.

As senhas vêm do ambiente. Sem elas, usa um fallback óbvio e avisa em voz alta —
o fallback existe para o desenvolvimento local, nunca para produção.
"""

import datetime as dt
import os

from dotenv import load_dotenv
from sqlalchemy import func
from sqlmodel import Session, SQLModel, select

from app.config import ENV_FILE
from app.db import create_db_and_tables, engine
from app.models import AppSettings, Decision, Feature, Feedback, Goal, Milestone, Task, User
from app.security import hash_senha

load_dotenv(ENV_FILE)

SENHA_FALLBACK = "trocar123"
SETTINGS_ID = "1"

USUARIOS = [
    {
        "name": "Matheus",
        "email_var": "SEED_MATHEUS_EMAIL",
        "email_padrao": "matheus@topai.com.br",
        "senha_var": "SEED_MATHEUS_PASSWORD",
        "role": "owner",
        "color": "#4C6EF5",
    },
    {
        "name": "Geovanny",
        "email_var": "SEED_GEOVANNY_EMAIL",
        "email_padrao": "geovanny@topai.com.br",
        "senha_var": "SEED_GEOVANNY_PASSWORD",
        "role": "member",
        "color": "#12B886",
    },
]

# --------------------------------------------------------------- conteúdo semente
# Espelha `seedData()` / `seedCards()` do index.html.

META = {"app_name": "Topaí", "launch_date": "2026-08-01", "launch_city": "Cabreúva"}

# (title, desc, col, category, priority, assignee, due)
TASKS = [
    ("Parcerias com academias e mercados locais",
     "Mapear pontos de fluxo em Cabreúva para divulgar na largada.",
     "ideias", "marketing", "media", "matheus", ""),
    ("Programa de indicação entre prestadores",
     "Prestador que traz outro ganha destaque. Definir mecânica.",
     "ideias", "produto", "baixa", "geovanny", ""),
    ("Finalizar deck de condomínios",
     "Revisar copy e trocar mockups pelas telas reais do app.",
     "afazer", "comercial", "alta", "matheus", "2026-07-18"),
    ("Sequência de 9 Stories da semana",
     "Roteiro alternando enquete, contagem e bastidores.",
     "afazer", "marketing", "media", "matheus", "2026-07-14"),
    ("Onboarding dos Prestadores Fundadores",
     "Fluxo de cadastro, selo e ativação. 80% do foco inicial.",
     "fazendo", "produto", "urgente", "geovanny", "2026-07-20"),
    ("Posts de feed alternando amarelo e preto",
     "7 artes de lançamento no padrão da marca.",
     "fazendo", "design", "alta", "matheus", "2026-07-16"),
    ("Copy dos 7 posts de lançamento",
     "Tom humanizado, foco no portfólio do prestador.",
     "validacao", "marketing", "alta", "matheus", ""),
    ("Reativar seção de depoimentos na landing",
     "Ligar quando tiver prova social real de prestador.",
     "validacao", "dev", "media", "geovanny", ""),
    ("Capas de destaque do Instagram",
     "6 capas com ícone, círculo amarelo no preto.",
     "concluido", "design", "media", "matheus", ""),
    ("Definir slots de Fundador por cidade",
     "Vagas proporcionais à população de cada cidade.",
     "concluido", "produto", "media", "geovanny", ""),
]

GOALS = [
    ("Prestadores Fundadores", 12, 100, "#FFB000"),
    ("Clientes cadastrados", 40, 500, "#4C6EF5"),
    ("Parcerias com condomínios", 1, 5, "#12B886"),
    ("Cadastros na waitlist", 87, 300, "#7048E8"),
]

MILESTONES = [
    ("Landing e waitlist no ar", "2026-05-20", "done",
     "Next.js na Vercel, formulário no Google Sheets."),
    ("Presença no Instagram", "2026-06-10", "done",
     "Perfil, destaques, carrosséis e Stories."),
    ("Deck comercial para condomínios", "2026-07-18", "doing",
     "18 slides, foco em condomínios de casas."),
    ("Onboarding dos Prestadores Fundadores", "2026-07-25", "todo",
     "Cadastro, selo e ativação dos primeiros 100."),
    ("Lançamento em Cabreúva", "2026-08-01", "todo",
     "Abertura oficial do app na cidade."),
    ("Expansão para Itupeva e região", "2026-09-15", "todo",
     "Replicar o modelo nas cidades vizinhas."),
]

FEATURES = [
    ("Chat direto cliente e prestador",
     "Conversa dentro do app, sem sair pro WhatsApp.", 3, 3, "construindo"),
    ("Perfil com portfólio verificado",
     "O diferencial: portfólio e avaliações visíveis antes de contratar.", 3, 2, "construindo"),
    ("Busca por categoria e cidade",
     "Encontrar o prestador certo por região.", 3, 2, "construindo"),
    ("Avaliações bilaterais",
     "Cliente e prestador se avaliam. Base do anti-fraude.", 3, 2, "planejado"),
    ("Selo Fundador no perfil",
     "Destaque para os primeiros prestadores.", 2, 1, "pronto"),
    ("Programa de indicação",
     "Prestador traz prestador e ganha destaque.", 2, 1, "ideia"),
    ("Agendamento dentro do app",
     "Marcar horário sem troca de mensagens.", 3, 3, "ideia"),
    ("Notificações push",
     "Avisar sobre novas mensagens e oportunidades.", 2, 2, "ideia"),
]

FEEDBACK = [
    ("Gostei de ver o portfólio antes de chamar. Passa muito mais confiança.",
     "cliente", "elogio", "Beta tester", "2026-07-02"),
    ("Queria marcar o horário direto, sem ficar combinando no chat.",
     "cliente", "ideia", "Beta tester", "2026-07-03"),
    ("O cadastro travou na etapa da foto do serviço.",
     "prestador", "problema", "Eletricista de Cabreúva", "2026-07-04"),
    ("O selo de Fundador foi o que me convenceu a entrar agora.",
     "prestador", "elogio", "Pintor local", "2026-07-05"),
    ("Síndico pediu uma forma de indicar prestadores para o condomínio inteiro.",
     "condominio", "ideia", "Condomínio de casas", "2026-07-06"),
]

DECISIONS = [
    ("Esconder depoimentos na landing até ter prova social",
     "Manter a seção desativada, não apagada, até haver avaliações reais de prestadores.",
     "Depoimento vazio ou falso quebra a confiança antes mesmo do lançamento.",
     "2026-06-15", "ativa"),
    ("Foco inicial 80% no prestador",
     "Direcionar a maior parte da comunicação para atrair prestadores primeiro.",
     "Marketplace precisa de oferta antes de demanda. "
     "Sem prestador, o cliente não tem o que contratar.",
     "2026-06-05", "ativa"),
    ("Modelo Prestador Fundador",
     "50% de desconto permanente na assinatura, "
     "com vagas proporcionais à população de cada cidade.",
     "Cria urgência, recompensa quem acredita cedo e ancora a base inicial.",
     "2026-05-28", "ativa"),
    ("Nunca usar a palavra gratuito",
     "Evitar o termo em toda a comunicação da marca.",
     "Posiciona o serviço pelo valor, não pelo preço, e evita atrair quem só busca o de graça.",
     "2026-06-01", "ativa"),
    ("Cabreúva primeiro, depois expandir",
     "Concentrar todo o esforço em Cabreúva antes de abrir Itupeva e região.",
     "Densidade local vale mais que espalhar fino. Massa crítica em uma cidade prova o modelo.",
     "2026-05-25", "ativa"),
]


def data_ou_none(valor: str) -> dt.date | None:
    """O front usa string vazia para 'sem data'; no banco isso é NULL."""
    return dt.date.fromisoformat(valor) if valor else None


def vazia(session: Session, model: type[SQLModel]) -> bool:
    return session.exec(select(func.count()).select_from(model)).one() == 0


def seed_usuarios(session: Session) -> list[str]:
    usou_fallback = []
    for u in USUARIOS:
        email = os.getenv(u["email_var"], u["email_padrao"]).strip().lower()
        senha = os.getenv(u["senha_var"]) or SENHA_FALLBACK

        if session.exec(select(User).where(User.email == email)).first():
            print(f"[=] {u['name']} já existe ({email}), nada a fazer.")
            continue

        # Só avisa por quem foi de fato criado agora com a senha padrão.
        if senha == SENHA_FALLBACK:
            usou_fallback.append(f"{u['name']} <{email}>")

        session.add(
            User(
                name=u["name"],
                email=email,
                password_hash=hash_senha(senha),
                role=u["role"],
                color=u["color"],
            )
        )
        print(f"[+] {u['name']} criado ({email}, role={u['role']}).")
    return usou_fallback


def seed_tasks(session: Session) -> None:
    if not vazia(session, Task):
        print("[=] tasks já tem conteúdo, pulando.")
        return

    # `position` reinicia em cada coluna (0,1,2...), igual ao que o POST /api/tasks calcula.
    ordem: dict[str, int] = {}
    for title, desc, col, category, priority, assignee, due in TASKS:
        pos = ordem.get(col, 0)
        ordem[col] = pos + 1
        session.add(
            Task(
                title=title,
                description=desc,
                stage=col,
                category=category,
                priority=priority,
                assignee=assignee,
                due=data_ou_none(due),
                feedback="",
                position=float(pos),
            )
        )
    print(f"[+] {len(TASKS)} tasks inseridas.")


def seed_goals(session: Session) -> None:
    if not vazia(session, Goal):
        print("[=] goals já tem conteúdo, pulando.")
        return
    for title, current, target, color in GOALS:
        session.add(Goal(title=title, current=current, target=target, color=color))
    print(f"[+] {len(GOALS)} goals inseridas.")


def seed_milestones(session: Session) -> None:
    if not vazia(session, Milestone):
        print("[=] milestones já tem conteúdo, pulando.")
        return
    for title, date, status, desc in MILESTONES:
        session.add(
            Milestone(title=title, description=desc, date=data_ou_none(date), status=status)
        )
    print(f"[+] {len(MILESTONES)} milestones inseridos.")


def seed_features(session: Session) -> None:
    if not vazia(session, Feature):
        print("[=] features já tem conteúdo, pulando.")
        return
    for title, desc, impact, effort, status in FEATURES:
        session.add(
            Feature(title=title, description=desc, impact=impact, effort=effort, status=status)
        )
    print(f"[+] {len(FEATURES)} features inseridas.")


def seed_feedback(session: Session) -> None:
    if not vazia(session, Feedback):
        print("[=] feedback já tem conteúdo, pulando.")
        return
    for text, source, tipo, author, date in FEEDBACK:
        session.add(
            Feedback(text=text, source=source, type=tipo, author=author, date=data_ou_none(date))
        )
    print(f"[+] {len(FEEDBACK)} feedbacks inseridos.")


def seed_decisions(session: Session) -> None:
    if not vazia(session, Decision):
        print("[=] decisions já tem conteúdo, pulando.")
        return
    for title, decision, rationale, date, status in DECISIONS:
        session.add(
            Decision(
                title=title,
                decision=decision,
                rationale=rationale,
                date=data_ou_none(date),
                status=status,
            )
        )
    print(f"[+] {len(DECISIONS)} decisões inseridas.")


def seed_settings(session: Session) -> None:
    """Cria o registro único, ou preenche um que nasceu vazio.

    `GET /api/state` cria a linha id="1" com valores em branco na primeira leitura.
    Se isso já aconteceu, aqui a completamos. Se alguém já configurou pela UI,
    não sobrescrevemos.
    """
    settings = session.get(AppSettings, SETTINGS_ID)

    if settings is None:
        session.add(
            AppSettings(
                id=SETTINGS_ID,
                app_name=META["app_name"],
                launch_date=data_ou_none(META["launch_date"]),
                launch_city=META["launch_city"],
            )
        )
        print("[+] settings criado a partir do meta.")
        return

    nunca_configurado = settings.launch_date is None and not settings.launch_city
    if nunca_configurado:
        settings.app_name = META["app_name"]
        settings.launch_date = data_ou_none(META["launch_date"])
        settings.launch_city = META["launch_city"]
        session.add(settings)
        print("[+] settings estava em branco, preenchido a partir do meta.")
    else:
        print("[=] settings já configurado, preservado.")


def seed() -> None:
    create_db_and_tables()

    with Session(engine) as session:
        usou_fallback = seed_usuarios(session)
        seed_settings(session)
        seed_tasks(session)
        seed_goals(session)
        seed_milestones(session)
        seed_features(session)
        seed_feedback(session)
        seed_decisions(session)
        session.commit()

    if usou_fallback:
        print()
        print("!" * 70)
        print(f"AVISO: senha padrão '{SENHA_FALLBACK}' usada para: {', '.join(usou_fallback)}")
        print("Defina SEED_*_PASSWORD no .env e troque estas senhas antes de ir para produção.")
        print("!" * 70)


if __name__ == "__main__":
    seed()
