# 🥚 Escala Automática de Compra de Ovos

Automação desenvolvida em Python para gerenciar e notificar automaticamente, via Microsoft Teams, a escala semanal de responsáveis pela compra de ovos.

---

## 🚀 Funcionalidades

- ✅ Geração automática de escala semanal
- 👥 Sempre 2 pessoas por semana
- 🔄 Rotação inteligente (sem repetição consecutiva)
- 🔁 Suporte para número par e ímpar de pessoas
- 📅 Tratamento de feriados (Brasil + Minas Gerais + Belo Horizonte)
- 📢 Envio automático de mensagens no Microsoft Teams
- ⏰ Lógica inteligente de envio:
  - Sexta-feira → aviso da próxima semana
  - Quinta-feira → antecipa se sexta for feriado
  - Segunda-feira → aviso da semana atual
  - Terça-feira → antecipa se segunda for feriado
- 🛑 Evita envio duplicado no mesmo dia
- 📊 Registro automático em log (`log_ovos.json`)

---

## 🧩 Tecnologias utilizadas

- Python 3
- requests
- python-dotenv
- holidays
- Microsoft Teams (Incoming Webhook)
- Windows Task Scheduler

---

## ⚙️ Configuração

### 1. Clonar o projeto
```bash
git clone https://github.com/seu-usuario/seu-repositorio.git
cd seu-repositorio
```

### 2. Instalar dependências
pip install -r requirements.txt

### 3. Criar arquivo .env
Na raiz do projeto, crie um arquivo chamado .env:
WEBHOOK_URL=https://seu-webhook-do-teams

### 4. Executar projeto
python script.py

### 🖥️ Execução em produção

O sistema foi projetado para rodar via Agendador de Tarefas do Windows.

### 📅 Dias recomendados:
Segunda-feira (09:00)
Terça-feira (backup caso segunda seja feriado)
Quinta-feira (09:00)
Sexta-feira (backup caso sexta seja feriado)

### ⚠️ O próprio código decide automaticamente se deve enviar a mensagem ou não.

### 📦 Gerar executável (.exe)
Para rodar em servidor:

pip install pyinstaller
pyinstaller --onefile --noconsole script.py

O executável será gerado em:

dist/script.exe

### 📁 Estrutura do projeto
/projeto
 ├── script.py
 ├── .env               # NÃO subir para o GitHub
 ├── .gitignore
 ├── requirements.txt
 ├── log_ovos.json      # Gerado automaticamente

### 🔐 Segurança
🔒 Uso de .env para proteger o webhook
🚫 .gitignore impede envio de dados sensíveis para o GitHub

### 🧠 Lógica da escala
### 🔹 Número par de pessoas
1-2
3-4
5-6
7-8
...
(repete)

### 🔹 Número ímpar de pessoas
1-2
3-4
5-6
...
último-1
2-3
4-5
...
(rotativo contínuo)

### 📊 Log de execução
O sistema gera automaticamente o arquivo:
log_ovos.json

Contendo:
Data do envio
Responsáveis da semana

### 🧪 Modo de teste
Você pode simular execuções sem enviar para o Teams:
MODO_TESTE = True
DATA_FIXA = datetime(2026, 4, 10).date()  # simula uma data

### 🚀 Melhorias futuras
Integração com Microsoft Graph (menções no Teams)
Dashboard de acompanhamento
Interface web
Banco de dados
API REST

### 👨‍💻 Autor
Desenvolvido por Leandro Ricardo

### 📄 Licença
Este projeto é de uso interno/educacional, podendo ser adaptado conforme necessidade.