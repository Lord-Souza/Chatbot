import json
import logging
import datetime
from rasa_sdk import Action, Tracker
from rasa_sdk.events import SlotSet
from rasa_sdk.executor import CollectingDispatcher
import requests
from typing import Any, Text, Dict, List, Union, Tuple
import re

import json
import logging
import datetime
from rasa_sdk import Action, Tracker
from rasa_sdk.events import SlotSet
from rasa_sdk.executor import CollectingDispatcher
import requests
from typing import Any, Text, Dict, List, Union, Tuple
import re

class ActionGetAtendimentos(Action):
    print("============teste da API===========")    
    def name(self) -> Text:
        return "action_get_atendimentos"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        try:
            api_url = "http://localhost:8080/bot/getAtendimentos"
            response = requests.get(api_url)
            response.raise_for_status()  # Verificar se houve algum erro na solicitação
            atendimentos = response.json()

            message_text = tracker.latest_message.get('text').lower()

            # Usando expressão regular para encontrar o número do atendimento na mensagem
            numero_atendimento = re.search(r'\b\d{3}\b', message_text)

            if numero_atendimento:
                numero_atendimento = int(numero_atendimento.group())
                atendimento_encontrado = next((atendimento for atendimento in atendimentos if atendimento.get("nrAtendimento") == numero_atendimento), None)
                if atendimento_encontrado:
                    formatted_info = self._formatar_atendimento(atendimento_encontrado)
                    dispatcher.utter_message(formatted_info)
                else:
                    dispatcher.utter_message(f"Atendimento de número {numero_atendimento} não encontrado.")
            else:
                entities = tracker.latest_message.get('entities')
                if entities:
                    medicos = {}
                    for entity in entities:
                        if entity['entity'] == 'nmMedico':
                            nome_medico = entity['value']
                            atendimentos_medico = [atendimento for atendimento in atendimentos if atendimento.get("nmMedico") == nome_medico]
                            if atendimentos_medico:
                                numeros_atendimentos = len(atendimentos_medico)
                                dispatcher.utter_message(f"Total de atendimentos do Dr. {nome_medico}: {numeros_atendimentos}")
                                for atendimento in atendimentos_medico:
                                    formatted_info = self._formatar_atendimento(atendimento)
                                    dispatcher.utter_message(formatted_info)
                            else:
                                dispatcher.utter_message(f"Atendimentos do Dr. {nome_medico} não encontrados.")
                        elif entity['entity'] == 'data':
                            data_referencia = entity['value']
                            data_referencia_formatada = self._formatar_data(data_referencia)
                            atendimentos_dia = [atendimento for atendimento in atendimentos if self._formatar_data(atendimento.get("dtEntrada")) == data_referencia_formatada]
                            if atendimentos_dia:
                                dispatcher.utter_message(f"Atendimentos do dia {data_referencia}:")
                                for atendimento in atendimentos_dia:
                                    formatted_info = self._formatar_atendimento(atendimento)
                                    dispatcher.utter_message(formatted_info)
                            else:
                                dispatcher.utter_message(f"Atendimentos do dia {data_referencia} não encontrados.")
                    
                elif 'quantos atendimentos' in message_text and 'esta semana' in message_text:
                    atendimentos_semana = [atendimento for atendimento in atendimentos if self._esta_semana(atendimento.get("data_atendimento"))]
                    numeros_atendimentos_semana = len(atendimentos_semana)
                    dispatcher.utter_message(f"Tivemos {numeros_atendimentos_semana} atendimentos esta semana.")
                elif 'quantos atendimentos' in message_text and 'último mês' in message_text:
                    atendimentos_mes = [atendimento for atendimento in atendimentos if self._este_mes(atendimento.get("data_atendimento"))]
                    numeros_atendimentos_mes = len(atendimentos_mes)
                    dispatcher.utter_message(f"Tivemos {numeros_atendimentos_mes} atendimentos no último mês.")
                elif 'quantos atendimentos' in message_text:
                    total_atendimentos = len(atendimentos)
                    dispatcher.utter_message(f"Total de atendimentos: {total_atendimentos}")
                else:
                    dispatcher.utter_message("Por favor, forneça o número do atendimento, o nome do médico ou a data de referência.")
        except requests.exceptions.RequestException as e:
            dispatcher.utter_message("Ocorreu um erro ao obter os dados da API.")
        except Exception as e:
            dispatcher.utter_message("Ocorreu um erro ao processar a solicitação.")

        return []

    def _formatar_atendimento(self, atendimento: Dict[str, Any]) -> str:
        formatted_info = "\n".join([f"Número do Atendimento: {atendimento['nrAtendimento']}, Médico: {atendimento['nmMedico']}, Data de Entrada: {atendimento['dtEntrada']}, Convênio: {atendimento['dsConvenio']}"])
        return formatted_info

    def _formatar_data(self, data: str) -> datetime.date:
        for fmt in ('%d-%m-%y', '%d/%m/%y', '%d de %b %y', '%d %b %y', '%d %B %y'):
            try:
                return datetime.datetime.strptime(data, fmt).strftime('%Y-%m-%d')
            except ValueError:
                pass
        raise ValueError('Data fornecida em formato inválido')

    def _esta_semana(self, data: str) -> bool:
        if not data:
            return False

        data_atendimento = self._formatar_data(data)
        hoje = datetime.datetime.now()
        inicio_semana = hoje - datetime.timedelta(days=hoje.weekday())
        final_semana = inicio_semana + datetime.timedelta(days=6)
        return inicio_semana.date() <= data_atendimento <= final_semana.date()

    def _este_mes(self, data: str) -> bool:
        if not data:
            return False

        data_atendimento = self._formatar_data(data)
        hoje = datetime.datetime.now()
        inicio_mes = hoje.replace(day=1)
        ultimo_dia_mes = hoje.replace(day=1, month=hoje.month % 12 + 1) - datetime.timedelta(days=1)
        return inicio_mes.date() <= data_atendimento <= ultimo_dia_mes.date()
