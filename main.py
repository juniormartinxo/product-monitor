# -*- coding: utf-8 -*-
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
from datetime import datetime
import os
import json
from plyer import notification
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

load_dotenv()

import colorlog

# Configurar logging com cores
log_colors = {
    'DEBUG': 'cyan',
    'INFO': 'green',
    'WARNING': 'yellow',
    'ERROR': 'red',
    'CRITICAL': 'red,bg_white',
}

handler = colorlog.StreamHandler()
handler.setFormatter(colorlog.ColoredFormatter(
    '%(log_color)s%(asctime)s | %(levelname)-8s | %(message)s',
    datefmt='%H:%M:%S',
    log_colors=log_colors
))

logger = colorlog.getLogger(__name__)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

class AmazonMonitor:
    def __init__(self, product_url, check_interval=300):
        self.product_url = product_url
        self.check_interval = check_interval
        self.data_file = "/home/junior/apps/jm/alert/product.json"
        self.first_check = True
    
    def extract_product_data(self, page):
        """Extrai dados do produto da página"""
        try:
            # Título do produto
            title_selectors = ['#productTitle', 'h1 span', '.product-title']
            title = "N/A"
            for selector in title_selectors:
                element = page.query_selector(selector)
                if element:
                    title = element.inner_text().strip()
                    break
            
            # Preço
            price_selectors = ['.a-price-whole', '#priceblock_dealprice', '#priceblock_ourprice', '.a-price .a-offscreen']
            price = "N/A"
            for selector in price_selectors:
                element = page.query_selector(selector)
                if element:
                    price = element.inner_text().strip()
                    break
            
            # Status de disponibilidade
            availability_element = page.query_selector('#availability')
            availability = "N/A"
            if availability_element:
                availability = availability_element.inner_text().strip()
            
            # Avaliação
            rating_element = page.query_selector('.a-icon-alt')
            rating = "N/A"
            if rating_element:
                rating_text = rating_element.get_attribute('textContent') or rating_element.inner_text()
                rating = rating_text.strip() if rating_text else "N/A"
            
            return {
                "titulo": title,
                "preco": price,
                "disponibilidade": availability,
                "avaliacao": rating,
                "url": self.product_url,
                "primeira_consulta": datetime.now().isoformat(),
                "ultima_atualizacao": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"🔄 Erro ao extrair dados do produto: {e}")
            return None
    
    def save_product_data(self, data):
        """Salva dados do produto em JSON"""
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info(f"💾 Dados do produto salvos em: {self.data_file}")
        except Exception as e:
            logger.error(f"💾 Erro ao salvar dados: {e}")
    
    def load_product_data(self):
        """Carrega dados existentes do produto"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                logger.info("📂 Dados do produto carregados do arquivo existente")
                self.first_check = False
                return data
        except Exception as e:
            logger.error(f"📂 Erro ao carregar dados: {e}")
        return None
        
    def check_availability(self):
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    viewport={'width': 1920, 'height': 1080},
                    extra_http_headers={
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                        'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
                        'Accept-Encoding': 'gzip, deflate, br',
                        'DNT': '1',
                        'Connection': 'keep-alive',
                        'Upgrade-Insecure-Requests': '1',
                    }
                )
                page = context.new_page()
                
                # Navegar para a página do produto com timeout maior
                page.goto(self.product_url, wait_until='domcontentloaded', timeout=60000)
                
                # Aguardar um pouco para garantir que tudo carregou
                page.wait_for_timeout(3000)
                
                # Verificar se há tela de verificação/captcha
                continue_button = page.query_selector('button.a-button-text[alt="Continuar comprando"]')
                if continue_button:
                    logger.info("🔓 Tela de verificação detectada - clicando 'Continuar comprando'")
                    continue_button.click()
                    page.wait_for_timeout(5000)
                    logger.info("✅ Verificação contornada - carregando página do produto")
                
                # Tirar screenshot para debug
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                screenshot_path = f"/home/junior/apps/jm/alert/screenshots/debug_{timestamp}.png"
                page.screenshot(path=screenshot_path, full_page=True)
                logger.debug(f"📸 Screenshot salvo: {screenshot_path}")
                
                # Na primeira consulta, extrair e salvar dados do produto
                if self.first_check:
                    logger.info("🔍 Primeira consulta - extraindo dados do produto...")
                    product_data = self.extract_product_data(page)
                    if product_data:
                        self.save_product_data(product_data)
                        logger.info(f"📋 Produto: {product_data['titulo']}")
                        logger.info(f"💰 Preço: {product_data['preco']}")
                    self.first_check = False
                
                # Verificar elementos visuais específicos de indisponibilidade primeiro
                unavailable_selectors = [
                    '[data-feature-name="availability"] .a-color-state',
                    '.a-color-state:has-text("Temporariamente indisponível")',
                    '.a-color-secondary:has-text("indisponível")',
                    '#availability .a-color-state'
                ]
                
                for selector in unavailable_selectors:
                    element = page.query_selector(selector)
                    if element:
                        element_text = element.inner_text().lower()
                        if any(word in element_text for word in ['indisponível', 'fora de estoque', 'não disponível']):
                            logger.warning(f"❌ Produto INDISPONÍVEL - elemento visual: '{element_text.strip()}'")
                            browser.close()
                            return False
                
                # Verificar especificamente no container de disponibilidade
                availability_element = page.query_selector('#availability')
                if availability_element:
                    availability_text = availability_element.inner_text().lower()
                    logger.info(f"🔍 Container disponibilidade: '{availability_text.strip()}'")
                    
                    if "em estoque" in availability_text:
                        logger.info("✅ Produto DISPONÍVEL - 'Em estoque' encontrado!")
                        browser.close()
                        return True
                    elif any(word in availability_text for word in ['indisponível', 'fora de estoque', 'não disponível']):
                        logger.warning(f"❌ Produto INDISPONÍVEL - container: '{availability_text.strip()}'")
                        browser.close()
                        return False
                else:
                    logger.debug("🔍 Container #availability não encontrado")
                
                # Verificar se há botão "Adicionar ao carrinho" ativo
                add_to_cart_buttons = [
                    '#add-to-cart-button:not([disabled])',
                    'input[name="submit.add-to-cart"]:not([disabled])',
                    '.a-button-primary:has-text("Adicionar ao carrinho")',
                    '.a-button-primary:has-text("Comprar agora")'
                ]
                
                for selector in add_to_cart_buttons:
                    button = page.query_selector(selector)
                    if button and button.is_visible():
                        logger.info("✅ Produto DISPONÍVEL - botão 'Adicionar ao carrinho' ativo!")
                        browser.close()
                        return True
                
                # Fallback: verificar na página inteira
                page_text = page.inner_text('body').lower()
                if "em estoque" in page_text and not any(word in page_text for word in ['temporariamente indisponível', 'não disponível']):
                    logger.info("✅ Produto DISPONÍVEL - 'Em estoque' sem indicadores negativos!")
                    browser.close()
                    return True
                
                logger.warning("❌ Produto não disponível - critérios não atendidos")
                browser.close()
                return False
                
        except Exception as e:
            logger.error(f"💥 Erro ao verificar disponibilidade: {e}")
            return None
    
    def send_desktop_notification(self):
        try:
            # Tentar notificação nativa primeiro
            notification.notify(
                title="Produto Disponível!",
                message=f"O produto que você está monitorando está disponível para compra!\n{self.product_url}",
                timeout=10
            )
            logger.info("🔔 Notificação desktop enviada")
        except Exception as e:
            # Fallback para notify-send se disponível
            try:
                import subprocess
                subprocess.run([
                    'notify-send', 
                    'Produto Disponível!', 
                    f'O produto está disponível para compra!\n{self.product_url}'
                ], check=True)
                logger.info("🔔 Notificação desktop enviada via notify-send")
            except (subprocess.CalledProcessError, FileNotFoundError):
                # Fallback final: mostrar no console
                print("\n" + "="*60)
                print("🎉 PRODUTO DISPONÍVEL PARA COMPRA! 🎉")
                print("="*60)
                print(f"🔗 URL: {self.product_url}")
                print(f"⏰ Verificado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
                print("="*60 + "\n")
                logger.info("🔔 Notificação exibida no console")
    
    def send_email_notification(self, email_config):
        try:
            msg = MIMEMultipart()
            msg['From'] = email_config['from_email']
            msg['To'] = email_config['to_email']
            msg['Subject'] = "Produto Amazon Disponível!"
            
            body = f"""
            Boa notícia!
            
            O produto que você está monitorando na Amazon está disponível para compra:
            {self.product_url}
            
            Verificado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            server = smtplib.SMTP(email_config['smtp_server'], email_config['smtp_port'])
            server.starttls()
            server.login(email_config['from_email'], email_config['password'])
            server.send_message(msg)
            server.quit()
            
            logger.info("📧 Email de notificação enviado com sucesso")
        except Exception as e:
            logger.error(f"📧 Erro ao enviar email: {e}")
    
    def start_monitoring(self, email_config=None):
        print("\n" + "="*70)
        print("🚀 AMAZON MONITOR - INICIANDO MONITORAMENTO")
        print("="*70)
        logger.info(f"🔗 URL do produto: {self.product_url}")
        logger.info(f"⏱️  Intervalo de verificação: {self.check_interval} segundos")
        
        # Verificar se já existe dados do produto
        existing_data = self.load_product_data()
        if existing_data:
            logger.info(f"📋 Produto monitorado: {existing_data.get('titulo', 'N/A')}")
            logger.info(f"💰 Último preço: {existing_data.get('preco', 'N/A')}")
        
        print("="*70 + "\n")
        
        check_count = 0
        
        while True:
            try:
                check_count += 1
                logger.info(f"🔍 Verificação #{check_count} - Analisando disponibilidade...")
                is_available = self.check_availability()
                
                if is_available is True:
                    print("\n" + "🎉"*25)
                    logger.info("🎉 PRODUTO DISPONÍVEL ENCONTRADO!")
                    print("🎉"*25 + "\n")
                    self.send_desktop_notification()
                    
                    if email_config:
                        self.send_email_notification(email_config)
                    
                    logger.info("✅ Monitoramento concluído com sucesso - produto encontrado!")
                    logger.info("🛑 Aplicação será finalizada")
                    break
                elif is_available is False:
                    logger.warning("⏳ Produto ainda indisponível")
                else:
                    logger.error("⚠️  Não foi possível verificar a disponibilidade")
                
                logger.info(f"😴 Aguardando {self.check_interval} segundos para próxima verificação...")
                time.sleep(self.check_interval)
                
            except KeyboardInterrupt:
                logger.info("Monitoramento interrompido pelo usuário")
                break
            except Exception as e:
                logger.error(f"💥 Erro durante o monitoramento: {e}")
                logger.info("🔄 Tentando novamente em 60 segundos...")
                time.sleep(60)

if __name__ == "__main__":
    PRODUCT_URL = "https://www.amazon.com.br/dp/8542234081/?coliid=I1CJ7Q6PEE62A8&colid=AU6V2U4PQQMT&psc=0&ref_=list_c_wl_lv_ov_lig_dp_it"
    #PRODUCT_URL = "https://www.amazon.com.br/livro-voc%C3%AA-gostaria-seus-tivessem/dp/8584391606/ref=wsixn_inc_v1_d_sccl_1_7/137-7182940-1763300?pd_rd_w=BSQfP&content-id=amzn1.sym.d36dde69-f862-4af6-bcf8-fae00b203821&pf_rd_p=d36dde69-f862-4af6-bcf8-fae00b203821&pf_rd_r=AFE35RQ140BXDADH9GWP&pd_rd_wg=Ahxay&pd_rd_r=4b9a725b-899c-43b6-b40d-6216f1dcd230&pd_rd_i=8584391606&psc=1"
    #PRODUCT_URL = "https://www.amazon.com.br/Carrinho-Ferramentas-Desmont%C3%A1vel-Semifechado-VDO2631/dp/B079JSMHP9?ref=dlx_deals_dg_dcl_B079JSMHP9_dt_sl14_36_pi&pf_rd_r=9KNFBRJ2S0Y519D3Q990&pf_rd_p=7bf52575-68ff-44b0-9358-534353e02336"
    
    CHECK_INTERVAL = 300  # 5 minutos
    
    email_config = {
        'from_email': os.getenv('FROM_EMAIL', ''),
        'password': os.getenv('EMAIL_PASSWORD', ''),
        'to_email': os.getenv('TO_EMAIL', ''),
        'smtp_server': 'smtp.gmail.com',
        'smtp_port': 587
    }
    
    if not all([email_config['from_email'], email_config['password'], email_config['to_email']]):
        logger.warning("📧 Configuração de email não encontrada - usando apenas notificações desktop")
        email_config = None
    
    monitor = AmazonMonitor(PRODUCT_URL, CHECK_INTERVAL)
    monitor.start_monitoring(email_config)