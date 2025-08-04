# 🚀 Product Monitor

Monitor de disponibilidade de produtos dos maiores players da internet com notificações automáticas via desktop e email.

## ✨ Funcionalidades

- 🔍 **Monitoramento Contínuo**: Verifica a disponibilidade de produtos Amazon automaticamente
- 🎯 **Detecção Inteligente**: Usa Playwright para contornar proteções anti-bot da Amazon
- 🔔 **Notificações Múltiplas**: Desktop e email quando o produto fica disponível
- 💾 **Persistência de Dados**: Salva informações do produto em JSON
- 📸 **Debug Visual**: Screenshots automáticos para troubleshooting
- 🎨 **Logs Coloridos**: Interface visual com emojis e cores
- ⚙️ **Configurável**: Intervalo de verificação e configurações personalizáveis

## 🛠️ Instalação

### Pré-requisitos
- Python 3.8+
- Sistema operacional: Linux, macOS ou Windows

### Configuração

1. **Clone o repositório**
```bash
git clone <repository-url>
cd alert
```

2. **Crie o ambiente virtual**
```bash
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# ou
venv\Scripts\activate     # Windows
```

3. **Instale as dependências**
```bash
pip install -r requirements.txt
playwright install chromium
```

4. **Configure as notificações por email (opcional)**
```bash
cp .env.example .env
# Edite o arquivo .env com suas credenciais
```

Exemplo do arquivo `.env`:
```env
FROM_EMAIL=seu_email@gmail.com
EMAIL_PASSWORD=sua_senha_de_app
TO_EMAIL=destino@gmail.com
```

> **Nota**: Para Gmail, use uma [senha de app](https://support.google.com/accounts/answer/185833) em vez da senha normal.

## 🚦 Como Usar

### Configuração Básica

1. **Configure a URL do produto** no arquivo `main.py`:
```python
PRODUCT_URL = "https://www.amazon.com.br/dp/SEU_PRODUTO_ID"
```

2. **Execute o monitor**:
```bash
python main.py
```

### Primeira Execução

Na primeira execução, o sistema irá:
- Extrair dados completos do produto (título, preço, avaliação)
- Salvar as informações em `product.json`
- Iniciar o monitoramento contínuo

### Monitoramento

O sistema verifica a disponibilidade a cada 5 minutos (configurável) e:
- ✅ **Produto disponível**: Envia notificações e para o monitoramento
- ⏳ **Produto indisponível**: Continua monitorando
- ⚠️ **Erro de conexão**: Tenta novamente em 60 segundos

## ⚙️ Configurações

### Intervalo de Verificação
```python
CHECK_INTERVAL = 300  # 5 minutos (em segundos)
```

### Notificações Desktop

O sistema usa uma abordagem de fallback:
1. Notificações nativas (plyer)
2. Sistema notify-send (Linux)
3. Output no console

### Estrutura de Arquivos

```
alert/
├── main.py              # Aplicação principal
├── requirements.txt     # Dependências Python
├── .env                 # Configurações de email (criar)
├── .env.example         # Exemplo de configuração
├── product.json         # Dados do produto (auto-gerado)
├── screenshots/         # Screenshots de debug
├── venv/               # Ambiente virtual
└── README.md           # Este arquivo
```

## 🔧 Desenvolvimento

### Estrutura do Código

- **AmazonMonitor**: Classe principal que gerencia todo o processo
- **check_availability()**: Lógica de detecção de disponibilidade
- **extract_product_data()**: Extração de dados do produto
- **send_notifications()**: Sistema de notificações múltiplas

### Logs e Debug

O sistema inclui logs coloridos com emojis:
- 🚀 Inicialização
- 🔍 Verificações de disponibilidade
- ✅ Operações bem-sucedidas
- ❌ Erros e produtos indisponíveis
- 📧 Operações de email
- 📸 Screenshots de debug

### Screenshots de Debug

Automaticamente salvos em `screenshots/` com timestamp:
```
debug_YYYYMMDD_HHMMSS.png
```

## 🤔 Como Funciona

### 1. Detecção Anti-Bot
- Usa Playwright com navegador real (Chromium)
- Headers HTTP realistas
- Detecção automática de páginas de verificação da Amazon
- Aguarda carregamento completo das páginas

### 2. Lógica de Disponibilidade
O sistema verifica múltiplos indicadores:
- Container `#availability` com texto "Em estoque"
- Elementos visuais específicos da Amazon
- Botões "Adicionar ao carrinho" ativos
- Ausência de mensagens de indisponibilidade

### 3. Persistência
- Primeira consulta: salva dados completos em JSON
- Consultas seguintes: carrega dados existentes
- Mantém histórico de timestamps

## 🚨 Troubleshooting

### Problemas Comuns

**"Erro 500" ou timeouts da Amazon**
- A Amazon pode estar bloqueando muitas requisições
- Aumente o intervalo entre verificações
- Verifique se a URL do produto está correta

**Notificações desktop não funcionam**
- Instale: `sudo apt install libnotify-bin` (Ubuntu/Debian)
- O sistema tem fallback para console

**Email não está sendo enviado**
- Verifique as credenciais no arquivo `.env`
- Use senha de app para Gmail
- Confirme que o SMTP está configurado corretamente

### Debug

Use os screenshots automáticos em `screenshots/` para verificar:
- Se a página está carregando corretamente
- Se há captchas ou páginas de verificação
- Se os elementos de disponibilidade estão presentes

## 📄 Licença

Este projeto é para fins educacionais. Use responsavelmente e respeite os termos de serviço da Amazon.

## 🤝 Contribuição

Sinta-se à vontade para:
- Reportar bugs
- Sugerir melhorias
- Contribuir com código
- Melhorar a documentação

---

**⚠️ Aviso**: Este projeto é apenas para monitoramento pessoal. Use com moderação para evitar sobrecarregar os servidores da Amazon.
