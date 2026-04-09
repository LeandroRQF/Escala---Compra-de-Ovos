import requests  # Biblioteca para fazer requisições HTTP (envio para o Teams)
import json      # Manipulação de JSON (log e payload)
import os        # Manipulação de arquivos (verificar se log existe)
from datetime import datetime, timedelta  # Trabalhar com datas
import holidays  # Biblioteca para verificar feriados
from dotenv import load_dotenv
import os

load_dotenv()

# =========================
# CONFIGURAÇÕES
# =========================

# URL do Incoming Webhook do seu canal no Teams
# Como criar: Canal Teams → "..." → Conectores → "Incoming Webhook" → Configurar
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

# Lista de pessoas participantes da escala
PESSOAS = [
    "Anna Martins",
    "Rafael Silva",
    "Lucas Bueno",
    "Roberta Casella",
    "Rafael Freitas",
    "Tatiana Vieira",
    "Leandro Faria",
    "Daniel Nascimento",
    "Erick Faluba",
    "Rafael Gouvea"
]

# Arquivo onde será salvo o histórico de envios (evita duplicidade)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ARQUIVO_LOG = os.path.join(BASE_DIR, "log_ovos.json")

# Se True → imprime no console | False → envia para o Teams
# Data fixa para simulação (só usada se MODO_TESTE_DATA = True)
MODO_TESTE = False
DATA_FIXA = datetime(2026, 4, 13).date() 

# Feriados nacionais + Minas Gerais
feriados = holidays.Brazil(subdiv="MG")

# Feriados específicos de Belo Horizonte (não estão na lib)
FERIADOS_BH_FIXOS = [
    "15-08",
    "08-12",
    "12-08",
]

# =========================
# DATA ATUAL
# =========================

def hoje():
    """
    Retorna a data atual.
    Se estiver em modo teste, retorna a data simulada.
    """
    if MODO_TESTE:
        return DATA_FIXA
    return datetime.now().date()

# =========================
# VALIDAÇÃO DE FERIADOS
# =========================

def eh_feriado(data):
    """
    Verifica se a data é feriado:
    - Nacional / MG (via biblioteca)
    - BH (manual)
    """    

    # Verifica feriados oficiais
    if data in feriados:
        return True

    # Verifica feriados fixos de BH
    if data.strftime("%d-%m") in FERIADOS_BH_FIXOS:
        return True

    return False

# =========================
# LOG (EVITAR DUPLICIDADE)
# =========================

def carregar_log():
    """
    Carrega o histórico de envios do arquivo JSON.
    Se o arquivo não existir ou estiver vazio, retorna um dicionário vazio.
    """

    if not os.path.exists(ARQUIVO_LOG):
        return {}

    try:
        with open(ARQUIVO_LOG, "r") as f:
            conteudo = f.read().strip()
            if not conteudo:
                return {}
            return json.loads(conteudo)
    except:
        return {}

def salvar_log(log):
    """
    Salva o histórico de envios no arquivo JSON.
    """
        
    with open(ARQUIVO_LOG, "w") as f:
        json.dump(log, f, indent=2, ensure_ascii=False)

# =========================
# GERAÇÃO DE PARES
# =========================

def gerar_pares(pessoas):
    """
    Gera a lista de pares:

    - Se número PAR:
      (1-2, 3-4, 5-6...)

    - Se número ÍMPAR:
      faz rotação:
      (1-2, 3-4...)
      depois (2-3, 3-4...)
    """

    n = len(pessoas)

    # Caso PAR
    if n % 2 == 0:
        return [(pessoas[i], pessoas[i+1]) for i in range(0, n, 2)]

    # Caso ÍMPAR
    pares = []

    # Primeira rodada (pares fixos)
    for i in range(0, n - 1, 2):
        pares.append((pessoas[i], pessoas[i+1]))
    
    # Segunda rodada (rotativo)
    for i in range(n):
        pares.append((pessoas[i], pessoas[(i+1) % n]))

    return pares

def obter_par(data_ref):
    """
    Define qual par será responsável baseado na semana do ano.
    """

    pares = gerar_pares(PESSOAS)

    # Número da semana (ISO)
    semana = data_ref.isocalendar()[1]

    # Retorna o par baseado na semana
    return pares[semana % len(pares)]

# =========================
# CÁLCULO DO INÍCIO SEMANA
# =========================

def calcular_inicio_semana(data_ref, tipo):
    """
    Calcula a data de início da semana:
    - Próxima semana → próxima segunda (ou terça se feriado)
    - Semana atual → segunda da semana (ou terça se feriado)
    """

    # Próxima semana (quinta/sexta)
    if tipo == "PROXIMA_SEMANA":

        # Calcula próxima segunda
        dias_ate_segunda = (7 - data_ref.weekday()) % 7
        proxima_segunda = data_ref + timedelta(days=dias_ate_segunda)

        # Se for feriado → usa terça
        if eh_feriado(proxima_segunda):
            return proxima_segunda + timedelta(days=1)

        return proxima_segunda

    # Semana atual (segunda/terça)
    if tipo == "SEMANA_ATUAL":

        # Volta até segunda da semana
        segunda = data_ref - timedelta(days=data_ref.weekday())
        
        # Se segunda for feriado → usa terça
        if eh_feriado(segunda):
            return segunda + timedelta(days=1)

        return segunda

# =========================
# DECISÃO INTELIGENTE DE ENVIO
# =========================

def decidir_envio():
    """
    Decide se hoje deve enviar mensagem:

    - Segunda → envia semana atual
    - Terça → envia se segunda foi feriado
    - Sexta → envia próxima semana
    - Quinta → envia se sexta será feriado
    """

    data_hoje = hoje()
    dia = data_hoje.weekday()

    # Segunda
    if dia == 0:
        if eh_feriado(data_hoje):
            return None
        return "SEMANA_ATUAL", data_hoje

    # Terça (se segunda foi feriado)
    if dia == 1:
        if eh_feriado(data_hoje - timedelta(days=1)):
            return "SEMANA_ATUAL", data_hoje

    # Sexta
    if dia == 4:
        if eh_feriado(data_hoje):
            return None
        return "PROXIMA_SEMANA", data_hoje + timedelta(days=3)

    # Quinta (se sexta será feriado)
    if dia == 3:
        if eh_feriado(data_hoje + timedelta(days=1)):
            return "PROXIMA_SEMANA", data_hoje + timedelta(days=3)

    return None

# =========================
# ENVIO PARA TEAMS
# =========================

def enviar(pessoa1, pessoa2, semana, data_inicio):
    """
    Monta e envia o Adaptive Card para o Teams.
    """

    data_formatada = data_inicio.strftime("%d/%m/%Y")

    payload = {
        "type": "message",
        "attachments": [
            {
                "contentType": "application/vnd.microsoft.card.adaptive",
                "content": {
                    "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                    "type": "AdaptiveCard",
                    "version": "1.4",
                    "body": [

                        # Título
                        {
                            "type": "TextBlock",
                            "text": "🥚 ESCALA DE COMPRA DE OVOS 🥚",
                            "weight": "Bolder",
                            "size": "Large"
                        },

                        # Semana
                        {
                            "type": "TextBlock",
                            "text": semana,
                            "weight": "Bolder",
                            "size": "Medium",
                            "spacing": "Medium"
                        },
                        {
                            "type": "TextBlock",
                            "text": f"Início em: {data_formatada}",
                            "spacing": "None"
                        },

                        # Responsáveis
                        {
                            "type": "TextBlock",
                            "text": "👥 Responsáveis",
                            "weight": "Bolder",
                            "size": "Medium",
                            "spacing": "Medium"
                        },
                        {
                            "type": "TextBlock",
                            "text": f"{pessoa1} e {pessoa2}",
                            "spacing": "None",
                            "wrap": True
                        },

                        # Padrão
                        {
                            "type": "TextBlock",
                            "text": "🛒 Padrão de compra",
                            "weight": "Bolder",
                            "size": "Medium",
                            "spacing": "Medium"
                        },
                        {
                            "type": "TextBlock",
                            "text": "Cada um deve comprar uma cartela com 30 ovos",
                            "spacing": "None",
                            "wrap": True
                        },

                        # Rodapé
                        {
                            "type": "TextBlock",
                            "text": "🔄 Escala automática e contínua",
                            "isSubtle": True,
                            "spacing": "Medium"
                        }
                    ]
                }
            }
        ]
    }

    # Se estiver em modo teste → não envia, apenas imprime
    if MODO_TESTE:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        try:
            response = requests.post(WEBHOOK_URL, json=payload, timeout=10)
            
            if response.status_code != 200:
                print(f"Erro Teams: {response.status_code} - {response.text}")
        
        except Exception as e:
            print(f"Erro ao enviar: {e}")


# =========================
# EXECUÇÃO PRINCIPAL
# =========================

def executar():
    """
    Fluxo principal da aplicação:
    1. Verifica se já enviou hoje
    2. Decide se deve enviar
    3. Calcula responsáveis
    4. Envia mensagem
    5. Salva log
    """

    log = carregar_log()
    hoje_str = hoje().strftime("%Y-%m-%d")

    # Evita envio duplicado no mesmo dia
    if hoje_str in log:
        print("Já enviado hoje")
        return

    decisao = decidir_envio()

    # Se não for dia de envio → sai
    if not decisao:
        print("Hoje não envia")
        return

    tipo, data_ref = decisao
    
    # Define responsáveis baseado na data de referência (pode ser hoje ou próxima semana)
    pessoa1, pessoa2 = obter_par(data_ref)

    # Calcula início da semana (pode ser semana atual ou próxima semana, dependendo da decisão)
    data_inicio = calcular_inicio_semana(data_ref, tipo)

    # Define título do card baseado no tipo de envio
    if tipo == "SEMANA_ATUAL":
        semana = "📅 Semana atual"
    else:
        semana = "📅 Semana que vem (aviso antecipado)"

    # Envia mensagem para o Teams
    enviar(pessoa1, pessoa2, semana, data_inicio)

    # Salva no log para evitar duplicidade
    log[hoje_str] = {
        "pessoa1": pessoa1,
        "pessoa2": pessoa2
    }

    salvar_log(log)

    print(f"Enviado: {pessoa1} e {pessoa2} | Início: {data_inicio.strftime('%d/%m/%Y')}")

# =========================
# MAIN
# =========================

if __name__ == "__main__":
    executar()