"""
Dashboard Qualidade de TOI — EDP SP
Acesso protegido por senha.
"""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import html
from pathlib import Path
from urllib.parse import quote

from config import (
    CHART_PALETTE,
    CHART_TEAM_COLORS,
    COLORS,
    DEVIATION_COLORS,
    DEVIATION_PILL_COLORS,
    DASHBOARD_PASSWORD,
    ACCESS_PROFILES,
    IRREGULARIDADE_COLORS,
    LOGO_DIR,
    LOGO_FILENAMES,
    MONITORAMENTO_FILE,
    MONITORAMENTO_SCHEMA_VERSION,
)
from monitoramento_processor import (
    colaboradores_resumo,
    colaborador_analise,
    csd_breakdown,
    csds_resumo,
    delete_monitoramento_rows,
    detect_inconsistencias,
    ensure_monitoramento_schema,
    export_base_view,
    filter_colaboradores,
    filter_csds,
    filter_ficha,
    count_desvios_laboratorio,
    count_total_desvios_encontrados,
    pct_tois_com_desvio,
    desvios_por_tipo_equipe,
    desvios_ranking,
    expand_desvios_ocorrencias,
    filter_desvios_laboratorio,
    filter_medidor_resultado,
    filter_por_csd,
    filter_por_desvio_tipo,
    filter_por_matricula,
    filter_por_tipo_equipe,
    timeline_desvios_monthly,
    timeline_desvios_por_equipe,
    timeline_desvios_por_pessoa,
    inconsistencia_record_view,
    inconsistencia_row_label,
    inspetor_issues_ranking,
    irregularidade_ranking,
    kpi_metrics as kpi_monitoramento,
    laudo_summary,
    load_monitoramento,
    medidor_summary,
    periodo_agendamento,
)

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Qualidade do TOI | Laboratório de Medição",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── CSS EDP SP ─────────────────────────────────────────────────────────────────
st.markdown(
    f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Source+Sans+3:wght@400;500;600;700&display=swap');

:root {{
    --edp-navy: {COLORS['navy']};
    --edp-green: {COLORS['green']};
    --edp-text: {COLORS['navy']};
    --edp-text-secondary: {COLORS['grey_text']};
    --edp-bg: {COLORS['bg']};
    --edp-white: {COLORS['white']};
    --primary-color: {COLORS['green']};
}}
.stApp {{
    --primary-color: {COLORS['green']} !important;
}}

/* Base — força tema claro com texto escuro */
html, body, .stApp {{
    font-family: 'Source Sans 3', sans-serif !important;
    background-color: {COLORS['bg']} !important;
    color: {COLORS['text']} !important;
}}

.block-container {{
    padding-top: 1.5rem;
    max-width: 1400px;
}}

/* Componentes nativos Streamlit */
.stTextInput label,
.stTextInput label p,
.stButton p,
[data-testid="stMarkdownContainer"],
[data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] span,
[data-testid="stMarkdownContainer"] div,
[data-testid="stMarkdownContainer"] li {{
    color: {COLORS['navy']} !important;
}}

/* Campo de senha — fundo branco, texto azul escuro */
.stTextInput div[data-baseweb="base-input"] {{
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
}}
.stTextInput div[data-baseweb="base-input"] > div[data-baseweb="input"] {{
    background-color: {COLORS['white']} !important;
    border: 1px solid {COLORS['grey']} !important;
    border-radius: 8px !important;
    box-shadow: none !important;
}}
.stTextInput input {{
    background-color: transparent !important;
    color: {COLORS['navy']} !important;
    -webkit-text-fill-color: {COLORS['navy']} !important;
    border: none !important;
    box-shadow: none !important;
    caret-color: {COLORS['navy']} !important;
}}
.stTextInput div[data-baseweb="base-input"] > div[data-baseweb="input"]:focus-within,
.stTextInput div[data-baseweb="input"]:focus-within,
div[data-testid="stTextInput"] div[data-baseweb="input"]:focus-within,
div[data-testid="stTextInput"] div[data-baseweb="input"]:focus,
div[data-baseweb="input"]:focus-within {{
    border: 1px solid {COLORS['green']} !important;
    box-shadow: none !important;
    outline: none !important;
}}
.stTextInput input:focus,
.stTextInput input:focus-visible,
div[data-testid="stTextInput"] input:focus,
div[data-testid="stTextInput"] input:focus-visible {{
    outline: none !important;
    box-shadow: none !important;
    border: none !important;
}}
.stTextInput input::placeholder {{
    color: {COLORS['grey_text']} !important;
    -webkit-text-fill-color: {COLORS['grey_text']} !important;
}}
/* Botão mostrar/ocultar senha — sem caixa extra */
.stTextInput div[data-baseweb="base-input"] button {{
    background: transparent !important;
    background-color: transparent !important;
    border: none !important;
    box-shadow: none !important;
    outline: none !important;
    color: {COLORS['navy']} !important;
    min-width: unset !important;
    padding: 0 10px !important;
}}
.stTextInput div[data-baseweb="base-input"] button:hover {{
    background: transparent !important;
    color: {COLORS['green']} !important;
    border: none !important;
    box-shadow: none !important;
}}
.stTextInput [data-baseweb="input-suffix"],
.stTextInput [data-baseweb="input-end-enhancer"] {{
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
}}

/* Botões — verde EDP */
div[data-testid="stButton"] > button,
div[data-testid="stButton"] button,
button[data-testid="stBaseButton-primary"],
button[data-testid="stBaseButton-secondary"],
button[kind="primary"],
button[kind="secondary"],
.stButton > button,
.stButton button {{
    background: {COLORS['green']} !important;
    background-color: {COLORS['green']} !important;
    color: {COLORS['white']} !important;
    border: none !important;
    border-color: {COLORS['green']} !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    box-shadow: none !important;
}}
div[data-testid="stButton"] > button:hover,
button[data-testid="stBaseButton-primary"]:hover,
button[data-testid="stBaseButton-secondary"]:hover,
.stButton button:hover {{
    background: {COLORS['green_dark']} !important;
    background-color: {COLORS['green_dark']} !important;
    color: {COLORS['white']} !important;
    border-color: {COLORS['green_dark']} !important;
}}
div[data-testid="stButton"] > button p,
div[data-testid="stButton"] > button span,
.stButton button p,
.stButton button span {{
    color: {COLORS['white']} !important;
}}
/* Menu de navegação — não herdar verde dos botões globais */
.st-key-nav_menu_bar div[data-testid="stButton"] > button,
.st-key-nav_menu_bar div[data-testid="stButton"] > button[kind="secondary"],
.st-key-nav_menu_bar div[data-testid="stButton"] > button[data-testid="stBaseButton-secondary"],
.st-key-nav_tabs_track div[data-testid="stButton"] > button,
.st-key-nav_tabs_track div[data-testid="stButton"] > button[kind="secondary"],
.st-key-nav_tabs_track div[data-testid="stButton"] > button[data-testid="stBaseButton-secondary"] {{
    background: transparent !important;
    background-color: transparent !important;
    color: {COLORS['grey_text']} !important;
    border: none !important;
    font-weight: 500 !important;
    box-shadow: none !important;
}}
.st-key-nav_menu_bar div[data-testid="stButton"] > button p,
.st-key-nav_menu_bar div[data-testid="stButton"] > button span,
.st-key-nav_tabs_track div[data-testid="stButton"] > button p,
.st-key-nav_tabs_track div[data-testid="stButton"] > button span {{
    color: inherit !important;
}}

/* Menu principal — navegação com aba ativa em cinza */
.st-key-nav_menu_bar {{
    background: {COLORS['white']};
    border: 1px solid {COLORS['border']};
    border-radius: 12px;
    padding: 10px 14px;
    margin-bottom: 1.25rem;
    box-shadow: 0 1px 3px rgba(13, 40, 64, 0.06);
}}
.st-key-nav_menu_bar [data-testid="stHorizontalBlock"] {{
    align-items: center !important;
    gap: 12px !important;
}}
.st-key-nav_menu_bar .nav-page-flag {{
    display: none !important;
}}
.nav-profile-badge {{
    display: flex;
    align-items: center;
    justify-content: center;
    height: 40px;
    padding: 0 10px;
    background: {COLORS['grey']};
    color: {COLORS['navy']} !important;
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
    font-size: 0.78rem;
    font-weight: 600;
    letter-spacing: 0.02em;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}}
.st-key-nav_tabs_track {{
    background: {COLORS['grey']};
    border-radius: 10px;
    padding: 4px;
    width: 100%;
}}
.st-key-nav_tabs_track [data-testid="stHorizontalBlock"] {{
    align-items: stretch !important;
    gap: 4px !important;
}}
.st-key-nav_tabs_track [data-testid="column"] {{
    padding: 0 !important;
}}
.st-key-nav_tabs_track [data-testid="column"] div[data-testid="stButton"] {{
    margin: 0 !important;
}}
/* Abas inativas — sem verde global */
.st-key-nav_menu_bar .st-key-nav_tabs_track div[data-testid="stButton"] > button,
.st-key-nav_menu_bar .st-key-nav_tabs_track div[data-testid="stButton"] > button[kind="secondary"],
.st-key-nav_menu_bar .st-key-nav_tabs_track div[data-testid="stButton"] > button[data-testid="stBaseButton-secondary"],
.st-key-nav_tabs_track [data-testid="column"] div[data-testid="stButton"] > button,
.st-key-nav_tabs_track [data-testid="column"] div[data-testid="stButton"] > button[kind="secondary"],
.st-key-nav_tabs_track [data-testid="column"] div[data-testid="stButton"] > button[data-testid="stBaseButton-secondary"] {{
    background: transparent !important;
    background-color: transparent !important;
    color: {COLORS['grey_text']} !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 500 !important;
    font-size: 0.875rem !important;
    min-height: 40px !important;
    padding: 0 0.85rem !important;
    box-shadow: none !important;
    white-space: nowrap !important;
    width: 100% !important;
    transition: background 0.15s ease, color 0.15s ease;
}}
.st-key-nav_tabs_track [data-testid="column"] div[data-testid="stButton"] > button:hover {{
    background: rgba(255, 255, 255, 0.55) !important;
    color: {COLORS['navy']} !important;
}}
.st-key-nav_tabs_track [data-testid="column"] div[data-testid="stButton"] > button p,
.st-key-nav_tabs_track [data-testid="column"] div[data-testid="stButton"] > button span {{
    color: inherit !important;
    -webkit-text-fill-color: inherit !important;
    white-space: nowrap !important;
}}
/* Aba ativa — cinza */
.st-key-nav_menu_bar:has(.nav-page-painel) .st-key-go_dash div[data-testid="stButton"] > button,
.st-key-nav_menu_bar:has(.nav-page-painel) .st-key-go_dash div[data-testid="stButton"] > button[kind="secondary"],
.st-key-nav_menu_bar:has(.nav-page-painel) .st-key-go_dash div[data-testid="stButton"] > button[data-testid="stBaseButton-secondary"],
.st-key-nav_menu_bar:has(.nav-page-dados) .st-key-go_dados div[data-testid="stButton"] > button,
.st-key-nav_menu_bar:has(.nav-page-dados) .st-key-go_dados div[data-testid="stButton"] > button[kind="secondary"],
.st-key-nav_menu_bar:has(.nav-page-dados) .st-key-go_dados div[data-testid="stButton"] > button[data-testid="stBaseButton-secondary"],
.st-key-nav_menu_bar:has(.nav-page-cadastro) .st-key-go_cadastro div[data-testid="stButton"] > button,
.st-key-nav_menu_bar:has(.nav-page-cadastro) .st-key-go_cadastro div[data-testid="stButton"] > button[kind="secondary"],
.st-key-nav_menu_bar:has(.nav-page-cadastro) .st-key-go_cadastro div[data-testid="stButton"] > button[data-testid="stBaseButton-secondary"],
.st-key-nav_menu_bar:has(.nav-page-inconsistencias) .st-key-go_inconsistencias div[data-testid="stButton"] > button,
.st-key-nav_menu_bar:has(.nav-page-inconsistencias) .st-key-go_inconsistencias div[data-testid="stButton"] > button[kind="secondary"],
.st-key-nav_menu_bar:has(.nav-page-inconsistencias) .st-key-go_inconsistencias div[data-testid="stButton"] > button[data-testid="stBaseButton-secondary"] {{
    background: #C5CBD4 !important;
    background-color: #C5CBD4 !important;
    color: {COLORS['navy']} !important;
    font-weight: 600 !important;
    box-shadow: none !important;
    border: none !important;
}}
.st-key-nav_menu_bar:has(.nav-page-painel) .st-key-go_dash div[data-testid="stButton"] > button:hover,
.st-key-nav_menu_bar:has(.nav-page-dados) .st-key-go_dados div[data-testid="stButton"] > button:hover,
.st-key-nav_menu_bar:has(.nav-page-cadastro) .st-key-go_cadastro div[data-testid="stButton"] > button:hover,
.st-key-nav_menu_bar:has(.nav-page-inconsistencias) .st-key-go_inconsistencias div[data-testid="stButton"] > button:hover {{
    background: #B8BEC8 !important;
    background-color: #B8BEC8 !important;
    color: {COLORS['navy']} !important;
}}
/* Sair — contorno, nunca verde */
.st-key-nav_menu_bar .st-key-logout div[data-testid="stButton"] > button,
.st-key-nav_menu_bar .st-key-logout div[data-testid="stButton"] > button[kind="secondary"],
.st-key-nav_menu_bar .st-key-logout div[data-testid="stButton"] > button[data-testid="stBaseButton-secondary"] {{
    background: transparent !important;
    background-color: transparent !important;
    color: {COLORS['grey_text']} !important;
    border: 1px solid {COLORS['border']} !important;
    border-radius: 8px !important;
    font-weight: 500 !important;
    font-size: 0.82rem !important;
    min-height: 38px !important;
    box-shadow: none !important;
}}
.st-key-nav_menu_bar .st-key-logout div[data-testid="stButton"] > button:hover {{
    background: {COLORS['grey']} !important;
    color: {COLORS['navy']} !important;
    border-color: {COLORS['grey_text']} !important;
}}
.st-key-nav_menu_bar .st-key-logout div[data-testid="stButton"] > button p,
.st-key-nav_menu_bar .st-key-logout div[data-testid="stButton"] > button span {{
    color: inherit !important;
    -webkit-text-fill-color: inherit !important;
}}

/* Campo senha no login — fundo branco */
div[data-testid="stTextInput"] input,
div[data-testid="stTextInput"] div[data-baseweb="input"],
div[data-testid="stTextInput"] div[data-baseweb="base-input"] {{
    background-color: {COLORS['white']} !important;
    color: {COLORS['navy']} !important;
}}
.login-error {{
    background: {COLORS['grey']};
    color: {COLORS['navy']};
    border-left: 4px solid {COLORS['green']};
    padding: 10px 14px;
    border-radius: 8px;
    font-size: 0.85rem;
    margin: 8px 0 4px;
    text-align: left;
}}

/* Login */
.login-wrap {{
    max-width: 420px;
    margin: 80px auto;
    background: {COLORS['white']};
    border-radius: 16px;
    padding: 48px 40px;
    box-shadow: 0 4px 24px rgba(16,37,63,0.10);
    text-align: center;
    color: {COLORS['navy']} !important;
}}
.login-panel-anchor {{
    display: none;
}}
[data-testid="column"]:has(.login-panel-anchor) {{
    background: {COLORS['white']};
    border: 1px solid {COLORS['border']};
    border-radius: 6px;
    padding: 40px 32px 32px;
    box-shadow: none;
    text-align: center;
    margin-top: 60px;
    margin-bottom: 8px;
}}
[data-testid="column"]:has(.login-panel-anchor) [data-testid="stImage"] {{
    display: flex;
    justify-content: center;
    margin-bottom: 16px;
}}
[data-testid="column"]:has(.login-panel-anchor) [data-testid="stImage"] img,
[data-testid="column"]:has(.login-panel-anchor) .logo-svg img {{
    max-height: 72px;
    width: auto !important;
    max-width: 100%;
    object-fit: contain;
    display: block;
    margin: 0 auto;
}}
[data-testid="column"]:has(.login-panel-anchor) .logo-svg {{
    display: flex;
    justify-content: center;
    margin-bottom: 16px;
}}
.login-logo {{
    font-size: 2.4rem;
    font-weight: 700;
    color: {COLORS['navy']} !important;
    margin-bottom: 4px;
}}
.login-logo span {{ color: {COLORS['green']} !important; }}
.login-sub {{
    color: {COLORS['grey_text']} !important;
    font-size: 0.88rem;
    font-weight: 600;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    margin-top: 8px;
    margin-bottom: 32px;
    text-align: center !important;
    width: 100%;
    display: block;
    margin-left: auto;
    margin-right: auto;
}}
[data-testid="column"]:has(.login-panel-anchor) .login-sub,
[data-testid="column"]:has(.login-panel-anchor) [data-testid="stMarkdownContainer"]:has(.login-sub) {{
    text-align: center !important;
    display: flex !important;
    justify-content: center !important;
    width: 100% !important;
}}
.brand-logo img {{
    display: block;
    margin: 0 auto 16px;
    object-fit: contain;
    max-width: 220px;
    width: auto;
    height: 72px;
}}

/* Header — estilo Laudo de Perícia */
.laudo-header {{
    position: relative;
    background: {COLORS['white']};
    border: 1px solid {COLORS['border']};
    border-radius: 6px;
    padding: 22px 28px;
    margin-bottom: 24px;
    overflow: hidden;
}}
.laudo-header-deco {{
    position: absolute;
    top: -20px;
    right: -20px;
    width: 140px;
    height: 140px;
    border-radius: 0 0 0 100%;
    border: 2px solid {COLORS['cyan']};
    opacity: 0.45;
    pointer-events: none;
}}
.laudo-header-deco::before {{
    content: "";
    position: absolute;
    inset: 12px;
    border-radius: 0 0 0 100%;
    border: 1.5px solid {COLORS['navy']};
    opacity: 0.5;
}}
.laudo-header-deco::after {{
    content: "";
    position: absolute;
    inset: 26px;
    border-radius: 0 0 0 100%;
    border: 1px solid {COLORS['cyan']};
    opacity: 0.35;
}}
.laudo-header-body {{
    display: flex;
    align-items: center;
    gap: 24px;
    position: relative;
    z-index: 1;
}}
.laudo-header-logo img {{
    max-height: 48px;
    width: auto;
    object-fit: contain;
    display: block;
}}
.laudo-header-lab {{
    display: block;
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: {COLORS['grey_text']} !important;
    margin-bottom: 4px;
}}
.laudo-header-info h1 {{
    color: {COLORS['navy']} !important;
    font-size: 1.25rem;
    font-weight: 700;
    letter-spacing: 0.04em;
    text-transform: uppercase;
    margin: 0 !important;
    line-height: 1.15;
}}
.laudo-header-info p,
.laudo-header-info .laudo-header-sub {{
    color: {COLORS['grey_text']} !important;
    font-size: 0.85rem;
    margin: 2px 0 0 !important;
    padding: 0 !important;
    line-height: 1.2;
    font-weight: 400;
    text-transform: none !important;
    letter-spacing: normal !important;
}}
.edp-badge {{
    background: {COLORS['green']};
    color: white !important;
    font-size: 0.75rem;
    font-weight: 600;
    padding: 4px 12px;
    border-radius: 4px;
    letter-spacing: 0.05em;
}}

/* KPI cards */
.kpi-row {{
    display: grid !important;
    grid-template-columns: repeat(4, 1fr) !important;
    gap: 16px;
    margin-bottom: 24px;
    width: 100%;
}}
[data-testid="stMarkdownContainer"] .kpi-row {{
    display: grid !important;
    grid-template-columns: repeat(4, 1fr) !important;
}}
.kpi-card {{
    background: {COLORS['white']};
    border-radius: 6px;
    padding: 18px 14px 22px;
    text-align: center;
    border: 1px solid {COLORS['border']};
    box-shadow: none;
    border-top: 3px solid {COLORS['green']};
    color: {COLORS['navy']} !important;
    position: relative;
    transition: box-shadow 0.15s ease, border-color 0.15s ease;
}}
.kpi-card.kpi-clickable:hover {{
    box-shadow: 0 4px 14px rgba(13, 40, 64, 0.1);
    border-color: {COLORS['green']};
}}
.kpi-card-icons {{
    position: absolute;
    top: 8px;
    right: 8px;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 3px;
    z-index: 2;
}}
.kpi-card-icons .info-tip,
.kpi-card-icons .kpi-drill-link {{
    pointer-events: auto;
}}
.kpi-card .kpi-hint,
.kpi-card .kpi-drill-link {{
    color: {COLORS['grey_text']};
    width: 14px;
    height: 14px;
    line-height: 0;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
    text-decoration: none;
    cursor: pointer;
}}
.kpi-card .kpi-hint svg,
.kpi-card .kpi-drill-link svg {{
    display: block;
}}
.kpi-card.kpi-clickable:hover .kpi-hint,
.kpi-card.kpi-clickable:hover .kpi-drill-link {{
    color: {COLORS['navy']};
}}
.kpi-col-wrap {{
    position: relative;
}}
.kpi-card .info-tip {{
    position: relative;
}}
.kpi-card.navy {{ border-top-color: {COLORS['navy']}; }}
.kpi-val {{
    font-size: 2rem;
    font-weight: 700;
    color: {COLORS['navy']} !important;
    line-height: 1;
}}
.kpi-lbl {{
    font-size: 0.78rem;
    color: {COLORS['grey_text']} !important;
    margin-top: 6px;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    font-weight: 600;
}}
.kpi-period {{
    font-size: 0.9rem;
    color: {COLORS['navy']} !important;
    margin: 14px 0 24px 2px;
}}
.kpi-period strong {{
    color: {COLORS['navy']} !important;
}}
.detail-action-row div[data-testid="stHorizontalBlock"] button {{
    background: {COLORS['bg']} !important;
    color: {COLORS['navy']} !important;
    border: 1px solid {COLORS['border']} !important;
    font-size: 0.78rem !important;
    min-height: 34px !important;
    padding: 4px 10px !important;
}}
.detail-action-row div[data-testid="stHorizontalBlock"] button p,
.detail-action-row div[data-testid="stHorizontalBlock"] button span {{
    font-size: 0.78rem !important;
    font-weight: 600 !important;
    color: {COLORS['navy']} !important;
    -webkit-text-fill-color: {COLORS['navy']} !important;
}}
.detail-action-row div[data-testid="stHorizontalBlock"] button:hover {{
    background: {COLORS['light_blue']} !important;
    border-color: {COLORS['green']} !important;
}}
.ver-todos-btn div[data-testid="stButton"] > button {{
    background: transparent !important;
    color: {COLORS['grey_text']} !important;
    border: none !important;
    font-size: 0.72rem !important;
    font-weight: 600 !important;
    min-height: 28px !important;
    padding: 0 !important;
    justify-content: flex-end !important;
}}
.ver-todos-btn div[data-testid="stButton"] > button:hover {{
    color: {COLORS['green']} !important;
    background: transparent !important;
}}
.ver-todos-btn div[data-testid="stButton"] > button p,
.ver-todos-btn div[data-testid="stButton"] > button span {{
    color: inherit !important;
    -webkit-text-fill-color: inherit !important;
    font-size: 0.72rem !important;
}}
.detail-links {{
    font-size: 0.82rem;
    color: {COLORS['grey_text']} !important;
    margin: -8px 0 16px 2px;
    line-height: 1.8;
}}

/* Chart card */
.chart-card {{
    background: {COLORS['white']};
    border-radius: 6px;
    padding: 20px 24px 8px;
    border: 1px solid {COLORS['border']};
    box-shadow: none;
    margin-bottom: 20px;
    color: {COLORS['navy']} !important;
}}
.chart-title {{
    font-size: 0.88rem;
    font-weight: 600;
    color: {COLORS['navy']} !important;
    letter-spacing: 0.02em;
    flex: 1;
}}
.chart-title-row {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 10px;
    margin-bottom: 12px;
    padding-bottom: 10px;
    border-bottom: 1px solid {COLORS['border']};
}}
.info-tip {{
    position: relative;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    color: {COLORS['grey_text']} !important;
    cursor: help;
    flex-shrink: 0;
    vertical-align: middle;
    line-height: 1;
}}
.info-tip svg {{
    display: block;
}}
.info-tip:hover,
.info-tip:focus,
.info-tip:active {{
    color: {COLORS['navy']} !important;
    outline: none;
}}
.info-tip-text {{
    visibility: hidden;
    opacity: 0;
    position: absolute;
    right: 0;
    top: calc(100% + 8px);
    z-index: 50;
    width: min(280px, 70vw);
    background: {COLORS['white']};
    color: {COLORS['navy']} !important;
    border: 1px solid {COLORS['border']};
    padding: 9px 11px;
    border-radius: 8px;
    font-size: 0.72rem;
    font-weight: 500;
    line-height: 1.45;
    text-align: left;
    text-transform: none;
    letter-spacing: normal;
    box-shadow: 0 6px 18px rgba(13, 40, 64, 0.12);
    pointer-events: none;
    transition: opacity 0.15s ease;
}}
.info-tip:hover .info-tip-text,
.info-tip:focus .info-tip-text,
.info-tip:active .info-tip-text {{
    visibility: visible;
    opacity: 1;
}}

.timeline-chart-wrap {{
    overflow-x: auto;
    width: 100%;
    margin-bottom: 8px;
}}
.timeline-chart-wrap [data-testid="stPlotlyChart"] {{
    min-width: 100%;
}}

/* Person cards */
.person-card {{
    background: {COLORS['white']};
    border-radius: 6px;
    overflow: hidden;
    border: 1px solid {COLORS['border']};
    box-shadow: none;
    margin-bottom: 16px;
    color: {COLORS['navy']} !important;
}}
.person-header {{
    padding: 14px 18px;
    color: white !important;
    font-weight: 600;
    font-size: 0.95rem;
}}
.person-header.propria {{ background: {COLORS['navy']}; }}
.person-header.terceirizada {{ background: {COLORS['green']}; }}
.person-body {{
    padding: 16px 18px;
    color: {COLORS['navy']} !important;
}}
.insight-badge {{
    display: inline-block;
    background: {COLORS['light_blue']};
    color: {COLORS['navy']} !important;
    font-size: 0.72rem;
    font-weight: 600;
    padding: 3px 10px;
    border-radius: 20px;
    margin-bottom: 8px;
    text-transform: uppercase;
    letter-spacing: 0.04em;
}}
.insight-badge.green {{
    background: {COLORS['light_green']};
    color: {COLORS['navy']} !important;
}}
.person-desc {{
    font-size: 0.82rem;
    color: {COLORS['grey_text']} !important;
    margin-bottom: 12px;
    line-height: 1.5;
}}
.partner-row {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 6px 0;
    border-bottom: 1px solid {COLORS['border']};
    font-size: 0.82rem;
    color: {COLORS['navy']} !important;
}}
.partner-row b {{
    color: {COLORS['navy']} !important;
}}

/* Lista compacta — Cadastro */
.colab-table-wrap {{
    max-height: 520px;
    overflow-y: auto;
    border: 1px solid {COLORS['border']};
    border-radius: 6px;
}}
.colab-table {{
    width: 100%;
    border-collapse: collapse;
    font-size: 0.84rem;
}}
.colab-table thead {{
    position: sticky;
    top: 0;
    z-index: 1;
    background: {COLORS['grey']};
}}
.colab-table th {{
    padding: 8px 12px;
    text-align: left;
    font-size: 0.72rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    color: {COLORS['grey_text']} !important;
    border-bottom: 1px solid {COLORS['border']};
}}
.colab-table td {{
    padding: 9px 12px;
    color: {COLORS['navy']} !important;
    border-bottom: 1px solid {COLORS['border']};
}}
.colab-table tbody tr:last-child td {{
    border-bottom: none;
}}
.colab-table tbody tr:hover {{
    background: {COLORS['light_blue']};
}}
.colab-table .pill {{
    font-size: 0.68rem;
    padding: 2px 8px;
    color: {COLORS['white']} !important;
    -webkit-text-fill-color: {COLORS['white']} !important;
}}
.partner-total {{
    background: {COLORS['light_blue']};
    color: {COLORS['navy']} !important;
    border-radius: 50%;
    width: 28px;
    height: 28px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 700;
    font-size: 0.75rem;
    flex-shrink: 0;
}}

/* Rank list rows */
.rank-row {{
    color: {COLORS['navy']} !important;
}}
.rank-row span {{
    color: {COLORS['navy']} !important;
}}

/* Table styling */
table.data-table {{
    width: 100%;
    border-collapse: collapse;
    font-size: 0.82rem;
    color: {COLORS['navy']} !important;
}}
table.data-table thead tr {{
    background: {COLORS['grey']};
    border-bottom: 2px solid {COLORS['border']};
}}
table.data-table th {{
    padding: 10px 14px;
    text-align: left;
    color: {COLORS['navy']} !important;
    font-weight: 700;
    font-size: 0.72rem;
    text-transform: uppercase;
    letter-spacing: 0.04em;
}}
table.data-table td {{
    padding: 10px 14px;
    text-align: left;
    color: {COLORS['text']} !important;
    font-weight: 500;
    border-bottom: 1px solid {COLORS['border']};
}}
table.data-table tbody tr {{
    background: {COLORS['white']};
}}
table.data-table tbody tr:nth-child(even) {{ background: {COLORS['bg']}; }}
table.data-table tbody tr:hover {{ background: {COLORS['light_blue']}; }}

.pill {{
    display: inline-block;
    padding: 2px 10px;
    border-radius: 20px;
    font-size: 0.72rem;
    font-weight: 600;
    color: {COLORS['white']} !important;
    -webkit-text-fill-color: {COLORS['white']} !important;
}}
.pill.propria {{ background: {COLORS['navy']}; color: {COLORS['white']} !important; }}
.pill.terceirizada {{ background: {COLORS['green']}; color: {COLORS['white']} !important; }}
.pill.mista {{ background: {COLORS['mista']}; color: {COLORS['white']} !important; }}
.deviation-pill {{
    display: inline-block;
    padding: 2px 8px;
    border-radius: 10px;
    font-size: 0.68rem;
    font-weight: 600;
    margin: 2px;
    color: {COLORS['navy']} !important;
    -webkit-text-fill-color: {COLORS['navy']} !important;
}}
[data-testid="stMarkdownContainer"] .deviation-pill {{
    color: {COLORS['navy']} !important;
    -webkit-text-fill-color: {COLORS['navy']} !important;
}}
[data-testid="stMarkdownContainer"] .pill,
[data-testid="stMarkdownContainer"] span.pill {{
    color: {COLORS['white']} !important;
    -webkit-text-fill-color: {COLORS['white']} !important;
}}

.section-title {{
    display: flex;
    align-items: center;
    gap: 10px;
    font-size: 0.95rem;
    font-weight: 700;
    color: {COLORS['navy']} !important;
    margin: 32px 0 18px;
    padding: 14px 18px;
    background: {COLORS['white']};
    border: 1px solid {COLORS['border']};
    border-radius: 6px;
    letter-spacing: 0.05em;
}}
.section-icon {{
    display: flex;
    align-items: center;
    flex-shrink: 0;
}}
.section-num {{
    color: {COLORS['navy']} !important;
    font-weight: 700;
}}
.section-label {{
    color: {COLORS['navy']} !important;
}}

/* Plotly — rótulos, legendas e valores */
.js-plotly-plot .barlayer text,
.js-plotly-plot .pielayer text,
.js-plotly-plot .legendtext,
.js-plotly-plot .xtick text,
.js-plotly-plot .ytick text,
.js-plotly-plot .g-xtitle text,
.js-plotly-plot .g-ytitle text {{
    fill: {COLORS['navy']} !important;
    color: {COLORS['navy']} !important;
}}

/* Alertas Streamlit */
[data-testid="stAlert"] {{
    color: {COLORS['navy']} !important;
}}

#MainMenu, footer, header {{ visibility: hidden; }}

/* Rodapé — barra verde estilo laudo */
.laudo-footer {{
    margin-top: 48px;
}}
.laudo-footer-gradient {{
    height: 3px;
    background: linear-gradient(
        90deg,
        {COLORS['cyan']} 0%,
        #E6007E 33%,
        #FFED00 66%,
        {COLORS['green']} 100%
    );
}}
.laudo-footer-bar {{
    height: 6px;
    background: {COLORS['green']};
}}
.laudo-footer-text {{
    text-align: center;
    font-size: 0.72rem;
    color: {COLORS['grey_text']} !important;
    padding: 14px 0 8px;
    letter-spacing: 0.04em;
}}
</style>
""",
    unsafe_allow_html=True,
)

PLOTLY_LAYOUT = dict(
    template="plotly_white",
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Source Sans 3, sans-serif", color=COLORS["navy"], size=13),
)

TEXT_COLOR = COLORS["navy"]
BAR_TEXT = dict(color=TEXT_COLOR, size=12)
TD = f'style="color:{COLORS["navy"]};font-weight:500;"'
LIGHT_BG = {
    COLORS["light_blue"],
    COLORS["light_green"],
    "#B8D9EC",
    "#A8E6C3",
    "#7EB8DA",
    "#7FD4A0",
    "#B8C4D0",
    "#F5C87A",
    "#F0A0A8",
}


def _icon_svg(paths: str, size: int = 22) -> str:
    return (
        f'<svg class="section-svg" xmlns="http://www.w3.org/2000/svg" '
        f'width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" '
        f'stroke="{COLORS["navy"]}" stroke-width="1.5" stroke-linecap="round" '
        f'stroke-linejoin="round">{paths}</svg>'
    )


SECTION_ICONS = {
    "overview": _icon_svg(
        '<path d="M18 20V10"/><path d="M12 20V4"/><path d="M6 20v-6"/>'
    ),
    "teams": _icon_svg(
        '<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/>'
        '<circle cx="9" cy="7" r="4"/>'
        '<path d="M22 21v-2a4 4 0 0 0-3-3.87"/>'
        '<path d="M16 3.13a4 4 0 0 1 0 7.75"/>'
    ),
    "duplas": _icon_svg(
        '<path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/>'
        '<path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/>'
    ),
    "individual": _icon_svg(
        '<path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>'
        '<circle cx="12" cy="7" r="4"/>'
    ),
    "patterns": _icon_svg(
        '<circle cx="11" cy="11" r="8"/>'
        '<path d="m21 21-4.3-4.3"/>'
    ),
    "cities": _icon_svg(
        '<path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/>'
        '<circle cx="12" cy="10" r="3"/>'
    ),
    "cadastro": _icon_svg(
        '<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/>'
        '<circle cx="9" cy="7" r="4"/>'
        '<path d="M19 8v6"/><path d="M22 11h-6"/>'
    ),
}


INFO = {
    "kpi_medidores": (
        "Total de medidores ensaiados registrados na ficha de monitoramento "
        "no período selecionado. Clique para ver a lista completa."
    ),
    "kpi_tois_desvio": (
        "Quantidade de TOIs com ao menos um desvio apontado pelo laboratório. "
        "Clique para ver os registros."
    ),
    "kpi_pct_desvio": (
        "Percentual de TOIs com desvio sobre o total de ensaios no período. "
        "Clique para ver os TOIs com desvio."
    ),
    "kpi_desvios_total": (
        "Soma de todas as ocorrências de desvio encontradas. Um mesmo TOI pode "
        "contar mais de uma vez. Clique para ver cada ocorrência."
    ),
    "chart_tois_equipe": (
        "Distribuição dos TOIs com desvio do laboratório por tipo de equipe: "
        "própria, terceirizada, mista ou sem identificação."
    ),
    "chart_medidor": (
        "Resultado do ensaio visual do medidor: classificação em ordem ou "
        "com irregularidade conforme a ficha de monitoramento."
    ),
    "chart_ranking_desvios": (
        "Ranking de ocorrências por tipo de desvio apontado pelo laboratório, "
        "considerando todos os TOIs com desvio."
    ),
    "chart_timeline_equipe": (
        "Evolução mensal dos TOIs com desvio por dupla de matrículas. "
        "Equipes com mais de 5 desvios no mês aparecem individualmente."
    ),
    "chart_timeline_pessoa": (
        "Evolução mensal dos TOIs com desvio por colaborador (matrícula). "
        "Colaboradores com mais de 5 desvios no mês aparecem individualmente."
    ),
    "chart_csd_pct": (
        "Percentual de TOIs com desvio do laboratório sobre o total ensaiado "
        "em cada CSD (centro de serviço)."
    ),
    "table_csd_resumo": (
        "Resumo por CSD: total de ensaios, TOIs com desvio e percentual de desvio."
    ),
    "table_colaborador": (
        "Análise por matrícula: volume de TOIs, parceiros, tendência, influência "
        "no padrão de desvio e tipos predominantes."
    ),
    "table_duplas": (
        "Duplas de colaboradores com maior volume de TOIs com desvio e os "
        "tipos de desvio mais frequentes em cada dupla."
    ),
    "table_cidades": (
        "Comparativo por cidade (CSD) entre equipe própria e terceirizada "
        "nos TOIs com desvio."
    ),
    "cadastro_colaboradores": (
        "Colaboradores únicos identificados na base, com tipo de equipe, "
        "aparições e CSDs em que atuaram."
    ),
    "cadastro_csds": (
        "CSDs presentes na base com quantidade de ensaios, rotatividade de "
        "equipes e colaboradores envolvidos."
    ),
    "cadastro_kpi_total": "Total de matrículas distintas encontradas na base.",
    "cadastro_kpi_propria": "Colaboradores classificados como equipe própria.",
    "cadastro_kpi_terceirizada": "Colaboradores classificados como terceirizados.",
    "cadastro_kpi_csds": "Quantidade de CSDs distintos com ensaios na base.",
    "inconsist_grupos": "Total de grupos de inconsistência detectados na base.",
    "inconsist_lab": "Divergências entre o apontamento do laboratório e a ficha.",
    "inconsist_equipe": "Registros com equipe divergente entre fontes.",
    "inconsist_dup": "Registros duplicados que precisam de revisão.",
    "inconsist_missing": "Registros com campos obrigatórios faltando.",
}


def _click_icon(view: str, size: int = 14) -> str:
    """Link para tela de detalhes (ícone de abrir em outra página)."""
    drill = quote(view, safe="")
    return (
        f'<a class="kpi-drill-link kpi-hint" href="?drill={drill}" '
        f'title="Abrir tela de detalhes" aria-label="Abrir tela de detalhes">'
        f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" '
        f'stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
        f'<path d="M15 3h6v6"/>'
        f'<path d="M10 14 21 3"/>'
        f'<path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>'
        f"</svg></a>"
    )


def _info_icon(text: str, size: int = 15) -> str:
    tip = html.escape(text, quote=True)
    return (
        f'<span class="info-tip" tabindex="0" role="button" aria-label="Informação">'
        f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" '
        f'stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
        f'<circle cx="12" cy="12" r="10"/><path d="M12 16v-4"/><path d="M12 8h.01"/>'
        f"</svg>"
        f'<span class="info-tip-text">{tip}</span></span>'
    )


def _chart_title_row(title: str, info: str | None = None) -> str:
    tip = _info_icon(info) if info else ""
    return (
        f'<div class="chart-title-row">'
        f'<span class="chart-title">{title}</span>{tip}</div>'
    )


def _kpi_card_html(
    value,
    label: str,
    info: str,
    style: str = "",
    value_color: str | None = None,
    drill_view: str | None = None,
) -> str:
    color = value_color or COLORS["navy"]
    click_cls = " kpi-clickable" if drill_view else ""
    hint = _click_icon(drill_view) if drill_view else ""
    icons = f'<div class="kpi-card-icons">{_info_icon(info, size=14)}{hint}</div>'
    return (
        f'<div class="kpi-card{click_cls} {style}">{icons}'
        f'<div class="kpi-val" style="color:{color};">{value}</div>'
        f'<div class="kpi-lbl">{label}</div></div>'
    )


def _section(num: int, icon_key: str, title: str) -> str:
    icon = SECTION_ICONS.get(icon_key, "")
    return (
        f'<div class="section-title">'
        f'<span class="section-icon">{icon}</span>'
        f'<span class="section-label">'
        f'<span class="section-num">{num}.</span> {title.upper()}'
        f"</span></div>"
    )


def _pill_style(bg: str) -> str:
    fg = COLORS["navy"] if bg in LIGHT_BG else "white"
    return (
        f"background:{bg};color:{fg};padding:2px 8px;border-radius:10px;"
        f"font-size:0.68rem;margin:2px;display:inline-block;font-weight:600;"
    )


def _deviation_pill_style(label: str) -> str:
    bg = DEVIATION_PILL_COLORS.get(label, COLORS["light_blue"])
    return (
        f"background:{bg};padding:2px 8px;border-radius:10px;"
        f"font-size:0.68rem;margin:2px;display:inline-block;font-weight:600;"
    )


def _deviation_pill(label: str, count: int) -> str:
    return (
        f'<span class="deviation-pill" style="{_deviation_pill_style(label)}">'
        f"{label} ×{count}</span>"
    )


def handle_drill_query() -> None:
    """Navega para detalhe quando o ícone do KPI define ?drill= na URL."""
    drill = st.query_params.get("drill")
    if not drill:
        return
    if "drill" in st.query_params:
        del st.query_params["drill"]
    go_detalhe(drill)


def go_detalhe(view: str, **filters) -> None:
    st.session_state.app_page = "detalhe"
    st.session_state.detalhe_view = view
    st.session_state.detalhe_filters = {
        k: str(v).strip()
        for k, v in filters.items()
        if v is not None and str(v).strip() not in ("", "nan", "—")
    }
    st.rerun()


def ver_todos_button(view: str, key: str, **filters) -> None:
    st.markdown('<div class="ver-todos-btn">', unsafe_allow_html=True)
    if st.button("Ver todos →", key=key, type="secondary"):
        go_detalhe(view, **filters)
    st.markdown("</div>", unsafe_allow_html=True)


def render_detail_buttons(items: list[tuple[str, str, dict]], key_prefix: str) -> None:
    """Botões compactos para abrir detalhes sem recarregar a página."""
    if not items:
        return
    st.markdown('<div class="detail-action-row">', unsafe_allow_html=True)
    cols = st.columns(min(len(items), 4))
    for i, (label, view, filters) in enumerate(items):
        with cols[i % len(cols)]:
            if st.button(label, key=f"{key_prefix}_{i}", use_container_width=True, type="secondary"):
                go_detalhe(view, **filters)
    st.markdown("</div>", unsafe_allow_html=True)


def _chart_card(title: str, info: str | None = None) -> str:
    return (
        f'<div class="chart-card" style="color:{COLORS["navy"]};">'
        f"{_chart_title_row(title, info)}"
    )


def _axis(**extra):
    opts = dict(
        tickfont=dict(color=TEXT_COLOR, size=12),
        gridcolor=COLORS["grey"],
    )
    if "title" in extra:
        t = extra.pop("title")
        if isinstance(t, str) and t:
            opts["title"] = dict(text=t, font=dict(color=TEXT_COLOR, size=12))
        elif t:
            opts["title"] = t
    opts.update(extra)
    return opts


def finalize_fig(fig, **layout_kwargs):
    if "legend" not in layout_kwargs:
        layout_kwargs["legend"] = dict(
            font=dict(color=TEXT_COLOR, size=12),
            bgcolor="rgba(255,255,255,0.9)",
        )
    fig.update_layout(**PLOTLY_LAYOUT, **layout_kwargs)
    fig.update_xaxes(tickfont=dict(color=TEXT_COLOR, size=12))
    fig.update_yaxes(tickfont=dict(color=TEXT_COLOR, size=12))
    return fig


def _detect_image_type(path: Path) -> str:
    """Detecta tipo real pelo conteúdo (ignora extensão errada)."""
    with open(path, "rb") as f:
        header = f.read(32)
    if header.startswith(b"<svg") or header.startswith(b"<?xml"):
        return "svg"
    if header.startswith(b"\x89PNG"):
        return "png"
    if header.startswith(b"\xff\xd8"):
        return "jpeg"
    return path.suffix.lower().lstrip(".")


def get_logo_path() -> Path | None:
    """Retorna o caminho da logo se existir em assets/logo/."""
    if not LOGO_DIR.exists():
        return None
    for name in LOGO_FILENAMES:
        path = LOGO_DIR / name
        if path.is_file():
            return path.resolve()
    for ext in ("*.png", "*.svg", "*.jpg", "*.jpeg", "*.webp"):
        for path in sorted(LOGO_DIR.glob(ext)):
            if path.name.startswith("."):
                continue
            return path.resolve()
    return None


def logo_img_html(width: int = 110, max_height: int = 36) -> str:
    """Retorna tag HTML da logo para uso em cabeçalhos."""
    path = get_logo_path()
    if not path:
        return '<div class="edp-badge">EDP SP</div>'

    img_type = _detect_image_type(path)
    if img_type == "svg":
        import base64

        svg_path = path
        if path.suffix.lower() != ".svg":
            svg_path = path.with_suffix(".svg")
            if not svg_path.exists():
                svg_path.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
        encoded = base64.b64encode(svg_path.read_bytes()).decode()
        return (
            f'<img src="data:image/svg+xml;base64,{encoded}" alt="EDP" '
            f'style="max-height:{max_height}px;width:auto;max-width:{width}px;">'
        )

    import base64

    mime_map = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
    }
    mime = mime_map.get(path.suffix.lower(), "image/png")
    encoded = base64.b64encode(path.read_bytes()).decode()
    return (
        f'<img src="data:{mime};base64,{encoded}" alt="EDP" '
        f'style="max-height:{max_height}px;width:auto;max-width:{width}px;">'
    )


def render_dash_header() -> None:
    st.markdown(
        f"""
<div class="laudo-header">
  <div class="laudo-header-deco"></div>
  <div class="laudo-header-body">
    <div class="laudo-header-logo">{logo_img_html(width=150, max_height=48)}</div>
    <div class="laudo-header-info">
      <h1>Qualidade do TOI</h1>
      <p class="laudo-header-sub">Laboratório de Medição</p>
    </div>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )


def render_dash_footer() -> None:
    st.markdown(
        f"""
<div class="laudo-footer">
  <div class="laudo-footer-gradient"></div>
  <div class="laudo-footer-bar"></div>
  <div class="laudo-footer-text">
    EDP São Paulo · Laboratório de Medição · Dashboard Qualidade do TOI
  </div>
</div>
""",
        unsafe_allow_html=True,
    )


def show_logo(width: int = 200) -> bool:
    """Exibe a logo. Suporta PNG/JPG via st.image e SVG inline."""
    path = get_logo_path()
    if not path:
        return False

    img_type = _detect_image_type(path)

    if img_type == "svg":
        st.markdown(
            f'<div class="logo-svg" style="max-width:{width}px;margin:0 auto;">'
            f"{logo_img_html(width, min(width, 72))}"
            f"</div>",
            unsafe_allow_html=True,
        )
        return True

    st.image(str(path), width=width)
    return True


def brand_fallback_html() -> str:
    return (
        f'<div class="login-logo" style="color:{COLORS["navy"]};">'
        f'EDP <span style="color:{COLORS["green"]};">SP</span></div>'
    )


def check_password() -> bool:
    if st.session_state.get("authenticated"):
        return True

    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.markdown('<span class="login-panel-anchor"></span>', unsafe_allow_html=True)
        if not show_logo(width=200):
            st.markdown(brand_fallback_html(), unsafe_allow_html=True)
        st.markdown(
            f'<div class="login-sub" style="text-align:center;width:100%;">Qualidade do TOI</div>'
            f'<div style="text-align:center;font-size:0.78rem;color:{COLORS["grey_text"]};'
            f'letter-spacing:0.06em;text-transform:uppercase;margin-bottom:28px;">'
            f'Laboratório de Medição · EDP SP</div>',
            unsafe_allow_html=True,
        )
        perfil_key = st.selectbox(
            "Perfil de acesso",
            options=list(ACCESS_PROFILES.keys()),
            format_func=lambda k: ACCESS_PROFILES[k]["label"],
            key="login_profile",
        )
        pwd = st.text_input("Senha de acesso", type="password", key="pwd_input")
        if st.button("Entrar", use_container_width=True, type="secondary"):
            perfil = ACCESS_PROFILES.get(perfil_key)
            if perfil and pwd == perfil["password"]:
                st.session_state["authenticated"] = True
                st.session_state["profile"] = perfil_key
                st.session_state["app_page"] = perfil["pages"][0]
                st.rerun()
            else:
                st.markdown(
                    '<div class="login-error">Senha incorreta para o perfil selecionado.</div>',
                    unsafe_allow_html=True,
                )
        st.markdown(
            f"""<style>
            div[data-testid="stButton"] > button,
            button[data-testid="stBaseButton-secondary"],
            button[data-testid="stBaseButton-primary"] {{
                background: {COLORS['green']} !important;
                background-color: {COLORS['green']} !important;
                color: {COLORS['white']} !important;
                border: none !important;
            }}
            div[data-testid="stButton"] > button p {{
                color: {COLORS['white']} !important;
            }}
            div[data-testid="stTextInput"] div[data-baseweb="input"] {{
                background-color: {COLORS['white']} !important;
                border: 1px solid {COLORS['grey']} !important;
            }}
            div[data-testid="stTextInput"] div[data-baseweb="input"]:focus-within,
            div[data-testid="stTextInput"] div[data-baseweb="input"]:focus {{
                border: 1px solid {COLORS['green']} !important;
                box-shadow: none !important;
                outline: none !important;
            }}
            div[data-testid="stTextInput"] input {{
                background-color: transparent !important;
                color: {COLORS['navy']} !important;
                -webkit-text-fill-color: {COLORS['navy']} !important;
                outline: none !important;
            }}
            div[data-testid="stTextInput"] input:focus,
            div[data-testid="stTextInput"] input:focus-visible {{
                outline: none !important;
                box-shadow: none !important;
            }}
            </style>""",
            unsafe_allow_html=True,
        )
    return False


def bar_color_alternate(idx: int, count: int) -> str:
    return CHART_PALETTE[idx % len(CHART_PALETTE)]


def _team_bar_color(tipo: str) -> str:
    if tipo == "Própria":
        return CHART_TEAM_COLORS["propria"]
    return CHART_TEAM_COLORS["terceirizada"]


def equipe_chart_color(equipe: str, idx: int) -> str:
    """Cor distinta por equipe no gráfico temporal (paleta clara EDP)."""
    if equipe == "Sem matrícula":
        return CHART_TEAM_COLORS["sem_equipe"]
    if equipe in ("Outras equipes", "Outras pessoas"):
        return CHART_TEAM_COLORS["mista"]
    return CHART_PALETTE[idx % len(CHART_PALETTE)]


def render_kpis(metrics: dict, df: pd.DataFrame):
    periodo = periodo_agendamento(df)
    tois_com_desvio = count_desvios_laboratorio(df)
    total_desvios = count_total_desvios_encontrados(df)
    pct_desvio = pct_tois_com_desvio(df)
    kpis = [
        (
            "kpi_medidores",
            "medidores_ensaiados",
            f"{metrics['total_ensaios']:,}",
            "Medidores ensaiados",
            "kpi_medidores",
            "navy",
            None,
        ),
        (
            "kpi_tois",
            "tois_com_desvio",
            f"{tois_com_desvio:,}",
            "TOIs com Desvio",
            "kpi_tois_desvio",
            "",
            COLORS["red"],
        ),
        (
            "kpi_pct",
            "tois_com_desvio",
            f"{pct_desvio}%",
            "% TOIs com Desvio",
            "kpi_pct_desvio",
            "",
            COLORS["red"],
        ),
        (
            "kpi_desvios",
            "desvios_encontrados",
            f"{total_desvios:,}",
            "Desvios Encontrados",
            "kpi_desvios_total",
            "",
            COLORS["red"],
        ),
    ]
    cols = st.columns(4, gap="medium")
    for col, (key, view, value, label, info_key, style, val_color) in zip(cols, kpis):
        with col:
            st.markdown(
                f'<div class="kpi-col-wrap">{_kpi_card_html(value, label, INFO[info_key], style, val_color, drill_view=view)}</div>',
                unsafe_allow_html=True,
            )
    st.markdown(
        f'<p class="kpi-period"><strong>Período:</strong> {periodo}</p>',
        unsafe_allow_html=True,
    )


def chart_desvios_equipe_donut(summary: dict):
    labels = [
        f"Equipe Própria ({summary['pct_propria']}%)",
        f"Terceirizada ({summary['pct_terceirizada']}%)",
    ]
    values = [summary["propria"], summary["terceirizada"]]
    colors = [
        CHART_TEAM_COLORS["propria"],
        CHART_TEAM_COLORS["terceirizada"],
    ]
    if summary.get("mista", 0) > 0:
        labels.append(f"Mista ({summary['pct_mista']}%)")
        values.append(summary["mista"])
        colors.append(CHART_TEAM_COLORS["mista"])
    if summary.get("sem_equipe", 0) > 0:
        labels.append(f"Sem equipe ({summary['pct_sem_equipe']}%)")
        values.append(summary["sem_equipe"])
        colors.append(CHART_TEAM_COLORS["sem_equipe"])
    fig = go.Figure(
        go.Pie(
            labels=labels,
            values=values,
            hole=0.55,
            marker=dict(colors=colors),
            textinfo="none",
            hovertemplate="%{label}<br>%{value} TOIs<extra></extra>",
        )
    )
    fig.update_layout(
        showlegend=True,
        legend=dict(orientation="h", y=-0.05, x=0.5, xanchor="center"),
        height=340,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        template="plotly_white",
    )
    return fig


def chart_laudo_donut(summary: dict):
    fig = go.Figure(
        go.Pie(
            labels=[
                f"Laudo correto ({summary['pct_sim']}%)",
                f"Laudo incorreto ({summary['pct_nao']}%)",
                f"Pendente ({summary['pct_pendente']}%)",
            ],
            values=[summary["sim"], summary["nao"], summary["pendente"]],
            hole=0.55,
            marker=dict(colors=[
                CHART_TEAM_COLORS["laudo_sim"],
                CHART_TEAM_COLORS["laudo_nao"],
                CHART_TEAM_COLORS["laudo_pendente"],
            ]),
            textinfo="none",
            hovertemplate="%{label}<br>%{value} registros<extra></extra>",
        )
    )
    fig.update_layout(
        showlegend=True,
        legend=dict(orientation="h", y=-0.05, x=0.5, xanchor="center"),
        height=340,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        template="plotly_white",
    )
    return fig


def chart_medidor_donut(summary: dict):
    fig = go.Figure(
        go.Pie(
            labels=[
                f"Medidor em ordem ({summary['pct_ordem']}%)",
                f"Com irregularidade ({summary['pct_irregular']}%)",
            ],
            values=[summary["em_ordem"], summary["irregular"]],
            hole=0.55,
            marker=dict(colors=[
                CHART_TEAM_COLORS["medidor_ordem"],
                CHART_TEAM_COLORS["medidor_irregular"],
            ]),
            textinfo="none",
            hovertemplate="%{label}<br>%{value} ensaios<extra></extra>",
        )
    )
    fig.update_layout(
        showlegend=True,
        legend=dict(orientation="h", y=-0.05, x=0.5, xanchor="center"),
        height=340,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        template="plotly_white",
    )
    return fig


def chart_irregularidade_ranking(ranking: pd.DataFrame):
    colors = [
        IRREGULARIDADE_COLORS.get(row["tipo"], bar_color_alternate(i, len(ranking)))
        for i, row in ranking.iterrows()
    ]
    fig = go.Figure(
        go.Bar(
            x=ranking["count"],
            y=ranking["tipo"],
            orientation="h",
            marker=dict(color=colors, cornerradius=4),
            text=ranking["count"],
            textposition="outside",
            textfont=BAR_TEXT,
        )
    )
    finalize_fig(
        fig,
        height=max(360, len(ranking) * 36),
        xaxis=_axis(title="Ocorrências"),
        yaxis=_axis(categoryorder="total ascending"),
        margin=dict(l=220, r=40, t=10, b=20),
    )
    return fig


def chart_csd_desvio_pct(csd_df: pd.DataFrame):
    required = {"csd", "total", "com_desvio", "pct_desvio"}
    if csd_df.empty or not required.issubset(csd_df.columns):
        csd_df = csd_breakdown()
    if csd_df.empty:
        fig = go.Figure()
        finalize_fig(fig, height=200, xaxis=_axis(), yaxis=_axis(title="% TOIs com desvio"))
        return fig

    df = csd_df.sort_values("total", ascending=False)
    colors = [CHART_PALETTE[i % len(CHART_PALETTE)] for i in range(len(df))]
    labels = [
        f"{int(r['com_desvio'])} - {r['pct_desvio']:.1f}%".replace(".", ",")
        for _, r in df.iterrows()
    ]
    y_max = float(df["pct_desvio"].max()) if not df.empty else 10
    fig = go.Figure(
        go.Bar(
            x=df["csd"],
            y=df["pct_desvio"],
            marker=dict(color=colors, cornerradius=4),
            text=labels,
            textposition="outside",
            textfont=BAR_TEXT,
            hovertemplate=(
                "%{x}<br>%{customdata[0]} TOIs com desvio / %{customdata[1]} ensaiados"
                "<br>%{y:.1f}%<extra></extra>"
            ),
            customdata=df[["com_desvio", "total"]].values,
        )
    )
    finalize_fig(
        fig,
        height=max(380, len(df) * 28),
        xaxis=_axis(title="CSD (cidade)", tickangle=-25),
        yaxis=_axis(title="% TOIs com desvio", range=[0, max(y_max * 1.15, 10)]),
        showlegend=False,
        margin=dict(l=50, r=30, t=20, b=80),
    )
    return fig


def _mes_label(mes: str) -> str:
    try:
        return pd.Period(mes, freq="M").strftime("%m/%Y")
    except (ValueError, TypeError):
        return str(mes)


def _label_text_color(hex_color: str) -> str:
    return COLORS["navy"]


def _equipe_label_lines(name: str) -> str:
    if name in ("Sem matrícula", "Outras equipes", "Outras pessoas"):
        return name
    parts = name.split(" - ")
    if len(parts) == 2:
        return f"{parts[0]}<br>{parts[1]}"
    return name


def _pessoa_label_lines(pessoa: str) -> str:
    if pessoa == "Outras pessoas":
        return pessoa
    return pessoa


def _annotation_font_size(val: float) -> int:
    if val >= 20:
        return 9
    if val >= 10:
        return 8
    return 7


TIMELINE_DESVIOS_HEIGHT = 1320
TIMELINE_DESVIOS_MIN_WIDTH = 1680
TIMELINE_DESVIOS_WIDTH_PER_MONTH = 150


def _stack_segment_annotations(
    labels: list[str],
    segments: list[tuple],
    outras_label: str = "Outras equipes",
    label_lines=_equipe_label_lines,
    inline_labels: bool = False,
) -> list[dict]:
    """Anotações centradas em cada faixa empilhada (sempre visíveis)."""
    n = len(labels)
    cum = [0.0] * n
    annotations: list[dict] = []
    for segment in segments:
        y_vals, color = segment[0], segment[2]
        count_vals = segment[3] if len(segment) > 3 else y_vals
        if segment[1] == "__outras__":
            outras_por_mes = segment[4] if len(segment) > 4 else None
        else:
            outras_por_mes = None
            entity = segment[1]

        text_color = _label_text_color(color)
        for j, label in enumerate(labels):
            val = float(y_vals[j])
            if val <= 0:
                continue
            count = int(count_vals[j])
            y_mid = cum[j] + val / 2
            cum[j] += val
            if outras_por_mes is not None:
                text = (
                    f"{outras_label} ({outras_por_mes[j]})"
                    f"<br>{count} desv."
                )
            elif inline_labels:
                text = f"{label_lines(entity)} · {count} desv."
            else:
                text = f"{label_lines(entity)}<br>{count} desv."
            annotations.append(
                {
                    "x": label,
                    "y": y_mid,
                    "text": text,
                    "showarrow": False,
                    "xref": "x",
                    "yref": "y",
                    "xanchor": "center",
                    "yanchor": "middle",
                    "font": {
                        "size": _annotation_font_size(count),
                        "color": text_color,
                    },
                }
            )
    return annotations


def _timeline_monthly_scale(
    meses: list,
    pivot: pd.DataFrame,
    totals: pd.DataFrame,
    entity_col: str,
) -> dict:
    """Por colaborador, cada TOI conta para 2 pessoas — escala barras ao total de TOIs."""
    totals_idx = totals.set_index("mes")
    scale: dict = {}
    for mes in meses:
        stack_sum = float(pivot.loc[mes].sum()) if mes in pivot.index else 0.0
        if mes in totals_idx.index:
            target = float(totals_idx.loc[mes, "tois_com_desvio"])
        else:
            target = stack_sum
        if entity_col == "pessoa" and stack_sum > 0 and target > 0:
            scale[mes] = target / stack_sum
        else:
            scale[mes] = 1.0
    return scale


def _scale_series(values: pd.Series, meses: list, monthly_scale: dict) -> list[float]:
    return [float(values.get(m, 0)) * monthly_scale.get(m, 1.0) for m in meses]


def _inside_bar_labels(y_vals, name: str, min_height: int = 3) -> list[str]:
    labels = []
    for v in y_vals:
        n = int(v)
        if n >= min_height:
            labels.append(f"{name}<br>{n} desv.")
        else:
            labels.append("")
    return labels


def _inside_outras_labels(
    y_vals, equipes_por_mes: list[int], min_height: int = 3
) -> list[str]:
    labels = []
    for v, n_equipes in zip(y_vals, equipes_por_mes):
        n = int(v)
        if n >= min_height:
            labels.append(f"Outras equipes ({n_equipes})<br>{n} desv.")
        else:
            labels.append("")
    return labels


MIN_DESVIOS_EQUIPE_INDIVIDUAL = 5


def _split_timeline_pivot(pivot: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series, list[str], pd.DataFrame]:
    """Por mês: >5 desvios = faixa individual; demais vão para Outras equipes."""
    limiar = MIN_DESVIOS_EQUIPE_INDIVIDUAL
    individual = pivot.where(pivot > limiar, 0)
    outras_detail = pivot.where((pivot > 0) & (pivot <= limiar), 0)
    outras = outras_detail.sum(axis=1)
    top_equipes = [
        e for e in pivot.columns if (pivot[e] > limiar).any()
    ]
    top_equipes.sort(key=lambda e: pivot[e].sum(), reverse=True)
    return individual, outras, top_equipes, outras_detail


def chart_timeline_desvios(
    entity_timeline: pd.DataFrame,
    totals: pd.DataFrame,
    entity_col: str = "equipe",
    outras_label: str = "Outras equipes",
    label_lines=_equipe_label_lines,
):
    meses = sorted(entity_timeline["mes"].unique())
    labels = [_mes_label(m) for m in meses]
    pivot = (
        entity_timeline.pivot_table(
            index="mes", columns=entity_col, values="count", fill_value=0, aggfunc="sum"
        )
        .reindex(meses)
        .fillna(0)
    )
    individual, outras, top_entities, outras_detail = _split_timeline_pivot(pivot)
    monthly_scale = _timeline_monthly_scale(meses, pivot, totals, entity_col)
    segment_specs: list[tuple] = []

    fig = go.Figure()
    for i, entity in enumerate(top_entities):
        y_vals = individual[entity]
        if int(y_vals.sum()) == 0:
            continue
        color = equipe_chart_color(entity, i)
        y_counts = y_vals.tolist()
        y_display = _scale_series(y_vals, meses, monthly_scale)
        segment_specs.append((y_display, entity, color, y_counts))
        fig.add_trace(
            go.Bar(
                x=labels,
                y=y_display,
                name=entity,
                customdata=y_counts,
                marker=dict(color=color, cornerradius=2),
                hovertemplate=(
                    "%{x}<br>%{fullData.name}: %{customdata} TOIs<extra></extra>"
                ),
            )
        )
    if outras.sum() > 0:
        outras_por_mes = (outras_detail > 0).sum(axis=1).tolist()
        outras_color = equipe_chart_color(outras_label, len(top_entities))
        outras_counts = outras.tolist()
        outras_display = _scale_series(outras, meses, monthly_scale)
        segment_specs.append(
            (outras_display, "__outras__", outras_color, outras_counts, outras_por_mes)
        )
        fig.add_trace(
            go.Bar(
                x=labels,
                y=outras_display,
                name=outras_label,
                marker=dict(color=outras_color, cornerradius=2),
                customdata=list(zip(outras_counts, outras_por_mes)),
                hovertemplate=(
                    f"%{{x}}<br>{outras_label} (%{{customdata[1]}}): "
                    "%{customdata[0]} TOIs<extra></extra>"
                ),
            )
        )

    stack_annotations = _stack_segment_annotations(
        labels,
        segment_specs,
        outras_label=outras_label,
        label_lines=label_lines,
        inline_labels=(entity_col == "pessoa"),
    )
    totals_idx = totals.set_index("mes")
    annotations = list(stack_annotations)
    for mes, label in zip(meses, labels):
        if mes not in totals_idx.index:
            continue
        row = totals_idx.loc[mes]
        com_desvio = int(row["tois_com_desvio"])
        if com_desvio <= 0:
            continue
        pct_txt = f"{float(row['pct_com_desvio']):.1f}".replace(".", ",")
        annotations.append(
            {
                "x": label,
                "y": com_desvio,
                "text": f"{com_desvio} - {pct_txt}%",
                "showarrow": False,
                "yanchor": "bottom",
                "yshift": 8,
                "font": {"size": 13, "color": COLORS["navy"]},
            }
        )
    chart_width = max(
        TIMELINE_DESVIOS_MIN_WIDTH, len(labels) * TIMELINE_DESVIOS_WIDTH_PER_MONTH
    )
    y_max = float(totals["tois_com_desvio"].max()) if not totals.empty else 0
    finalize_fig(
        fig,
        width=chart_width,
        height=TIMELINE_DESVIOS_HEIGHT,
        barmode="stack",
        bargap=0.14,
        xaxis=_axis(
            title=dict(
                text="Mês (data do agendamento)",
                font=dict(color=TEXT_COLOR, size=14),
            ),
            tickfont=dict(color=TEXT_COLOR, size=13),
        ),
        yaxis=_axis(
            title=dict(
                text="TOIs com desvio",
                font=dict(color=TEXT_COLOR, size=14),
            ),
            tickfont=dict(color=TEXT_COLOR, size=13),
            range=[0, max(y_max * 1.12, 10)],
        ),
        legend=dict(orientation="h", y=-0.16, font=dict(size=11)),
        margin=dict(l=64, r=48, t=56, b=120),
        annotations=annotations,
    )
    return fig


def chart_toi_donut(summary: dict):
    fig = go.Figure(
        go.Pie(
            labels=[
                f"TOIs com Desvio ({summary['pct_com']}%)",
                f"TOIs sem Desvio ({summary['pct_sem']}%)",
            ],
            values=[summary["com_desvio"], summary["sem_desvio"]],
            hole=0.55,
            marker=dict(colors=[
                CHART_TEAM_COLORS["com_desvio"],
                CHART_TEAM_COLORS["sem_desvio"],
            ]),
            textinfo="none",
            hovertemplate="%{label}<br>%{value} TOIs<extra></extra>",
        )
    )
    fig.update_layout(
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.05,
            x=0.5,
            xanchor="center",
            font=dict(color=TEXT_COLOR, size=12),
            bgcolor="rgba(255,255,255,0.9)",
        ),
        height=340,
        font=dict(color=TEXT_COLOR, size=13),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        template="plotly_white",
    )
    return fig


def chart_desvios_ranking(ranking: pd.DataFrame, tois_com_desvio: int):
    colors = [
        DEVIATION_COLORS.get(row["tipo"], bar_color_alternate(i, row["count"]))
        for i, row in ranking.iterrows()
    ]
    fig = go.Figure(
        go.Bar(
            x=ranking["count"],
            y=ranking["tipo"],
            orientation="h",
            marker=dict(color=colors, cornerradius=4),
            text=ranking["count"],
            textposition="outside",
            textfont=BAR_TEXT,
            hovertemplate="%{y}: %{x} ocorrências<extra></extra>",
        )
    )
    finalize_fig(
        fig,
        height=max(380, len(ranking) * 32),
        xaxis=_axis(title=""),
        yaxis=_axis(categoryorder="total ascending"),
        margin=dict(l=200, r=40, t=10, b=20),
    )
    return fig


def chart_ranking(ranking: pd.DataFrame, total_dev: int):
    colors = [
        bar_color_alternate(i, row["count"])
        for i, row in ranking.iterrows()
    ]
    fig = go.Figure(
        go.Bar(
            x=ranking["count"],
            y=ranking["tipo"],
            orientation="h",
            marker=dict(color=colors, cornerradius=4),
            text=ranking["count"],
            textposition="outside",
            textfont=BAR_TEXT,
            hovertemplate="%{y}: %{x}<extra></extra>",
        )
    )
    finalize_fig(
        fig,
        height=max(380, len(ranking) * 32),
        xaxis=_axis(title=""),
        yaxis=_axis(categoryorder="total ascending"),
        margin=dict(l=180, r=40, t=10, b=20),
    )
    return fig


def chart_team_comparison(comp: pd.DataFrame):
    tipos = comp["tipo_desvio"].unique()
    fig = go.Figure()
    MIN_INSIDE = 8  # % mínimo para rótulo dentro da barra
    MIN_OFFSET = 5  # distância mínima do centro para valores pequenos

    for equipe, color, direction in [
        ("Própria", CHART_TEAM_COLORS["propria"], -1),
        ("Terceirizada", CHART_TEAM_COLORS["terceirizada"], 1),
    ]:
        sub = comp[comp["equipe"] == equipe]
        texts, positions = [], []
        for p in sub["pct"]:
            if p >= MIN_INSIDE:
                texts.append(f"{p}%")
                positions.append("inside")
            else:
                texts.append("")
                positions.append("none")

        fig.add_trace(
            go.Bar(
                y=sub["tipo_desvio"],
                x=[direction * p for p in sub["pct"]],
                orientation="h",
                name=equipe,
                marker=dict(color=color, cornerradius=4),
                text=texts,
                textposition=positions,
                textfont=dict(color=COLORS["navy"], size=11),
                customdata=sub["pct"],
                hovertemplate=f"{equipe}: %{{customdata}}%<extra></extra>",
            )
        )

        for _, row in sub.iterrows():
            p = row["pct"]
            if p < MIN_INSIDE and p > 0:
                if direction < 0:
                    fig.add_annotation(
                        x=-MIN_OFFSET,
                        y=row["tipo_desvio"],
                        text=f"{p}%",
                        showarrow=False,
                        xanchor="right",
                        font=dict(color=COLORS["navy"], size=11),
                    )
                else:
                    fig.add_annotation(
                        x=MIN_OFFSET,
                        y=row["tipo_desvio"],
                        text=f"{p}%",
                        showarrow=False,
                        xanchor="left",
                        font=dict(color=COLORS["navy"], size=11),
                    )

    finalize_fig(
        fig,
        barmode="overlay",
        height=320,
        xaxis=_axis(
            tickvals=[-60, -40, -20, 0, 20, 40, 60],
            ticktext=["60%", "40%", "20%", "0", "20%", "40%", "60%"],
            zeroline=True,
            zerolinecolor=COLORS["navy"],
            zerolinewidth=2,
            range=[-65, 65],
        ),
        yaxis=_axis(categoryorder="array", categoryarray=list(reversed(tipos))),
        legend=dict(orientation="h", y=-0.15, font=dict(color=TEXT_COLOR, size=12)),
        margin=dict(l=20, r=20, t=20, b=40),
    )
    return fig


def chart_top_duplas(duplas: pd.DataFrame):
    colors = [_team_bar_color(t) for t in duplas["tipo"]]
    fig = go.Figure(
        go.Bar(
            x=duplas["dupla"],
            y=duplas["tois"],
            marker=dict(color=colors, cornerradius=4),
            text=duplas["tois"],
            textposition="outside",
            textfont=BAR_TEXT,
            hovertemplate="Dupla %{x}<br>%{y} TOIs<extra></extra>",
        )
    )
    finalize_fig(
        fig,
        height=360,
        xaxis=_axis(tickangle=-30),
        yaxis=_axis(title="TOIs com Desvio"),
    )
    return fig


def chart_stacked_profile(top_duplas_list: list, profile_df: pd.DataFrame):
    dev_types = [
        c for c in profile_df.columns if c != "dupla"
    ]
    fig = go.Figure()
    for dt in dev_types:
        fig.add_trace(
            go.Bar(
                name=dt,
                x=profile_df["dupla"],
                y=profile_df[dt],
                marker_color=DEVIATION_COLORS.get(dt, COLORS["light_blue"]),
            )
        )
    finalize_fig(
        fig,
        barmode="stack",
        height=360,
        xaxis=_axis(tickangle=-30),
        yaxis=_axis(title="Ocorrências"),
        legend=dict(orientation="h", y=-0.25, font=dict(color=TEXT_COLOR, size=11)),
    )
    return fig


def chart_individuals(ind: pd.DataFrame, n: int = 12):
    top = ind.head(n)
    colors = [_team_bar_color(t) for t in top["tipo"]]
    fig = go.Figure(
        go.Bar(
            x=top["matricula"],
            y=top["count"],
            marker=dict(color=colors, cornerradius=4),
            text=top["count"],
            textposition="outside",
            textfont=BAR_TEXT,
        )
    )
    finalize_fig(
        fig,
        height=360,
        xaxis=_axis(tickangle=-30),
        yaxis=_axis(title="Aparições"),
    )
    return fig


def chart_cities(cities: pd.DataFrame):
    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            name="Própria",
            x=cities["cidade"],
            y=cities["propria"],
            marker_color=CHART_TEAM_COLORS["propria"],
        )
    )
    fig.add_trace(
        go.Bar(
            name="Terceirizada",
            x=cities["cidade"],
            y=cities["terceirizada"],
            marker_color=CHART_TEAM_COLORS["terceirizada"],
        )
    )
    finalize_fig(
        fig,
        barmode="stack",
        height=380,
        xaxis=_axis(tickangle=-35),
        yaxis=_axis(title="TOIs com Desvio"),
        legend=dict(orientation="h", y=-0.3, font=dict(color=TEXT_COLOR, size=12)),
    )
    return fig


def render_rank_list(title: str, df: pd.DataFrame, color: str):
    if df.empty:
        st.markdown(f"**{title}** — sem dados")
        return
    max_val = df["count"].max()
    rows_html = ""
    for i, row in df.iterrows():
        pct = row["count"] / max_val * 100
        tipo_label = row["tipo"]
        rows_html += f"""
<div class="rank-row" style="display:flex;align-items:center;gap:10px;padding:8px 0;border-bottom:1px solid {COLORS['grey']};color:{COLORS['navy']};">
  <span style="font-weight:700;color:{COLORS['navy']};width:20px;">{i+1}</span>
  <span style="font-weight:600;width:80px;color:{COLORS['navy']};">{row['matricula']}</span>
  <span class="pill {'propria' if tipo_label=='Própria' else 'terceirizada'}" style="font-size:0.65rem;">{tipo_label}</span>
  <div style="flex:1;background:{COLORS['grey']};border-radius:4px;height:8px;">
    <div style="width:{pct}%;background:{color};border-radius:4px;height:8px;"></div>
  </div>
  <span style="font-weight:700;width:36px;text-align:right;color:{COLORS['navy']};">{row['count']}</span>
</div>"""
    st.markdown(
        f'<div class="chart-card" style="color:{COLORS["navy"]};">{_chart_title_row(title, INFO.get("table_duplas"))}{rows_html}</div>',
        unsafe_allow_html=True,
    )


def render_dupla_table(duplas: pd.DataFrame):
    rows = ""
    max_tois = duplas["tois"].max()
    for i, row in duplas.iterrows():
        tipo = row["tipo"].lower()
        bar_pct = row["tois"] / max_tois * 100
        bar_color = _team_bar_color(row["tipo"])
        pills = ""
        for dev, cnt in row["predominantes"]:
            pills += _deviation_pill(dev, cnt)

        m1, m2 = str(row["Matricula"]), str(row["Matricula_2"])
        rows += f"""<tr>
          <td {TD}>{i+1}</td>
          <td {TD}>{m1}</td>
          <td {TD}>{m2}</td>
          <td><span class="pill {tipo}">{row['tipo']}</span></td>
          <td {TD}><div style="display:flex;align-items:center;gap:8px;">
            <span style="font-weight:700;color:{COLORS['navy']};">{row['tois']}</span>
            <div style="width:80px;background:{COLORS['grey']};border-radius:3px;height:6px;">
              <div style="width:{bar_pct}%;background:{bar_color};height:6px;border-radius:3px;"></div>
            </div>
          </div></td>
          <td {TD}>{row['pct_total']}%</td>
          <td>{pills}</td>
        </tr>"""

    st.markdown(
        f"""<div class="chart-card" style="color:{COLORS['navy']};">
        {_chart_title_row(f"Tabela Completa — Top {len(duplas)} Duplas", INFO["table_duplas"])}
        <table class="data-table">
          <thead><tr>
            <th>#</th><th>Matrícula 1</th><th>Matrícula 2</th><th>Tipo</th>
            <th>TOIs</th><th>% do Total c/ Desvio</th><th>Desvios Predominantes</th>
          </tr></thead>
          <tbody>{rows}</tbody>
        </table></div>""",
        unsafe_allow_html=True,
    )


def render_city_table(cities: pd.DataFrame):
    rows = ""
    for _, row in cities.iterrows():
        pred_class = row["predominancia"].lower()
        pred_bg = _team_bar_color(row["predominancia"])
        rows += f"""<tr>
          <td {TD}>{row['cidade']}</td>
          <td {TD}><span style="background:{COLORS['light_blue']};color:{COLORS['navy']};padding:3px 10px;border-radius:12px;font-weight:600;">{row['propria']}</span></td>
          <td {TD}><span style="background:{COLORS['light_green']};color:{COLORS['navy']};padding:3px 10px;border-radius:12px;font-weight:600;">{row['terceirizada']}</span></td>
          <td {TD} style="color:{COLORS['navy']};font-weight:700;">{row['total']}</td>
          <td><span style="background:{pred_bg};color:{COLORS['navy']};padding:4px 12px;border-radius:12px;font-size:0.78rem;">
            {row['predominancia']} ({row['pred_pct']}%)</span></td>
        </tr>"""

    st.markdown(
        f"""<div class="chart-card" style="color:{COLORS['navy']};">
        {_chart_title_row("Tabela — Cidades: Própria vs Terceirizada", INFO["table_cidades"])}
        <table class="data-table">
          <thead><tr>
            <th>Cidade</th><th>Própria</th><th>Terceirizada</th><th>Total</th><th>Predominância</th>
          </tr></thead>
          <tbody>{rows}</tbody>
        </table></div>""",
        unsafe_allow_html=True,
    )


def _tipos_desvio_pills(text: str) -> str:
    if not text or text == "—":
        return "—"
    pills = ""
    for part in text.split("; "):
        if "(" not in part:
            continue
        name, _, rest = part.rpartition(" (")
        cnt = rest.rstrip(")")
        label = name.strip()
        pills += _deviation_pill(label, cnt)
    return pills or "—"


def _tendencia_badge(tendencia: str) -> str:
    styles = {
        "Melhorou": (COLORS["light_green"], COLORS["navy"]),
        "Piorou": ("#FDE8EA", COLORS["red"]),
        "Estável": (COLORS["light_blue"], COLORS["navy"]),
        "Poucos dados": ("#EEF0F3", COLORS["grey_text"]),
    }
    bg, fg = styles.get(tendencia, (COLORS["light_blue"], COLORS["navy"]))
    return (
        f'<span style="background:{bg};color:{fg};padding:3px 10px;border-radius:12px;'
        f'font-size:0.72rem;font-weight:600;white-space:nowrap;">{tendencia}</span>'
    )


def _influencia_badge(influencia: str) -> str:
    styles = {
        "Influencia": (COLORS["light_green"], COLORS["navy"]),
        "Influenciado": (COLORS["light_blue"], COLORS["navy"]),
        "Indeterminado": ("#EEF0F3", COLORS["grey_text"]),
    }
    bg, fg = styles.get(influencia, (COLORS["light_blue"], COLORS["navy"]))
    return (
        f'<span style="background:{bg};color:{fg};padding:3px 10px;border-radius:12px;'
        f'font-size:0.72rem;font-weight:600;white-space:nowrap;">{influencia}</span>'
    )


def _meses_resumo_html(text: str) -> str:
    if not text:
        return "—"
    chips = ""
    for part in text.split(" | "):
        chips += (
            f'<span style="background:{COLORS["bg"]};color:{COLORS["navy"]};'
            f'padding:2px 8px;border-radius:10px;font-size:0.68rem;margin:2px;'
            f'display:inline-block;font-weight:600;">{part}</span>'
        )
    return chips or "—"


def render_colaborador_analise(df: pd.DataFrame):
    st.markdown(
        _chart_card("Tabela Completa — Análise por Colaborador", INFO["table_colaborador"]),
        unsafe_allow_html=True,
    )
    if df.empty:
        st.info("Nenhum colaborador identificado na base.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    f1, f2 = st.columns([2, 1])
    with f1:
        busca = st.text_input(
            "Pesquisar matrícula",
            placeholder="Ex.: 6472, RT917914…",
            key="colab_analise_busca",
        )
    with f2:
        tendencia_f = st.selectbox(
            "Tendência",
            ["Todas", "Melhorou", "Piorou", "Estável", "Poucos dados"],
            key="colab_analise_tendencia",
        )

    out = df.copy()
    if busca.strip():
        q = busca.strip().lower()
        out = out[out["matricula"].str.lower().str.contains(q, na=False)]
    if tendencia_f != "Todas":
        out = out[out["tendencia"] == tendencia_f]

    st.caption(
        f"{len(out):,} colaborador(es) · "
        "Influencia = padrão de desvio independe do parceiro · "
        "Influenciado = tipos de desvio mudam conforme o parceiro"
    )

    if not out.empty:
        c_open1, c_open2, c_open3 = st.columns([2, 1, 1])
        matriculas = out["matricula"].astype(str).tolist()
        with c_open1:
            mat_sel = st.selectbox(
                "Ver TOIs do colaborador",
                matriculas,
                key="colab_analise_open_mat",
            )
        with c_open2:
            if st.button("Todos os TOIs", key="colab_open_all", use_container_width=True):
                go_detalhe("colaborador", matricula=mat_sel)
        with c_open3:
            if st.button("Só com desvio", key="colab_open_desvio", use_container_width=True):
                go_detalhe("colaborador_desvio", matricula=mat_sel)

    max_tois = int(out["total_tois"].max()) if not out.empty else 1
    rows = ""
    for i, (_, row) in enumerate(out.iterrows()):
        tipo = str(row["tipo"]).lower()
        bar_pct = row["total_tois"] / max_tois * 100 if max_tois else 0
        bar_color = _team_bar_color(row["tipo"])
        pct_txt = f"{row['pct_desvio']:.1f}".replace(".", ",")
        rows += f"""<tr>
          <td {TD}>{i + 1}</td>
          <td {TD}><span style="font-weight:700;color:{COLORS['navy']};">{row['matricula']}</span></td>
          <td><span class="pill {tipo}">{row['tipo']}</span></td>
          <td {TD}><div style="display:flex;align-items:center;gap:8px;">
            <span style="font-weight:700;color:{COLORS['navy']};">{row['total_tois']}</span>
            <div style="width:80px;background:{COLORS['grey']};border-radius:3px;height:6px;">
              <div style="width:{bar_pct}%;background:{bar_color};height:6px;border-radius:3px;"></div>
            </div>
          </div></td>
          <td {TD}><span style="font-weight:700;color:{COLORS['red']};">{pct_txt}%</span></td>
          <td {TD}><span style="font-weight:700;color:{COLORS['navy']};">{row['com_desvio']}</span></td>
          <td {TD}>{row['parceiros']}</td>
          <td>{_tendencia_badge(row['tendencia'])}</td>
          <td>{_influencia_badge(row['influencia'])}</td>
          <td>{_meses_resumo_html(row['tois_por_mes'])}</td>
          <td>{_tipos_desvio_pills(row['tipos_desvio'])}</td>
        </tr>"""

    st.markdown(
        f"""<div class="colab-table-wrap" style="margin-top:8px;">
        <table class="data-table">
          <thead><tr>
            <th>#</th><th>Matrícula</th><th>Tipo</th><th>Total TOIs</th>
            <th>% c/ desvio</th><th>TOIs c/ desvio</th><th>Parceiros</th>
            <th>Tendência</th><th>Influência</th><th>TOIs por mês</th><th>Desvios Predominantes</th>
          </tr></thead>
          <tbody>{rows}</tbody>
        </table></div>""",
        unsafe_allow_html=True,
    )

    export = out.rename(
        columns={
            "matricula": "Matrícula",
            "tipo": "Tipo",
            "total_tois": "Total TOIs",
            "com_desvio": "TOIs c/ desvio",
            "pct_desvio": "% c/ desvio",
            "parceiros": "Parceiros",
            "tendencia": "Tendência",
            "influencia": "Influência",
            "tois_por_mes": "TOIs por mês",
            "tipos_desvio": "Tipos de desvio",
        }
    )
    st.download_button(
        "Exportar análise CSV",
        export.to_csv(index=False).encode("utf-8-sig"),
        file_name="analise_colaboradores.csv",
        mime="text/csv",
        key="export_colaborador_analise",
    )
    st.markdown("</div>", unsafe_allow_html=True)


def render_person_cards(cards: list):
    cols = st.columns(len(cards))
    for col, card in zip(cols, cards):
        tipo_class = card["tipo"].lower()
        badge_class = "green" if card["insight"] == "Erro segue a PESSOA" else ""
        partners_html = ""
        for p in card["parceiros"]:
            partners_html += f"""
<div class="partner-row" style="color:{COLORS['navy']};">
  <span style="color:{COLORS['navy']};"><b style="color:{COLORS['navy']};">{p['parceiro']}</b>: {p['deviations']}</span>
  <div class="partner-total">{p['total']}</div>
</div>"""

        col.markdown(
            f"""<div class="person-card" style="color:{COLORS['navy']};">
              <div class="person-header {tipo_class}">{card['matricula']} • {card['tipo']}</div>
              <div class="person-body" style="color:{COLORS['navy']};">
                <div class="insight-badge {badge_class}">{card['insight']}</div>
                <div class="person-desc">{card['descricao']}</div>
                {partners_html}
              </div>
            </div>""",
            unsafe_allow_html=True,
        )


def _data_file_version() -> float:
    """Versão do arquivo — invalida cache quando a base é alterada."""
    if MONITORAMENTO_FILE.is_file():
        stat = MONITORAMENTO_FILE.stat()
        return stat.st_mtime + stat.st_size * 1e-9
    return 0.0


def _ensure_data_cache_fresh() -> None:
    """Limpa cache quando a versão do schema ou da base mudou."""
    key = (
        MONITORAMENTO_SCHEMA_VERSION,
        _data_file_version(),
    )
    if st.session_state.get("_data_cache_key") != key:
        get_monitoramento_data.clear()
        st.session_state["_data_cache_key"] = key


NAV_ITEMS = [
    ("go_dash", "Painel", "dashboard", "painel"),
    ("go_dados", "Base de dados", "dados", "dados"),
    ("go_cadastro", "Cadastro", "cadastro", "cadastro"),
    ("go_inconsistencias", "Inconsistências", "inconsistencias", "inconsistencias"),
]
NAV_SLUG_BY_PAGE = {
    "dashboard": "painel",
    "detalhe": "painel",
    "dados": "dados",
    "cadastro": "cadastro",
    "inconsistencias": "inconsistencias",
}
NAV_WIDTHS = {
    "dashboard": 1.0,
    "dados": 1.35,
    "cadastro": 1.0,
    "inconsistencias": 1.4,
}


def current_profile() -> dict:
    key = st.session_state.get("profile", "administrador")
    return ACCESS_PROFILES.get(key, ACCESS_PROFILES["administrador"])


def allowed_pages() -> list[str]:
    return current_profile().get("pages", ["dashboard"])


def profile_can_delete() -> bool:
    return bool(current_profile().get("can_delete", False))


def enforce_page_access() -> None:
    """Garante que o perfil só acesse páginas permitidas."""
    allowed = allowed_pages()
    current = st.session_state.get("app_page", "dashboard")
    effective = "dashboard" if current == "detalhe" else current
    if effective not in allowed:
        st.session_state.app_page = allowed[0]


def render_nav_bar() -> None:
    if "app_page" not in st.session_state:
        st.session_state.app_page = "dashboard"

    allowed = allowed_pages()
    nav_items = [item for item in NAV_ITEMS if item[2] in allowed]
    if not nav_items:
        nav_items = [NAV_ITEMS[0]]

    page = st.session_state.app_page
    active_slug = NAV_SLUG_BY_PAGE.get(page, "painel")

    with st.container(key="nav_menu_bar"):
        st.markdown(
            f'<span class="nav-page-flag nav-page-{active_slug}"></span>',
            unsafe_allow_html=True,
        )
        tabs_col, profile_col, logout_col = st.columns([7.6, 1.6, 0.8], gap="small")
        with tabs_col:
            with st.container(key="nav_tabs_track"):
                widths = [NAV_WIDTHS.get(item[2], 1.0) for item in nav_items]
                tab_cols = st.columns(widths, gap="small")
                for col, (key, label, page_id, _slug) in zip(tab_cols, nav_items):
                    with col:
                        if st.button(
                            label,
                            key=key,
                            use_container_width=True,
                            type="secondary",
                        ):
                            st.session_state.app_page = page_id
                            if page_id == "dashboard":
                                st.session_state.pop("detalhe_view", None)
                                st.session_state.pop("detalhe_filters", None)
                            st.rerun()
        with profile_col:
            st.markdown(
                f'<div class="nav-profile-badge">{current_profile()["label"]}</div>',
                unsafe_allow_html=True,
            )
        with logout_col:
            if st.button("Sair", key="logout", use_container_width=True, type="secondary"):
                st.session_state.clear()
                st.rerun()


def prepare_data_view(df: pd.DataFrame) -> pd.DataFrame:
    return export_base_view(df)


def resolve_detalhe_data(
    df: pd.DataFrame, view: str, filters: dict | None = None
) -> tuple[str, str, pd.DataFrame, bool]:
    """Retorna título, subtítulo, dados filtrados e se exibe coluna de desvio expandido."""
    filters = filters or {}
    df = ensure_monitoramento_schema(df)
    periodo = periodo_agendamento(df)

    if view == "medidores_ensaiados":
        return (
            "Medidores ensaiados",
            f"Todos os {len(df):,} ensaios registrados · {periodo}.",
            df,
            False,
        )
    if view == "tois_com_desvio":
        sub = filter_desvios_laboratorio(df, "com")
        pct = pct_tois_com_desvio(df)
        return (
            "TOIs com desvio",
            f"{len(sub):,} TOIs ({pct}% do total) com desvio apontado pelo laboratório.",
            sub,
            False,
        )
    if view == "tois_sem_desvio":
        sub = filter_desvios_laboratorio(df, "sem")
        return (
            "TOIs sem desvio",
            f"{len(sub):,} TOIs sem desvio do laboratório.",
            sub,
            False,
        )
    if view == "desvios_encontrados":
        sub = expand_desvios_ocorrencias(df)
        return (
            "Desvios encontrados",
            f"{len(sub):,} ocorrências de desvio (uma linha por desvio apontado).",
            sub,
            True,
        )
    if view == "desvio_tipo":
        tipo = filters.get("tipo", "")
        sub = filter_por_desvio_tipo(df, tipo)
        return (
            f"Desvio — {tipo}",
            f"{len(sub):,} TOIs com o desvio «{tipo}».",
            sub,
            False,
        )
    if view == "equipe":
        equipe = filters.get("equipe", "Própria")
        sub = filter_por_tipo_equipe(df, equipe)
        return (
            f"TOIs com desvio — equipe {equipe}",
            f"{len(sub):,} TOIs com desvio classificados como equipe {equipe}.",
            sub,
            False,
        )
    if view == "medidor_em_ordem":
        sub = filter_medidor_resultado(df, True)
        return (
            "Medidor em ordem",
            f"{len(sub):,} ensaios com medidor em ordem no teste visual.",
            sub,
            False,
        )
    if view == "medidor_irregular":
        sub = filter_medidor_resultado(df, False)
        return (
            "Medidor com irregularidade",
            f"{len(sub):,} ensaios com irregularidade no teste visual.",
            sub,
            False,
        )
    if view == "csd":
        csd = filters.get("csd", "")
        sub = filter_por_csd(df, csd)
        com = count_desvios_laboratorio(sub)
        return (
            f"CSD — {csd}",
            f"{len(sub):,} ensaios · {com:,} com desvio do laboratório.",
            sub,
            False,
        )
    if view == "csd_com_desvio":
        csd = filters.get("csd", "")
        sub = filter_desvios_laboratorio(filter_por_csd(df, csd), "com")
        return (
            f"CSD — {csd} (com desvio)",
            f"{len(sub):,} TOIs com desvio do laboratório neste CSD.",
            sub,
            False,
        )
    if view == "colaborador":
        mat = filters.get("matricula", "")
        sub = filter_por_matricula(df, mat)
        com = count_desvios_laboratorio(sub)
        return (
            f"Colaborador — matrícula {mat}",
            f"{len(sub):,} TOIs · {com:,} com desvio do laboratório.",
            sub,
            False,
        )
    if view == "colaborador_desvio":
        mat = filters.get("matricula", "")
        sub = filter_desvios_laboratorio(filter_por_matricula(df, mat), "com")
        return (
            f"Colaborador — matrícula {mat} (com desvio)",
            f"{len(sub):,} TOIs com desvio do laboratório.",
            sub,
            False,
        )

    return (
        "Detalhamento",
        f"{len(df):,} registros.",
        df,
        False,
    )


def page_detalhe(df: pd.DataFrame) -> None:
    view = st.session_state.get("detalhe_view", "medidores_ensaiados")
    filters = st.session_state.get("detalhe_filters", {})
    title, subtitle, filtered, show_desvio_col = resolve_detalhe_data(df, view, filters)

    c_back, c_title = st.columns([1, 5])
    with c_back:
        if st.button("← Voltar", key="detalhe_voltar", use_container_width=True):
            st.session_state.app_page = "dashboard"
            st.session_state.pop("detalhe_view", None)
            st.session_state.pop("detalhe_filters", None)
            st.rerun()
    with c_title:
        st.markdown(f"### {title}")

    st.caption(subtitle)

    f1, f2 = st.columns([2, 1])
    with f1:
        search = st.text_input(
            "Pesquisar nesta lista",
            placeholder="TOI, CSD, medidor, colaborador, desvio…",
            key=f"detalhe_search_{view}",
        )
    with f2:
        csd_opts = ["Todos"] + sorted(
            [c for c in filtered["csd"].dropna().unique().tolist() if c and c != "nan"]
        )
        csd_filter = st.selectbox("Filtrar CSD", csd_opts, key=f"detalhe_csd_{view}")

    if search.strip() or csd_filter != "Todos":
        filtered = filter_ficha(filtered, search, csd_filter)

    st.caption(f"{len(filtered):,} registro(s) nesta visualização")

    view_df = prepare_data_view(filtered)
    if show_desvio_col and "desvio_item" in filtered.columns:
        view_df = view_df.copy()
        view_df.insert(0, "Desvio (ocorrência)", filtered["desvio_item"].astype(str).values)

    st.dataframe(
        view_df,
        use_container_width=True,
        height=560,
        hide_index=True,
        column_config={
            "Analisador": st.column_config.TextColumn("Analisador", width="small"),
            "Desvios encontrados": st.column_config.TextColumn(
                "Desvios encontrados",
                width="large",
            ),
            "Desvio (ocorrência)": st.column_config.TextColumn(
                "Desvio (ocorrência)",
                width="medium",
            ),
        },
    )
    render_dash_footer()


def page_dados(df: pd.DataFrame) -> None:
    df = ensure_monitoramento_schema(df)
    f1, f2 = st.columns([2, 1])
    with f1:
        search = st.text_input(
            "Pesquisar",
            placeholder="TOI, CSD, analisador, desvios, colaborador…",
            key="dados_search",
        )
    with f2:
        csd_opts = ["Todos"] + sorted(
            [c for c in df["csd"].dropna().unique().tolist() if c and c != "nan"]
        )
        csd_filter = st.selectbox("CSD", csd_opts, key="dados_csd")

    filtered = filter_ficha(df, search, csd_filter)

    com_desvios = count_desvios_laboratorio(df)
    st.caption(
        f"{len(filtered):,} registro(s) encontrado(s) · base com {len(df):,} ensaios · "
        f"{com_desvios:,} com desvios do laboratório"
    )

    if df.empty:
        st.info("Nenhum dado na base. Importe um arquivo Excel para visualizar os registros.")
        render_dash_footer()
        return

    view_df = prepare_data_view(filtered)
    st.dataframe(
        view_df,
        use_container_width=True,
        height=560,
        hide_index=True,
        column_config={
            "Analisador": st.column_config.TextColumn("Analisador", width="small"),
            "Desvios encontrados": st.column_config.TextColumn(
                "Desvios encontrados",
                width="large",
            ),
        },
    )

    render_dash_footer()


def page_inconsistencias(df: pd.DataFrame) -> None:
    df = df.reset_index(drop=True)
    grupos = detect_inconsistencias(df)

    st.markdown("### Tratamento de inconsistências e divergências")

    if df.empty:
        st.info("Nenhum dado na base para analisar.")
        render_dash_footer()
        return

    total_grupos = len(grupos)
    total_registros = len({idx for g in grupos for idx in g["indices"]})
    dup_count = sum(1 for g in grupos if g["tipo"] == "Registro duplicado")
    missing_count = sum(1 for g in grupos if g["tipo"] == "Campo faltando")
    lab_count = sum(1 for g in grupos if g["tipo"] == "Divergência do laboratório")
    equipe_count = sum(1 for g in grupos if g["tipo"] == "Equipe divergente")

    st.markdown(
        f"""
<div class="kpi-row" style="grid-template-columns: repeat(5, 1fr) !important;">
  {_kpi_card_html(total_grupos, "Grupos de inconsistência", INFO["inconsist_grupos"], "navy")}
  {_kpi_card_html(lab_count, "Divergências lab.", INFO["inconsist_lab"])}
  {_kpi_card_html(equipe_count, "Equipe divergente", INFO["inconsist_equipe"], "navy", COLORS["green"])}
  {_kpi_card_html(dup_count, "Duplicidades", INFO["inconsist_dup"])}
  {_kpi_card_html(missing_count, "Campos faltando", INFO["inconsist_missing"])}
</div>
""",
        unsafe_allow_html=True,
    )

    if not grupos:
        st.success("Nenhuma inconsistência encontrada na base atual.")
        render_dash_footer()
        return

    tipo_filtro = st.selectbox(
        "Filtrar por tipo",
        [
            "Todos",
            "Divergência do laboratório",
            "Equipe divergente",
            "Registro duplicado",
            "Campo faltando",
        ],
        key="inconsistencias_tipo",
    )
    filtrados = grupos if tipo_filtro == "Todos" else [g for g in grupos if g["tipo"] == tipo_filtro]
    st.caption(f"{len(filtrados):,} grupo(s) de inconsistência")

    pill_map = {
        "Registro duplicado": "terceirizada",
        "Campo faltando": "mista",
        "Equipe divergente": "propria",
        "Divergência do laboratório": "mista",
    }

    for grupo in filtrados:
        tipo_cls = pill_map.get(grupo["tipo"], "mista")
        st.markdown(
            f"""<div class="chart-card" style="padding:14px 18px;margin-bottom:12px;">
            <div style="display:flex;align-items:center;gap:10px;margin-bottom:10px;">
              <span class="pill {tipo_cls}">{grupo['tipo']}</span>
              <span style="font-weight:600;color:{COLORS['navy']};">{grupo['descricao']}</span>
            </div></div>""",
            unsafe_allow_html=True,
        )

        st.dataframe(
            inconsistencia_record_view(df, grupo["indices"]),
            use_container_width=True,
            hide_index=True,
        )

        pode_excluir = profile_can_delete()
        indices = grupo["indices"]
        if grupo["tipo"] == "Registro duplicado" and len(indices) > 1:
            excluir = st.radio(
                "Selecione o registro para excluir (os demais serão mantidos):",
                options=indices,
                format_func=lambda i: inconsistencia_row_label(df, i),
                key=f"excluir_{grupo['id']}",
            )
            if not pode_excluir:
                st.info("Somente o perfil Administrador pode excluir registros.")
            elif st.button(
                "Excluir registro selecionado",
                key=f"btn_excluir_{grupo['id']}",
                type="primary",
            ):
                removidos = delete_monitoramento_rows([excluir])
                if removidos:
                    get_monitoramento_data.clear()
                    st.success(f"Registro da linha {excluir + 1} excluído com sucesso.")
                    st.rerun()
                else:
                    st.error("Não foi possível excluir o registro.")
        else:
            idx = indices[0]
            st.caption(inconsistencia_row_label(df, idx))
            if grupo["tipo"] in ("Campo faltando",):
                if not pode_excluir:
                    st.info("Somente o perfil Administrador pode excluir registros.")
                elif st.button(
                    "Excluir registro",
                    key=f"btn_excluir_{grupo['id']}",
                ):
                    removidos = delete_monitoramento_rows([idx])
                    if removidos:
                        get_monitoramento_data.clear()
                        st.success(f"Registro da linha {idx + 1} excluído com sucesso.")
                        st.rerun()
                    else:
                        st.error("Não foi possível excluir o registro.")
            elif grupo["tipo"] in ("Divergência do laboratório", "Equipe divergente"):
                st.info("Revise o apontamento do laboratório e corrija os dados na base ou na ficha de campo.")

        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    render_dash_footer()


def page_cadastro(df: pd.DataFrame) -> None:
    if df.empty:
        st.info("Nenhum dado na base. Importe os dados da ficha de monitoramento.")
        render_dash_footer()
        return

    resumo = colaboradores_resumo(df)
    csds = csds_resumo(df)

    total = len(resumo)
    proprios = int((resumo["tipo"] == "Própria").sum()) if not resumo.empty else 0
    terc = int((resumo["tipo"] == "Terceirizada").sum()) if not resumo.empty else 0
    total_csds = len(csds)

    st.markdown(
        f"""
<div class="kpi-row">
  {_kpi_card_html(total, "Colaboradores únicos", INFO["cadastro_kpi_total"], "navy")}
  {_kpi_card_html(proprios, "Equipe Própria", INFO["cadastro_kpi_propria"])}
  {_kpi_card_html(terc, "Terceirizada", INFO["cadastro_kpi_terceirizada"], "navy", COLORS["green"])}
  {_kpi_card_html(total_csds, "CSDs na base", INFO["cadastro_kpi_csds"])}
</div>
""",
        unsafe_allow_html=True,
    )

    if not resumo.empty:
        f1, f2 = st.columns([2, 1])
        with f1:
            busca = st.text_input(
                "Pesquisar colaborador",
                placeholder="Nome ou matrícula… ex.: João, 6636, RT917847",
                key="cadastro_search",
            )
        with f2:
            tipo_filtro = st.selectbox(
                "Tipo",
                ["Todos", "Própria", "Terceirizada"],
                key="cadastro_tipo",
            )

        filtrado = filter_colaboradores(resumo, busca, tipo_filtro)
        st.caption(f"{len(filtrado):,} colaborador(es) · {total:,} registros únicos na base")

        c_dl, _ = st.columns([1, 3])
        with c_dl:
            export = filtrado[["nome", "matricula", "tipo", "aparicoes", "csds"]].rename(
                columns={
                    "nome": "Nome",
                    "matricula": "Matrícula",
                    "tipo": "Tipo",
                    "aparicoes": "Aparições",
                    "csds": "CSDs",
                }
            )
            st.download_button(
                "Exportar colaboradores CSV",
                export.to_csv(index=False).encode("utf-8-sig"),
                file_name="cadastro_colaboradores.csv",
                mime="text/csv",
                use_container_width=True,
                key="export_colaboradores",
            )

        st.markdown(
            f'<div style="margin:8px 0 12px;">{_chart_title_row("Colaboradores", INFO["cadastro_colaboradores"])}</div>',
            unsafe_allow_html=True,
        )
        st.dataframe(
            filtrado[["nome", "matricula", "tipo", "aparicoes", "csds"]].rename(
                columns={
                    "nome": "Nome",
                    "matricula": "Matrícula",
                    "tipo": "Tipo",
                    "aparicoes": "Aparições",
                    "csds": "CSDs",
                }
            ),
            use_container_width=True,
            height=560,
            hide_index=True,
            key="cadastro_colaboradores_table",
        )
    else:
        st.info("Nenhum colaborador identificado na base.")

    if not csds.empty:
        st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
        busca_csd = st.text_input(
            "Pesquisar CSD",
            placeholder="Nome do CSD… ex.: Guarulhos, Mogi",
            key="cadastro_csd_search",
        )
        csds_filtrado = filter_csds(csds, busca_csd)
        st.caption(f"{len(csds_filtrado):,} CSD(s) · {total_csds:,} na base")

        c_dl2, _ = st.columns([1, 3])
        with c_dl2:
            export_csds = csds_filtrado.rename(
                columns={
                    "csd": "CSD",
                    "ensaios": "Ensaios",
                    "rotatividade_equipe": "Qnt. equipes diferentes",
                    "colaboradores": "Colaboradores",
                }
            )
            st.download_button(
                "Exportar CSDs CSV",
                export_csds.to_csv(index=False).encode("utf-8-sig"),
                file_name="cadastro_csds.csv",
                mime="text/csv",
                use_container_width=True,
                key="export_csds",
            )

        st.markdown(
            f'<div style="margin:8px 0 12px;">{_chart_title_row("CSDs", INFO["cadastro_csds"])}</div>',
            unsafe_allow_html=True,
        )
        st.dataframe(
            csds_filtrado.rename(
                columns={
                    "csd": "CSD",
                    "ensaios": "Ensaios",
                    "rotatividade_equipe": "Qnt. equipes diferentes",
                    "colaboradores": "Colaboradores",
                }
            ),
            use_container_width=True,
            height=420,
            hide_index=True,
            key="cadastro_csds_table",
        )
    else:
        st.info("Nenhum CSD identificado na base.")

    render_dash_footer()


def page_dashboard(data: dict) -> None:
    render_kpis(data["metrics"], data["df"])

    if data["df"].empty:
        st.warning(
            "A base está vazia. Coloque os dados em "
            "`data/qualidade_toi_base_tratada.xlsx` (aba *Ficha de monitoramento*) "
            "e reinicie o dashboard."
        )
        render_dash_footer()
        return

    st.markdown(_section(1, "overview", "Visão Geral — Ficha de Monitoramento"), unsafe_allow_html=True)
    equipe_desvios = desvios_por_tipo_equipe(data["df"])
    hc1, hc2 = st.columns([4, 1])
    with hc1:
        st.markdown(
            _chart_card(
                "TOIs com desvio — Própria vs Terceirizada",
                INFO["chart_tois_equipe"],
            ),
            unsafe_allow_html=True,
        )
    with hc2:
        ver_todos_button("tois_com_desvio", "ver_equipe_donut")
    if equipe_desvios["total"] > 0:
        st.plotly_chart(
            chart_desvios_equipe_donut(equipe_desvios),
            use_container_width=True,
        )
        equipe_items = [
            (f"{label} ({equipe_desvios[key]})", "equipe", {"equipe": label})
            for label, key in [
                ("Própria", "propria"),
                ("Terceirizada", "terceirizada"),
                ("Mista", "mista"),
                ("Sem equipe", "sem_equipe"),
            ]
            if equipe_desvios.get(key, 0) > 0
        ]
        render_detail_buttons(equipe_items, "equipe_det")
    else:
        st.info("Nenhum TOI com desvio do laboratório na base.")
    st.markdown("</div>", unsafe_allow_html=True)

    tois_com_desvio = count_desvios_laboratorio(data["df"])
    ranking_desvios = desvios_ranking(data["df"])
    if not ranking_desvios.empty:
        rc1, rc2 = st.columns([4, 1])
        with rc1:
            st.markdown(
                _chart_card(
                    f"Ranking completo — Ocorrências por tipo "
                    f"(sobre {tois_com_desvio:,} TOIs com desvio)",
                    INFO["chart_ranking_desvios"],
                ),
                unsafe_allow_html=True,
            )
        with rc2:
            ver_todos_button("desvios_encontrados", "ver_ranking_desvios")
        st.plotly_chart(
            chart_desvios_ranking(ranking_desvios, tois_com_desvio),
            use_container_width=True,
        )
        tipo_items = [
            (f'{row["tipo"]} ({int(row["count"])})', "desvio_tipo", {"tipo": row["tipo"]})
            for _, row in ranking_desvios.sort_values("count", ascending=False).iterrows()
        ]
        render_detail_buttons(tipo_items, "tipo_det")
        st.markdown("</div>", unsafe_allow_html=True)

    timeline_desvios = timeline_desvios_monthly(data["df"])
    timeline_equipes = timeline_desvios_por_equipe(data["df"])
    if (
        not timeline_desvios.empty
        and not timeline_equipes.empty
        and timeline_desvios["tois_com_desvio"].sum() > 0
    ):
        tc1, tc2 = st.columns([4, 1])
        with tc1:
            st.markdown(
                _chart_card(
                    "Evolução dos desvios por mês — data do agendamento",
                    INFO["chart_timeline_equipe"],
                ),
                unsafe_allow_html=True,
            )
        with tc2:
            ver_todos_button("tois_com_desvio", "ver_timeline_equipe")
        st.markdown('<div class="timeline-chart-wrap">', unsafe_allow_html=True)
        st.plotly_chart(
            chart_timeline_desvios(timeline_equipes, timeline_desvios),
            use_container_width=False,
        )
        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    timeline_pessoas = timeline_desvios_por_pessoa(data["df"])
    if (
        not timeline_desvios.empty
        and not timeline_pessoas.empty
        and timeline_desvios["tois_com_desvio"].sum() > 0
    ):
        pc1, pc2 = st.columns([4, 1])
        with pc1:
            st.markdown(
                _chart_card(
                    "Evolução dos desvios por mês — por colaborador",
                    INFO["chart_timeline_pessoa"],
                ),
                unsafe_allow_html=True,
            )
        with pc2:
            ver_todos_button("tois_com_desvio", "ver_timeline_pessoa")
        st.markdown('<div class="timeline-chart-wrap">', unsafe_allow_html=True)
        st.plotly_chart(
            chart_timeline_desvios(
                timeline_pessoas,
                timeline_desvios,
                entity_col="pessoa",
                outras_label="Outras pessoas",
                label_lines=_pessoa_label_lines,
            ),
            use_container_width=False,
        )
        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    analise_colab = colaborador_analise(data["df"])
    render_colaborador_analise(analise_colab)

    st.markdown(_section(2, "cities", "Análise por CSD"), unsafe_allow_html=True)
    csd_resumo = csd_breakdown(data["df"])
    cc1, cc2 = st.columns([4, 1])
    with cc1:
        st.markdown(
            _chart_card(
                "% de desvio por CSD — sobre TOIs ensaiados",
                INFO["chart_csd_pct"],
            ),
            unsafe_allow_html=True,
        )
    with cc2:
        ver_todos_button("medidores_ensaiados", "ver_csd_chart")
    if csd_resumo.empty:
        st.info("Nenhum CSD com ensaios na base.")
    else:
        st.plotly_chart(chart_csd_desvio_pct(csd_resumo), use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

    if not csd_resumo.empty:
        csd_items = []
        for _, row in csd_resumo.iterrows():
            csd_items.append((str(row["csd"]), "csd", {"csd": row["csd"]}))
            csd_items.append(
                (
                    f'{row["csd"]} — com desvio ({row["com_desvio"]})',
                    "csd_com_desvio",
                    {"csd": row["csd"]},
                )
            )
        st.markdown(
            '<p class="detail-links" style="margin-top:8px;">Abrir detalhes por CSD:</p>',
            unsafe_allow_html=True,
        )
        render_detail_buttons(csd_items, "csd_det")

    csd_rows = ""
    for _, row in csd_resumo.iterrows():
        pct = f"{row['pct_desvio']:.1f}".replace(".", ",")
        csd_rows += f"""<tr>
      <td {TD}>{row['csd']}</td>
      <td {TD}>{row['total']}</td>
      <td {TD}>{row['com_desvio']}</td>
      <td {TD}>{pct}%</td>
    </tr>"""
    st.markdown(
        f"""<div class="chart-card">{_chart_title_row("Tabela — Resumo por CSD", INFO["table_csd_resumo"])}
    <table class="data-table"><thead><tr>
      <th>CSD</th><th>TOIs ensaiados</th><th>Com desvio</th><th>% Desvio</th>
    </tr></thead><tbody>{csd_rows}</tbody></table></div>""",
        unsafe_allow_html=True,
    )

    render_dash_footer()


# ── Main ─────────────────────────────────────────────────────────────────────
if not check_password():
    st.stop()


@st.cache_data
def get_monitoramento_data(_file_version: float, _schema_version: int):
    df = load_monitoramento()
    return {
        "df": df,
        "metrics": kpi_monitoramento(df),
        "laudo": laudo_summary(df),
        "medidor": medidor_summary(df),
        "ranking": irregularidade_ranking(df, 12),
        "csd": csd_breakdown(df),
        "inspetor_issues": inspetor_issues_ranking(df),
        "colaboradores": colaboradores_resumo(df),
    }


_ensure_data_cache_fresh()
data = get_monitoramento_data(_data_file_version(), MONITORAMENTO_SCHEMA_VERSION)

handle_drill_query()
enforce_page_access()
render_nav_bar()
if st.session_state.get("app_page", "dashboard") not in (
    "dados",
    "cadastro",
    "inconsistencias",
    "detalhe",
):
    render_dash_header()

if st.session_state.get("app_page", "dashboard") == "dados":
    page_dados(data["df"])
elif st.session_state.get("app_page") == "inconsistencias":
    page_inconsistencias(data["df"])
elif st.session_state.get("app_page") == "cadastro":
    page_cadastro(data["df"])
elif st.session_state.get("app_page") == "detalhe":
    page_detalhe(data["df"])
else:
    page_dashboard(data)
