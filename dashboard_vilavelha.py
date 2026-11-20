import streamlit as st
import pandas as pd
from core.gerenciador_alertas import GerenciadorAlertasComunitarios, BAIRROS_VILA_VELHA

st.set_page_config(page_title="Monitoramento Vila Velha - ThomasInfoTech", layout="wide")

MORADORES_CADASTRADOS = [
    {"id": "Morador 01 (Orla de Itaparica)", "lat": -20.3625, "lon": -40.2890},
    {"id": "Morador 02 (Bacia de Cobilândia)", "lat": -20.3458, "lon": -40.3892},
    {"id": "Morador 03 (Centro de Vila Velha)", "lat": -20.3294, "lon": -40.2944},
    {"id": "Morador 04 (Aribiri / Rio Aribiri)", "lat": -20.3382, "lon": -40.3352},
    {"id": "Morador 05 (Barra do Jucu)", "lat": -20.4152, "lon": -40.3192}
]

OPCOES_BAIRROS = {dados["nome"]: dados for dados in BAIRROS_VILA_VELHA.values()}

sistema = GerenciadorAlertasComunitarios(raio_alerta_km=0.5)

def classificar_status_via(risco):
    if risco >= 5.0:
        return "🔴 INTRANSITÁVEL (Risco de Resgate)"
    elif risco >= 3.5:
        return "🟡 ATENÇÃO (Alagamento Parcial)"
    return "🟢 VIA TRANSITÁVEL (Acúmulo Leve)"

st.title("🌊 Sistema de Alertas Comunitários — Vila Velha (ES)")
st.caption("Engenharia de Software e Geoprocessamento | ThomasInfoTech")

col_form, col_mapa = st.columns([1, 1.5])

with col_form:
    st.subheader("📢 Registrar Novo Alerta")
    bairro_selecionado = st.selectbox("Selecione o Bairro (16 Regiões Mapeadas):", sorted(OPCOES_BAIRROS.keys()))
    dados_b = OPCOES_BAIRROS[bairro_selecionado]
    st.caption(f"Altitude Média: **{dados_b['altitude']}m** | Bacia: **{dados_b['bacia']}**")

    relato = st.text_area("Descreva a situação da rua:", placeholder="Ex: Avenida totalmente alagada e intransitável...")

    if st.button("Disparar Alerta no Perímetro", type="primary"):
        if not relato.strip():
            st.error("Por favor, descreva a situação antes de enviar.")
        else:
            incidente, afetados = sistema.processar_novo_relato(
                relator_id="PAINEL-WEB",
                bairro=bairro_selecionado,
                texto_mensagem=relato,
                lat=dados_b["lat"],
                lon=dados_b["lon"],
                lista_moradores=MORADORES_CADASTRADOS,
                agrupar_proximos=True
            )
            status_via = classificar_status_via(incidente["fator_risco_topografico"])
            st.success(f"Protocolo **{incidente['id']}** | Confirmações: **{incidente.get('confirmacoes', 1)}**")
            st.warning(f"Status: **{status_via}** (Risco: {incidente['fator_risco_topografico']})")
            st.info(f"Vizinhos notificados no raio de 500m: **{len(afetados)}**")

    st.divider()
    st.subheader("📄 Defesa Civil e Gestão")
    if st.button("Exportar Relatório Oficial (CSV)"):
        if sistema.exportar_relatorio_csv():
            st.success("Arquivo 'relatorio_defesa_civil.csv' gerado na pasta do projeto!")
        else:
            st.warning("Não há alertas ativos para exportar.")

    if st.button("Limpar Histórico (Maré Baixa)"):
        sistema.limpar_incidentes_resolvidos()
        st.rerun()

with col_mapa:
    st.subheader("🗺️ Mapa de Incidentes Ativos")
    if sistema.historico_incidentes:
        df_mapa = pd.DataFrame([
            {
                "lat": inc["coordenadas"],
                "lon": inc["coordenadas"],
                "Bairro": inc["bairro"],
                "Risco": inc["fator_risco_topografico"],
                "Confirmações": inc.get("confirmacoes", 1)
            }
            for inc in sistema.historico_incidentes
        ])
        st.map(df_mapa, zoom=11)

        st.subheader("📊 Ranking de Vulnerabilidade e Status")
        ranking = sistema.gerar_estatisticas_bairros()
        df_rank = pd.DataFrame([
            {
                "Bairro": b,
                "Relatos": d["total_alertas"],
                "Risco Máximo": d["risco_maximo"],
                "Situação da Via": classificar_status_via(d["risco_maximo"])
            }
            for b, d in ranking
        ])
        st.dataframe(df_rank, use_container_width=True, hide_index=True)
    else:
        st.info("Nenhum ponto de alagamento ativo no momento. Registre um alerta ao lado para visualizar no mapa.")