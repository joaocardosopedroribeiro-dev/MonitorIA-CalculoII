# MonitorIA — Cálculo II (versão Cloud 0.2)

Protótipo pessoal para portfólio na trilha **AI Builder**, criado para demonstrar aplicação prática de IA e análise de dados em monitoria acadêmica. Não é um produto do iFood nem da UFSJ.

## O que já funciona

- Consulta aos quatro documentos **autorais de demonstração** incluídos em `materiais/`.
- Busca TF-IDF lexical por trechos em PDFs (com texto), TXT e Markdown.
- Chat em modo gratuito de consulta documental, **sem IA generativa**.
- **Opcional:** ao inserir sua própria chave OpenAI no campo lateral do app, gera explicações via API usando os documentos encontrados (a API pode cobrar por uso). Não coloque a chave no GitHub.
- Envio de materiais para a sessão atual, sem gravá-los em disco.
- Classificação de dúvidas, gráficos, exportação de CSV para Power BI e geração de relatório Markdown, sempre **somente para a sessão atual**.
- Indicadores sintéticos separados e claramente identificados como fictícios.

## Publicar sem instalar Python no Windows

1. Crie uma conta em https://github.com e abra https://github.com/new.
2. Crie um repositório **Public**, chamado `MonitorIA-CalculoII`; não adicione README ou licença automáticos.
3. Extraia `MonitorIA_Cloud_v0.2.zip` no Windows. Abra a pasta extraída, **selecione os arquivos e as duas pastas internas** (`materiais`, `dados_exemplo`, `tests`) e arraste para a página de upload do repositório: **Add file → Upload files**. Não envie apenas o ZIP.
4. Confirme que `app.py`, `core.py`, `requirements.txt`, `storage.py` e `README.md` aparecem **na raiz** do repositório. Confirme também as pastas `materiais/` e `dados_exemplo/`.
5. Clique em **Commit changes** no GitHub.
6. Abra https://share.streamlit.io, entre com seu GitHub e autorize o acesso aos repositórios públicos.
7. Clique **Create app** → **Yup, I have an app**. Selecione o repositório `MonitorIA-CalculoII`, branch `main` e **Main file path** `app.py`. Se solicitado, aceite a versão padrão de Python 3.12.
8. Clique **Deploy**. O Streamlit instala as dependências do `requirements.txt` automaticamente na nuvem. Ao terminar, você terá um endereço `https://...streamlit.app`.
9. Abra o app, clique em **Assistente** e pergunte `Como funciona a integração por partes?`. Depois abra **Indicadores**.

## Segurança e limites da versão em nuvem

- Não publique nem envie dados pessoais, documentos sigilosos, avaliações restritas ou dados reais dos estudantes.
- **Nunca** envie chaves de API, `.env` ou `secrets.toml` para o repositório.
- Para evitar cobranças involuntárias quando o link é público, a aplicação **não possui uma chave global**. IA generativa só é acionada se o próprio visitante inserir uma chave na sessão.
- A versão publicada não grava arquivos nem indicadores em disco. Os dados são temporários e isolados por sessão; não representam um dashboard institucional ou uma automação de agendamento.
- O arquivo `requirements.txt` tem todas as bibliotecas necessárias; não é preciso executar `pip install` no Windows.
- Integração Power BI é **exportação CSV**, não um conector Power BI ativo. Integração n8n é uma ideia futura.

## Arquivos

- `app.py` interface web (Streamlit), dados de sessão, visualização.
- `core.py` leitura de documentos, busca local, classificação e integração opcional à API.
- `storage.py` cálculo e exportação de indicadores.
- `materiais/` conteúdo didático demonstrativo e original.
- `dados_exemplo/` métricas sintéticas para demonstração.
- `tests/` testes unitários do núcleo.
- `requirements.txt` dependências Python gerenciadas automaticamente pelo Community Cloud.

## Teste local (opcional)

```bash
python -m unittest discover -s tests -v
```

## Apresentação no portfólio

**MonitorIA — protótipo pessoal de assistente para Cálculo II:** aplicação web em Python e Streamlit com pesquisa lexical em documentos, resposta generativa opcional com API própria, classificação de dúvidas, painel de indicadores e exportação CSV. Aplicativo demonstrativo sem uso oficial em produção.
