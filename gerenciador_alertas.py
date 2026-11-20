import csv
import datetime
import json
import os
import unicodedata
from core.parser_incidentes import ParserIncidentes
from core.geofencing import ResolvedorGeofencing

BAIRROS_VILA_VELHA = {
    "cobilandia": {"nome": "Cobilândia", "altitude": 1.2, "multiplicador": 1.5, "bacia": "Canal de Guaranhuns", "lat": -20.3456, "lon": -40.3890},
    "jardim marilandia": {"nome": "Jardim Marilândia", "altitude": 1.4, "multiplicador": 1.45, "bacia": "Canal de Guaranhuns", "lat": -20.3510, "lon": -40.3820},
    "novo mexico": {"nome": "Novo México", "altitude": 1.5, "multiplicador": 1.4, "bacia": "Canal de Guaranhuns", "lat": -20.3650, "lon": -40.3150},
    "aracas": {"nome": "Araçás", "altitude": 1.8, "multiplicador": 1.35, "bacia": "Canal da Costa", "lat": -20.3680, "lon": -40.3220},
    "paul": {"nome": "Paul", "altitude": 1.6, "multiplicador": 1.4, "bacia": "Baía de Vitória", "lat": -20.3260, "lon": -40.3420},
    "aribiri": {"nome": "Aribiri", "altitude": 1.9, "multiplicador": 1.3, "bacia": "Rio Aribiri", "lat": -20.3380, "lon": -40.3350},
    "ataide": {"nome": "Ataíde", "altitude": 2.1, "multiplicador": 1.25, "bacia": "Rio Aribiri", "lat": -20.3340, "lon": -40.3450},
    "centro": {"nome": "Centro", "altitude": 2.0, "multiplicador": 1.3, "bacia": "Canal da Costa", "lat": -20.3290, "lon": -40.2940},
    "divino espirito santo": {"nome": "Divino Espírito Santo", "altitude": 2.2, "multiplicador": 1.25, "bacia": "Canal da Costa", "lat": -20.3360, "lon": -40.2960},
    "praia da costa": {"nome": "Praia da Costa", "altitude": 2.8, "multiplicador": 1.15, "bacia": "Orla Atlântica", "lat": -20.3410, "lon": -40.2860},
    "itapoa": {"nome": "Itapoã", "altitude": 2.6, "multiplicador": 1.2, "bacia": "Canal da Costa", "lat": -20.3510, "lon": -40.2890},
    "praia de itaparica": {"nome": "Praia de Itaparica", "altitude": 2.5, "multiplicador": 1.2, "bacia": "Canal da Costa", "lat": -20.3621, "lon": -40.2894},
    "coqueiral de itaparica": {"nome": "Coqueiral de Itaparica", "altitude": 2.3, "multiplicador": 1.25, "bacia": "Canal da Costa", "lat": -20.3660, "lon": -40.2980},
    "ibes": {"nome": "Ibes", "altitude": 2.7, "multiplicador": 1.15, "bacia": "Canal de Guaranhuns", "lat": -20.3480, "lon": -40.3180},
    "gloria": {"nome": "Glória", "altitude": 3.5, "multiplicador": 1.0, "bacia": "Rio Aribiri", "lat": -20.3350, "lon": -40.3120},
    "barra do jucu": {"nome": "Barra do Jucu", "altitude": 1.7, "multiplicador": 1.35, "bacia": "Foz do Rio Jucu", "lat": -20.4150, "lon": -40.3190}
}

def normalizar_texto(texto):
    nfkd = unicodedata.normalize('NFKD', texto)
    sem_acento = "".join([c for c in nfkd if not unicodedata.combining(c)])
    return sem_acento.lower().strip()

class GerenciadorAlertasComunitarios:
    def __init__(self, raio_alerta_km=0.5, arquivo_banco="alertas_vilavelha.json"):
        self.parser = ParserIncidentes()
        self.geofence = ResolvedorGeofencing(raio_alerta_padrao_km=raio_alerta_km)
        self.arquivo_banco = arquivo_banco
        self.historico_incidentes = self._carregar_dados()

    def _carregar_dados(self):
        if os.path.exists(self.arquivo_banco):
            with open(self.arquivo_banco, "r", encoding="utf-8") as f:
                return json.load(f)
        return []

    def _salvar_dados(self):
        with open(self.arquivo_banco, "w", encoding="utf-8") as f:
            json.dump(self.historico_incidentes, f, indent=4, ensure_ascii=False)

    def calcular_risco_topografico(self, bairro, severidade):
        bairro_chave = normalizar_texto(bairro)
        dados_bairro = BAIRROS_VILA_VELHA.get(bairro_chave, {"altitude": 3.0, "multiplicador": 1.0})
        componente_altitude = 5.0 - dados_bairro["altitude"]
        risco = ((severidade * 0.4) + (componente_altitude * 0.6)) * dados_bairro["multiplicador"]
        return round(risco, 2)

    def _buscar_incidente_proximo(self, lat, lon, raio_agrupamento_km=0.2):
        for inc in self.historico_incidentes:
            lat_existente, lon_existente = inc["coordenadas"]
            distancia = self.geofence.calcular_distancia_haversine(lat, lon, lat_existente, lon_existente)
            if distancia <= raio_agrupamento_km:
                return inc
        return None

    def processar_novo_relato(self, relator_id, bairro, texto_mensagem, lat, lon, lista_moradores, agrupar_proximos=False):
        severidade = self.parser.extrair_severidade(texto_mensagem)
        fator_risco = self.calcular_risco_topografico(bairro, severidade)

        if agrupar_proximos:
            incidente_existente = self._buscar_incidente_proximo(lat, lon)
            if incidente_existente:
                incidente_existente["confirmacoes"] = incidente_existente.get("confirmacoes", 1) + 1
                if severidade > incidente_existente["severidade_relatada"]:
                    incidente_existente["severidade_relatada"] = severidade
                    incidente_existente["fator_risco_topografico"] = fator_risco
                    incidente_existente["texto"] = texto_mensagem
                self._salvar_dados()
                moradores_afetados = self.geofence.verificar_moradores_no_perimetro((lat, lon), lista_moradores)
                return incidente_existente, moradores_afetados

        id_incidente = f"INC-{datetime.datetime.now().strftime('%Y%m%d')}-{len(self.historico_incidentes) + 1:03d}"
        incidente = {
            "id": id_incidente,
            "timestamp": datetime.datetime.now().isoformat(),
            "relator": relator_id,
            "bairro": bairro.title(),
            "texto": texto_mensagem,
            "coordenadas": [lat, lon],
            "severidade_relatada": severidade,
            "fator_risco_topografico": fator_risco,
            "confirmacoes": 1
        }

        self.historico_incidentes.append(incidente)
        self._salvar_dados()

        moradores_afetados = self.geofence.verificar_moradores_no_perimetro((lat, lon), lista_moradores)
        return incidente, moradores_afetados

    def consultar_por_bairro(self, bairro_busca):
        chave_busca = normalizar_texto(bairro_busca)
        resultados = [
            inc for inc in self.historico_incidentes 
            if normalizar_texto(inc["bairro"]) == chave_busca
        ]
        return sorted(resultados, key=lambda x: x["fator_risco_topografico"], reverse=True)

    def gerar_estatisticas_bairros(self):
        estatisticas = {}
        for inc in self.historico_incidentes:
            bairro = inc["bairro"]
            risco = inc["fator_risco_topografico"]
            confirmacoes = inc.get("confirmacoes", 1)

            if bairro not in estatisticas:
                estatisticas[bairro] = {"total_alertas": 0, "risco_maximo": 0.0}

            estatisticas[bairro]["total_alertas"] += confirmacoes
            if risco > estatisticas[bairro]["risco_maximo"]:
                estatisticas[bairro]["risco_maximo"] = risco

        ranking = sorted(
            estatisticas.items(), 
            key=lambda item: (item[1]["risco_maximo"], item[1]["total_alertas"]), 
            reverse=True
        )
        return ranking

    def limpar_incidentes_resolvidos(self, id_protocolo=None):
        if id_protocolo:
            tamanho_antes = len(self.historico_incidentes)
            self.historico_incidentes = [
                inc for inc in self.historico_incidentes 
                if inc["id"].upper() != id_protocolo.upper().strip()
            ]
            removido = len(self.historico_incidentes) < tamanho_antes
        else:
            removido = len(self.historico_incidentes) > 0
            self.historico_incidentes = []

        if removido:
            self._salvar_dados()
        return removido

    def exportar_relatorio_csv(self, caminho_csv="relatorio_defesa_civil.csv"):
        if not self.historico_incidentes:
            return False
        with open(caminho_csv, mode="w", newline="", encoding="utf-8-sig") as arquivo:
            escritor = csv.writer(arquivo, delimiter=";")
            escritor.writerow(["Protocolo", "Data/Hora", "Bairro", "Confirmacoes", "Severidade (1-5)", "Risco Topografico", "Latitude", "Longitude", "Relato"])
            for inc in self.historico_incidentes:
                lat, lon = inc["coordenadas"]
                risco_br = str(inc["fator_risco_topografico"]).replace(".", ",")
                lat_br = str(lat).replace(".", ",")
                lon_br = str(lon).replace(".", ",")

                escritor.writerow([
                    inc["id"],
                    inc["timestamp"],
                    inc["bairro"],
                    inc.get("confirmacoes", 1),
                    inc["severidade_relatada"],
                    risco_br,
                    lat_br,
                    lon_br,
                    inc["texto"]
                ])
        return True