# Dashboard Qualidade de TOI — EDP SP

Dashboard interativo para análise de qualidade de TOIs (Termos de Ocorrência de Inspeção), com identidade visual EDP SP.

## Funcionalidades

- **Login por senha** — acesso protegido
- **Visão geral** — donut com/sem desvio + ranking de ocorrências
- **Equipes** — comparação Própria vs Terceirizada (% por tipo de desvio)
- **Duplas** — top 10, perfil empilhado e tabela detalhada
- **Individuais** — top 12 matrículas + rankings separados
- **Padrões** — cards "Erro segue a PESSOA" vs "Parceiro influencia"
- **Cidades** — gráfico empilhado + tabela de predominância

## Instalação

```bash
pip install -r requirements.txt
```

## Executar

```bash
streamlit run app.py
```

O dashboard abrirá em `http://localhost:8501`.

## Senha de acesso

Senha padrão: **edp2026**

Para alterar, edite `config.py` ou defina a variável de ambiente:

```bash
set DASHBOARD_PASSWORD=sua_senha
streamlit run app.py
```

## Dados

**Base atual:** `data/qualidade_toi_base_tratada.xlsx` — aba *Ficha de monitoramento* (importada de `Qualidade_TOI_Tratada_RT.xlsx`).

**Base legada (desvios TOI):** `data/base_unificada_dedup_toi.xlsx`.

Para atualizar, substitua o Excel em `data/` e reinicie o Streamlit.

## Identidade visual

- Azul marinho EDP: `#10253F`
- Verde EDP: `#00A84D`
- Fonte: Inter
