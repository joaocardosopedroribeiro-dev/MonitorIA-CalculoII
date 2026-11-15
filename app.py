"""Interface MVP do projeto autoral MonitorIA — execute com `streamlit run app.py`."""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
import pandas as pd
import streamlit as st

from core import (
    MAX_BYTES, SUPPORTED, classify_topic, generated_answer, load_chunks,
    offline_answer, read_material, retrieve, safe_filename,
)
from storage import build_stats, create_report, export_csv, load_events, log_event

ROOT = Path(__file__).resolve().parent
MATERIALS = ROOT / "materiais"
DB = ROOT / "data" / "events.sqlite3"
load_dotenv(ROOT / ".env")
MATERIALS.mkdir(exist_ok=True)

st.set_page_config(page_title="MonitorIA | Cálculo II", page_icon="🎓", layout="wide")
st.markdown("""<style>
.block-container {padding-top: 1.8rem; max-width: 1150px;}
h1, h2, h3 {letter-spacing: -.015em;}
[data-testid="stMetricValue"] {font-weight: 650;}
</style>""", unsafe_allow_html=True)

st.title("🎓 MonitorIA — Cálculo II")
st.caption("Projeto autoral • MVP de assistente acadêmico com IA e indicadores • Não afiliado ao iFood")
st.info("Use apenas conteúdos didáticos públicos ou autorizados e perguntas sem dados pessoais. "
        "Quando a IA generativa está ativada, trechos relevantes são enviados ao provedor da API.")

with st.sidebar:
    st.header("⚙️ Configuração")
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    model = os.getenv("OPENAI_MODEL", "gpt-4.1-mini").strip()
    st.success("IA generativa disponível") if api_key else st.warning("Modo demonstração: sem chave de API")
    st.caption("Para ativar a IA, crie um `.env` local a partir de `.env.example`. "
               "Não coloque sua chave no GitHub.")
    st.caption(f"Modelo configurado: `{model}`")
    st.divider()
    st.markdown("**Fluxo construído**")
    st.write("1. Receber dúvida")
    st.write("2. Buscar nos documentos")
    st.write("3. Responder com fonte")
    st.write("4. Classificar e registrar indicador")
    st.write("5. Gerar relatório")

tab_chat, tab_materials, tab_insights, tab_about = st.tabs(
    ["💬 Assistente", "📁 Materiais", "📊 Indicadores", "🧭 Sobre"]
)

with tab_materials:
    st.subheader("Base de conhecimentos")
    chunks, warnings = load_chunks(MATERIALS)
    names = sorted({c.source for c in chunks})
    st.write(f"**{len(names)} documentos** carregados · **{len(chunks)} trechos** indexados")
    if names:
        st.write(" · ".join(names))
    for warning in warnings:
        st.warning(warning)
    uploaded = st.file_uploader(
        "Adicione materiais próprios (PDF com texto, TXT ou MD; até 3 MB)",
        type=["pdf", "txt", "md"], accept_multiple_files=True,
    )
    if st.button("Adicionar materiais", disabled=not uploaded):
        messages = []
        for item in uploaded or []:
            data = item.getvalue()
            filename = safe_filename(item.name)
            if Path(filename).suffix.lower() not in SUPPORTED:
                messages.append(f"{item.name}: extensão inválida")
                continue
            if len(data) > MAX_BYTES:
                messages.append(f"{item.name}: excede 3 MB")
                continue
            try:
                read_material(filename, data)  # valida extração antes de salvar
                (MATERIALS / filename).write_bytes(data)
                messages.append(f"Adicionado: {filename}")
            except ValueError as exc:
                messages.append(f"{item.name}: {exc}")
        for msg in messages:
            st.write(msg)
        st.rerun()
    st.caption("Os arquivos ficam apenas no computador que executa o app. "
               "Não publique dados privados no repositório.")

with tab_chat:
    st.subheader("Pergunte sobre os materiais")
    st.caption("Experimente: 'Como funciona a integração por partes?' ou "
               "'Qual é o exemplo de integral dupla no material?'")
    if "messages" not in st.session_state:
        st.session_state.messages = []
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
    question = st.chat_input("Digite sua dúvida de Cálculo II...")
    if question:
        with st.chat_message("user"):
            st.markdown(question)
        st.session_state.messages.append({"role": "user", "content": question})
        with st.spinner("Buscando material e elaborando resposta..."):
            chunks, _ = load_chunks(MATERIALS)
            matches = retrieve(question, chunks)
            mode = "demo_sem_ia"
            if api_key and matches:
                try:
                    reply = generated_answer(question, matches, api_key=api_key, model=model)
                    mode = "ia_generativa"
                except Exception as exc:
                    reply = offline_answer(matches)
                    st.warning("A chamada da API falhou. Exibindo resultado local. "
                               "Verifique sua chave, créditos e conexão.")
            else:
                reply = offline_answer(matches)
            topic = classify_topic(question)
            log_event(DB, topic, mode, len(matches))
            sources = sorted({m.chunk.source for m in matches})
            if sources:
                reply += "\n\n**Materiais consultados:** " + ", ".join(sources)
            reply += f"\n\n*Assunto registrado (sem salvar a pergunta): {topic}*"
        with st.chat_message("assistant"):
            st.markdown(reply)
        st.session_state.messages.append({"role": "assistant", "content": reply})

with tab_insights:
    st.subheader("Indicadores de uso — dados reais desta instalação")
    events = load_events(DB)
    stats = build_stats(events)
    a, b, c = st.columns(3)
    a.metric("Interações registradas", stats["total"])
    b.metric("Com fonte relevante", stats["with_sources"])
    c.metric("Cobertura documental", f"{stats['coverage_percent']}%")
    if stats["topic_counts"]:
        df = pd.DataFrame([{"Assunto": topic, "Dúvidas": count}
                           for topic, count in stats["topic_counts"].items()])
        st.bar_chart(df.set_index("Assunto"))
    else:
        st.info("Ainda não há perguntas. Converse com o assistente para alimentar os indicadores.")
    st.download_button(
        "⬇️ Baixar dados anônimos para Power BI (CSV)",
        data=export_csv(events).encode("utf-8-sig"),
        file_name="monitoria_indicadores.csv", mime="text/csv",
    )
    st.download_button(
        "⬇️ Baixar relatório automático (Markdown)",
        data=create_report(events), file_name="relatorio_monitoria.md", mime="text/markdown",
    )
    with st.expander("Exemplo de indicadores fictícios — apenas para demonstração"):
        st.caption("Os números abaixo são SIMULADOS; não representam estudantes reais.")
        sample = pd.read_csv(ROOT / "dados_exemplo" / "indicadores_sinteticos.csv")
        demo = sample.groupby("assunto", as_index=False)["quantidade"].sum()
        st.bar_chart(demo.set_index("assunto"))

with tab_about:
    st.subheader("O que este MVP demonstra?")
    st.markdown("""
    - **Busca em documentos (RAG lexical):** encontra trechos relevantes em PDF, TXT e MD.
    - **IA generativa opcional:** explica conteúdos com fontes quando há chave de API.
    - **Automação de dados:** classifica dúvidas e registra somente métricas anônimas.
    - **Análise de dados:** gera gráfico, CSV compatível com Power BI e relatório Markdown.

    **Limitações atuais:** a busca é lexical, não por embeddings; pode perder sinônimos.
    Não há autenticação nem persistência multiusuário. O conteúdo de documentos pode
    conter erros e a resposta de IA deve ser revisada. Para implantação real, seriam
    necessários controle de acesso, consentimento, política de retenção e testes.
    """)
