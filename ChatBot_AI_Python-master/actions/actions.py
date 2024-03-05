from dataclasses import dataclass
from typing import List, Dict, Any, Text
import datetime
import re
import requests
from rasa_sdk import Action, Tracker
from rasa_sdk.events import SlotSet
from rasa_sdk.executor import CollectingDispatcher

@dataclass
class ChatResponse:
    message: str
    action: str
    entities: Dict[Text, Any]

class ActionGetAtendimentos(Action):
    def name(self) -> Text:
        return "action_get_atendimentos"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[ChatResponse]:
        try:
            api_url = "http://localhost:8080/bot/getAtendimentos"
            response = requests.get(api_url)
            response.raise_for_status()  # Verificar se houve algum erro na solicitação
            atendimentos = response.json()

            # Identificar o convênio na mensagem do usuário usando expressão regular
            message_text = tracker.latest_message.get('text')
            convenio_intervalo_datas = re.search(r'Mostre os atendimentos do (.+) entre (\d{1,2}[/-]\d{1,2}[/-]\d{2,4}) e (\d{1,2}[/-]\d{1,2}[/-]\d{2,4})', message_text)

            if convenio_intervalo_datas:
                convenio = convenio_intervalo_datas.group(1).lower()
                data_inicial = convenio_intervalo_datas.group(2)
                data_final = convenio_intervalo_datas.group(3)

                # Formatando as datas de referência
                data_inicial_formatada = self._formatar_data(data_inicial)
                data_final_formatada = self._formatar_data(data_final)

                # Filtrar os atendimentos pelo convênio e intervalo de datas especificados
                atendimentos_filtrados = [atendimento for atendimento in atendimentos if convenio in atendimento.get("dsConvenio").lower() and self._comparar_datas_intervalo(atendimento.get("dtEntrada"), data_inicial_formatada, data_final_formatada)]

                if atendimentos_filtrados:
                    dispatcher.utter_message(f"Atendimentos do convênio '{convenio}' entre {data_inicial_formatada} e {data_final_formatada}: {len(atendimentos_filtrados)}\n")
                    for atendimento in atendimentos_filtrados:
                        formatted_info = self._formatar_atendimento(atendimento)
                        dispatcher.utter_message(formatted_info)
                else:
                    dispatcher.utter_message(f"Atendimentos do convênio '{convenio}' entre {data_inicial_formatada} e {data_final_formatada} não encontrados.")
                return [ChatResponse(message=dispatcher.messages, action="action_get_atendimentos", entities={})]

            # Identificar o convênio na mensagem do usuário usando expressão regular
            convenio_especifico = re.search(r'Mostre os atendimentos do (.+)', message_text)

            if convenio_especifico:
                convenio = convenio_especifico.group(1).lower()

                # Filtrar os atendimentos pelo convênio especificado
                atendimentos_convenio = [atendimento for atendimento in atendimentos if convenio in atendimento.get("dsConvenio").lower()]

                if atendimentos_convenio:
                    dispatcher.utter_message(f"Atendimentos do convênio '{convenio}': {len(atendimentos_convenio)}\n")
                    for atendimento in atendimentos_convenio:
                        formatted_info = self._formatar_atendimento(atendimento)
                        dispatcher.utter_message(formatted_info)
                else:
                    dispatcher.utter_message(f"Atendimentos do convênio '{convenio}' não encontrados.")
                return [ChatResponse(message=dispatcher.messages, action="action_get_atendimentos", entities={})]

            # Identificar datas na mensagem do usuário usando expressão regular
            datas_encontradas = re.findall(r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b', message_text)

            if datas_encontradas:
                for data in datas_encontradas:
                    # Formatando a data de referência
                    data_referencia_formatada = self._formatar_data(data)

                    atendimentos_dia = [atendimento for atendimento in atendimentos if self._comparar_datas(atendimento.get("dtEntrada"), data_referencia_formatada)]

                    if atendimentos_dia:
                        dispatcher.utter_message(f"Atendimentos do dia {data_referencia_formatada}: {len(atendimentos_dia)}\n")
                        for atendimento in atendimentos_dia:
                            formatted_info = self._formatar_atendimento(atendimento)
                            dispatcher.utter_message(formatted_info)
                    else:
                        dispatcher.utter_message(f"Atendimentos do dia {data_referencia_formatada} não encontrados.")

            else:
                # Usando expressão regular para encontrar o número do atendimento na mensagem
                message_text = tracker.latest_message.get('text').lower()
                numero_atendimento = re.search(r'\b\d{5}\b', message_text)

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
                                # A busca por data já foi implementada acima
                                pass
                            elif entity['entity'] == 'nmPaciente':
                                nome_paciente = entity['value']
                                atendimentos_paciente = [atendimento for atendimento in atendimentos if atendimento.get("nmPaciente") == nome_paciente]
                                if atendimentos_paciente:
                                    numeros_atendimentos = len(atendimentos_paciente)
                                    dispatcher.utter_message(f"Total de atendimentos do Paciente {nome_paciente}: {numeros_atendimentos}")
                                    for atendimento in atendimentos_paciente:
                                        formatted_info = self._formatar_atendimento(atendimento)
                                        dispatcher.utter_message(formatted_info)
                                else:
                                    dispatcher.utter_message(f"Atendimentos do Paciente {nome_paciente} não encontrados.")
                            elif entity['entity'] == 'dsClinica':
                                nome_clinica = entity['value']
                                atendimentos_clinica = [atendimento for atendimento in atendimentos if atendimento.get("dsClinica") == nome_clinica]
                                if atendimentos_clinica:
                                    numeros_atendimentos = len(atendimentos_clinica)
                                    dispatcher.utter_message(f"Total de atendimentos na Clínica {nome_clinica}: {numeros_atendimentos}")
                                    for atendimento in atendimentos_clinica:
                                        formatted_info = self._formatar_atendimento(atendimento)
                                        dispatcher.utter_message(formatted_info)
                                else:
                                    dispatcher.utter_message(f"Atendimentos na Clínica {nome_clinica} não encontrados.")
                            elif entity['entity'] == 'dsConvenio':
                                convenio = entity['value']
                                atendimentos_convenio = [atendimento for atendimento in atendimentos if atendimento.get("dsConvenio") == convenio]
                                if atendimentos_convenio:
                                    numeros_atendimentos = len(atendimentos_convenio)
                                    dispatcher.utter_message(f"Total de atendimentos com o convênio {convenio}: {numeros_atendimentos}")
                                    for atendimento in atendimentos_convenio:
                                        formatted_info = self._formatar_atendimento(atendimento)
                                        dispatcher.utter_message(formatted_info)
                                else:
                                    dispatcher.utter_message(f"Atendimentos com o convênio {convenio} não encontrados.")
                            # Adicione aqui outras condições para outras entidades, se necessário
                    
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
                        dispatcher.utter_message("Por favor, forneça o número do atendimento, o nome do médico, do paciente, da clínica ou o convênio.")
        except requests.exceptions.RequestException as e:
            dispatcher.utter_message("Ocorreu um erro ao obter os dados da API.")
        except Exception as e:
            dispatcher.utter_message("Ocorreu um erro ao processar a solicitação.")

        return [ChatResponse(message=dispatcher.messages, action="action_get_atendimentos", entities={})]

    def _formatar_atendimento(self, atendimento: Dict[str, Any]) -> str:
        formatted_info = "\n".join([
            f"Nº do Atendimento: {atendimento['nrAtendimento']}",            
            f"Paciente: {atendimento['nmPaciente']}",
            f"Médico: {atendimento['nmMedico']}",
            f"Data de Entrada: {atendimento['dtEntrada']}",
            f"Convênio: {atendimento['dsConvenio']}",
            f"Clínica: {atendimento['dsClinica']}",
            " "  # Adicionando uma quebra de linha no final
        ]) + '\n\n'
        return formatted_info

    def _formatar_data(self, data: str) -> str:
        for fmt in ('%d/%m/%Y', '%d-%m-%Y', '%Y/%m/%d', '%Y-%m-%d'):
            try:
                return datetime.datetime.strptime(data, fmt).strftime('%Y-%m-%d')
            except ValueError:
                pass
        raise ValueError('Data fornecida em formato inválido')

    def _comparar_datas(self, data1: str, data2: str) -> bool:
        return data1.startswith(data2)

    def _comparar_datas_intervalo(self, data: str, data_inicial: str, data_final: str) -> bool:
        return data_inicial <= data <= data_final

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
