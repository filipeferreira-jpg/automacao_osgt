"""
Gerenciador de Itens da Fatura
Responsável por carregar, armazenar e iterar os itens vindos do N8N
"""

import requests
import json

class GerenciadorItens:
    """
    Gerencia a matriz de itens recebida do N8N
    Controla o estado de cada item durante o processamento RPA
    """

    def __init__(self, base_url='https://n8n2.titoonline.com.br'):
        self.base_url = base_url
        self.itens = []
        self.item_atual_index = 0
        self.fatura_id = None
        # cabecalho fatura
        self.numero_fatura = None
        self.data_fatura = None

    # ─────────────────────────────────────────
    # CARREGAMENTO e ENVIO DE DADOS
    # ─────────────────────────────────────────

    def carregar_do_n8n(self, fatura_id):
        """
        Carrega itens da fatura do webhook N8N

        Args:
            fatura_id: ID da fatura no banco

        Returns:
            True se carregou com sucesso, False caso contrário
        """
        url = f"{self.base_url}/webhook/phinia-query?id={fatura_id}"

        print(f"🌐 Carregando fatura ID {fatura_id}...")

        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            dados = response.json()

            # Retorno: lista com objeto contendo invoice_id e items aninhado
            if isinstance(dados, list) and len(dados) > 0:
                primeiro = dados[0]

                # Novo formato: { "invoice_id": X, "items": [...] }
                if 'items' in primeiro:
                    items_raw = primeiro['items']
                    # extrair de 'primeiro'
                    self.numero_fatura = primeiro.get('invoice_number')
                    self.data_fatura = primeiro.get('invoice_date')

                    # items pode vir como string JSON ou já como lista
                    if isinstance(items_raw, str):
                        items_raw = json.loads(items_raw)

                    # Trata colchetes duplos [[...]]
                    if isinstance(items_raw, list) and len(items_raw) > 0 and isinstance(items_raw[0], list):
                        items_raw = items_raw[0]

                    self.itens = items_raw

                # Formato antigo: lista direta de itens
                else:
                    self.itens = dados

            elif isinstance(dados, dict) and 'items' in dados:
                self.itens = dados['items']

            else:
                print("❌ Estrutura JSON não reconhecida")
                return False

            self.fatura_id = fatura_id
            self.item_atual_index = 0

            print(f"✅ {len(self.itens)} itens carregados")
            return True

        except Exception as e:
            print(f"❌ Erro ao carregar fatura: {e}")
            return False

    def enviar_relatorio_consulta(self, itens_nao_encontrados, itens_sem_saldo, itens_encontrados):
        """
        Envia relatório final consolidado ao N8N contendo:
        - Itens não encontrados no sistema
        - Itens com divergência de quantidade

        Args:
            itens_nao_encontrados: Lista de dicts com itens que não foram encontrados
            itens_sem_saldo: Lista de dicts com itens com quantidade insuficiente

        Returns:
            True se enviou com sucesso, False caso contrário
        """
        url = f"{self.base_url}/webhook/phinia-not-found"

        payload = {
            "fatura_id": self.fatura_id,
            "resumo": {
                "total_nao_encontrados" : len(itens_nao_encontrados),
                "total_divergentes_qtde": len(itens_sem_saldo),
                "total_encontrados"     : len(itens_encontrados),
            },
            "itens_nao_encontrados"  : itens_nao_encontrados,
            "itens_sem_saldo" : itens_sem_saldo,
            "itens_encontrados"      : itens_encontrados,
        }

        print(f"\n📤 Enviando relatório final ao N8N...")
        print(f"   ❌ Não encontrados:   {len(itens_nao_encontrados)}")
        print(f"   ⚠️  Qtde. divergente: {len(itens_sem_saldo)}")

        try:
            response = requests.post(
                url,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            response.raise_for_status()

            print(f"✅ N8N recebeu o relatório com sucesso!")
            return True

        except Exception as e:
            print(f"❌ Erro ao enviar relatório para N8N: {e}")
            return False

    def enviar_relatorio_montagem(self, itens_nao_encontrados, itens_sem_saldo, itens_selecionados):
        """
        Envia relatório final da MONTAGEM DO RASCUNHO ao N8N.
        Usa webhook separado para não sobrescrever o retorno do load_invoice.

        Args:
            itens_nao_encontrados: itens que não foram encontrados na grade
            itens_sem_saldo: itens com quantidade insuficiente na grade
            itens_selecionados: itens selecionados com sucesso

        Returns:
            True se enviou com sucesso, False caso contrário
        """
        url = f"{self.base_url}/webhook/phinia-relatorio-montagem"

        payload = {
            "fatura_id": self.fatura_id,
            "origem": "monta_invoice",
            "resumo": {
                "total_selecionados"    : len(itens_selecionados),
                "total_nao_encontrados" : len(itens_nao_encontrados),
                "total_sem_saldo"       : len(itens_sem_saldo),
            },
            "itens_selecionados"    : itens_selecionados,
            "itens_nao_encontrados" : itens_nao_encontrados,
            "itens_sem_saldo"       : itens_sem_saldo,
        }

        print(f"\n📤 Enviando relatório de montagem ao N8N...")
        print(f"   ✅ Selecionados:      {len(itens_selecionados)}")
        print(f"   ❌ Não encontrados:   {len(itens_nao_encontrados)}")
        print(f"   ⚠️  Sem saldo:        {len(itens_sem_saldo)}")

        try:
            response = requests.post(
                url,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            response.raise_for_status()
            print(f"✅ N8N recebeu o relatório de montagem com sucesso!")
            return True

        except Exception as e:
            print(f"❌ Erro ao enviar relatório de montagem: {e}")
            return False
    # ─────────────────────────────────────────
    # ITERAÇÃO
    # ─────────────────────────────────────────

    def tem_proximo(self):
        """
        Verifica se ainda há itens para processar

        Returns:
            True se há próximo item, False se terminou
        """
        return self.item_atual_index < len(self.itens)

    def proximo_item(self):
        """
        Retorna o próximo item e avança o índice

        Returns:
            Dict com dados do item ou None se não houver mais
        """
        if not self.tem_proximo():
            return None

        item = self.itens[self.item_atual_index]
        self.item_atual_index += 1
        return item

    def item_atual(self):
        """
        Retorna o item atual sem avançar o índice

        Returns:
            Dict com dados do item atual ou None
        """
        if not self.tem_proximo():
            return None
        return self.itens[self.item_atual_index]

    def resetar(self):
        """Reinicia a iteração do primeiro item"""
        self.item_atual_index = 0
        print("🔄 Iteração reiniciada do primeiro item")

    # ─────────────────────────────────────────
    # ACESSO AOS CAMPOS DO ITEM
    # ─────────────────────────────────────────

    def get_id(self, item):
        """Retorna o ID único do item (se existir no payload)"""
        return item.get('id')

    def get_part_number(self, item):
        """Retorna o Part Number do item já convertido pelo DE-PARA (campo part_number_sistema)"""
        return str(item.get('part_number_sistema', item.get('part_number', ''))).strip()

    def get_quantity(self, item):
        """Retorna a quantidade do item como float"""
        return float(item.get('quantity', 0))

    def get_num_ordem(self, item):
        """Retorna o número da ordem do item"""
        return str(item.get('custom_order_nro', '')).strip()

    def get_net_price(self, item):
        """Retorna o preço unitário como float"""
        return float(item.get('net_price', 0))

    def get_total_value(self, item):
        """Retorna o valor total como float"""
        return float(item.get('total_value', 0))

    # ─────────────────────────────────────────
    # INFORMAÇÕES / STATUS
    # ─────────────────────────────────────────

    def total_itens(self):
        """Retorna total de itens"""
        return len(self.itens)

    def progresso(self):
        """
        Retorna progresso atual

        Returns:
            Dict com 'atual', 'total', 'percentual'
        """
        return {
            'atual': self.item_atual_index,
            'total': len(self.itens),
            'percentual': round((self.item_atual_index / len(self.itens)) * 100, 1)
            if self.itens else 0
        }