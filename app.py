"""MonitorIA Cloud v0.2: aplicativo Streamlit com dados de sessão, sem persistência compartilhada."""
from __future__ import annotations

from datetime import datetime, timezone
import os
from pathlib import Path

import pandas as pd
import streamlit as st

from core import (
    Chunk, MAX_BYTES, SUPPORTED, classify_topic, generated_answer,
    load_chunks, offline_answer, read_material, retrieve,
    safe_filename, split_into_chunks,
)
from storage import build_stats, create_report, export_csv

ROOT = Path(__file__).resolve().parent
MATERIALS = ROOT / "materiais"

st.set_page_config(page_title="MonitorIA | Cálculo II", page_icon="🎓", layout="wide")
st.markdown("""<style>
.block-container {padding-top: 1.8rem; max-width: 1150px;}
h1, h2, h3 {letter-spacing: -.015em;}
</style>""", unsafe_allow_html=True)

# No Streamlit Community Cloud, all these values stay isolated within each browser session.
if "messages" not in st.session_state:
    st.session_state.messages = []
if "uploads" not in st.session_state:
    st.session_state.uploads = {}
if "events" not in st.session_state:
    st.session_state.events = []


def current_chunks() -> tuple[list[Chunk], list[str]]:
    """Index authored demo materials + files uploaded only during this session."""
    chunks, warnings = load_chunks(MATERIALS)
    for name, content in st.session_state.uploads.items():
        try:
            text = read_material(name, content)
            chunks.extend(
                Chunk(name, i, part)
                for i, part in enumerate(split_into_chunks(text), start=1)
            )
        except ValueError as exc:
            warnings.append(f"{name}: {exc}")
    return chunks, warnings


st.title("🎓 MonitorIA — Cálculo II")
st.caption("Projeto pessoal de portfólio • Protótipo de busca documental e IA opcional • Não é um serviço oficial da UFSJ nem do iFood")
st.info("Versão pública de demonstração: perguntas, materiais enviados e indicadores permanecem somente na sua sessão. "
        "Não compartilhe dados pessoais nem documentos sigilosos."
        " Os materiais demonstrativos são exemplos autorais, não apostilas oficiais.")

with st.sidebar:
    st.header("⚙️ Configuração")
    st.write("**Modo padrão:** busca documental sem IA generativa.")
    supplied_key = st.text_input(
        "Sua chave OpenAI (opcional)", type="password", value="",
        help="Somente para testar respostas generativas nesta sessão. Não insira a chave no GitHub. "
             "A API da OpenAI é cobrada separadamente do ChatGPT.",
    )
    api_key = supplied_key.strip()
    model = os.getenv("OPENAI_MODEL", "gpt-4.1-mini").strip()
    if api_key:
        st.success("IA generativa ativada nesta sessão")
        st.warning("Chamadas à API podem gerar custos. Sua chave não é gravada nos indicadores.")
    else:
        st.info("Modo demonstração gratuito (sem geração por IA)")
    st.divider()
    st.caption("Como funciona: pergunta → documentos → busca lexical → resposta/trecho → classificação → indicadores da sessão.")

tab_chat, tab_materials, tab_insights, tab_about = st.tabs(
    ["💬 Assistente", "📁 Materiais", "📊 Indicadores", "🧭 Sobre"]
)

with tab_materials:
    st.subheader("Base de conhecimentos")
    chunks, warnings = current_chunks()
    names = sorted({c.source for c in chunks})
    st.write(f"**{len(names)} documentos** carregados · **{len(chunks)} trechos** indexados")
    if names:
        st.write(" · ".join(names))
    for warning in warnings:
        st.warning(warning)
    incoming = st.file_uploader(
        "Adicione materiais de estudo públicos ou próprios (PDF com texto, TXT ou MD; até 3 MB cada)",
        type=["pdf", "txt", "md"], accept_multiple_files=True,
    )
    if st.button("Adicionar materiais à minha sessão", disabled=not incoming):
        result = []
        for item in (incoming or [])[:10]:
            name = safe_filename(item.name)
            data = item.getvalue()
            if Path(name).suffix.lower() not in SUPPORTED:
                result.append(f"{name}: extensão não suportada")
            elif len(data) > MAX_BYTES:
                result.append(f"{name}: limite de 3 MB")
            else:
                try:
                    read_material(name, data)
                    st.session_state.uploads[name] = data
                    result.append(f"{name}: incluído nesta sessão")
                except ValueError as exc:
                    result.append(f"{name}: {exc}")
        st.session_state["upload_feedback"] = result
        st.rerun()
    for feedback in st.session_state.get("upload_feedback", []):
        st.write(feedback)
    if st.session_state.uploads and st.button("Limpar materiais enviados nesta sessão"):
        st.session_state.uploads = {}
        st.session_state["upload_feedback"] = []
        st.rerun()
    st.caption("Arquivos enviados não são gravados em disco nem compartilhados entre visitantes. "
               "Ao finalizar a sessão ou reiniciar o aplicativo, serão descartados.")

with tab_chat:
    st.subheader("Pergunte sobre os materiais")
    st.caption("Experimente: 'Como funciona a integração por partes?' ou "
               "'Qual é o exemplo de integral dupla no material?'")
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    question = st.chat_input("Digite sua dúvida de Cálculo II...")
    if question:
        st.session_state.messages.append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.markdown(question)
        with st.spinner("Buscando trechos nos materiais..."):
            chunks, _ = current_chunks()
            matches = retrieve(question, chunks)
            mode = "demo_sem_ia"
            if api_key and matches:
                try:
                    reply = generated_answer(question, matches, api_key=api_key, model=model)
                    mode = "ia_generativa"
                except Exception:
                    reply = offline_answer(matches)
                    st.warning("A chamada à API falhou. Confira chave, créditos e conexão. "
                               "A busca documental local continua disponível.")
            else:
                reply = offline_answer(matches)
            topic = classify_topic(question)
            st.session_state.events.append({
                "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "topic": topic,
                "mode": mode,
                "found_sources": len(matches),
            })
            sources = sorted({m.chunk.source for m in matches})
            if sources:
                reply += "\n\n**Materiais consultados:** " + ", ".join(sources)
            reply += f"\n\n*Assunto registrado (sem salvar a pergunta): {topic}*"
        st.session_state.messages.append({"role": "assistant", "content": reply})
        with st.chat_message("assistant"):
            st.markdown(reply)

with tab_insights:
    st.subheader("Indicadores da sessão atual")
    st.caption("Somente as perguntas feitas neste navegador, nesta sessão. "
               "Não são dados da UFSJ nem uso real por estudantes.")
    events = st.session_state.events
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
        st.info("Faça uma pergunta no Assistente para alimentar os indicadores.")
    st.download_button(
        "⬇️ Exportar indicadores desta sessão (CSV / Power BI)",
        data=export_csv(events).encode("utf-8-sig"),
        file_name="monitoria_indicadores.csv", mime="text/csv",
    )
    report = create_report(events).replace(
        "Indicadores anônimos gerados a partir do banco local da aplicação.",
        "Indicadores agregados gerados apenas nesta sessão de demonstração.",
    )
    st.download_button(
        "⬇️ Exportar relatório desta sessão (Markdown)",
        data=report, file_name="relatorio_monitoria.md", mime="text/markdown",
    )
    with st.expander("Exemplo de indicadores fictícios — somente para demonstração"):
        st.caption("Os números abaixo são simulados e não representam estudantes reais.")
        sample = pd.read_csv(ROOT / "dados_exemplo" / "indicadores_sinteticos.csv")
        demo = sample.groupby("assunto", as_index=False)["quantidade"].sum()
        st.bar_chart(demo.set_index("assunto"))

with tab_about:
    st.subheader("O que este MVP demonstra?")
    st.markdown("""
    - **Pesquisa em documentos:** trechos de PDF, TXT e Markdown encontrados via busca TF-IDF lexical.
    - **Respostas com IA generativa (opcional):** somente após o próprio visitante fornecer uma chave da API.
    - **Classificação e métricas:** assuntos organizados e indicadores anônimos apenas da sessão atual.
    - **Análise de dados:** gráficos, exportação CSV para uso futuro em Power BI e relatório em Markdown.

    **Limitações:** sem persistência entre sessões, autenticação ou banco de dados compartilhado;
    a busca não usa embeddings; os indicadores de exemplo são fictícios; a qualidade das
    explicações deve ser revisada. Este é um protótipo de portfólio, não um serviço acadêmico oficial.
    """)
