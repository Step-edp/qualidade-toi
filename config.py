"""Configurações do dashboard Qualidade de TOI — EDP SP."""

import os
from pathlib import Path

BASE_DIR = Path(__file__).parent
DATA_FILE = BASE_DIR / "data" / "base_unificada_dedup_toi.xlsx"
MONITORAMENTO_FILE = BASE_DIR / "data" / "qualidade_toi_base_tratada.xlsx"
APONTAMENTOS_LAB_FILE = BASE_DIR / "data" / "apontamentos_laboratorio.xlsx"
MONITORAMENTO_SHEET = "Ficha de monitoramento"
# Incrementar quando colunas/campos internos da base mudarem (invalida cache Streamlit)
MONITORAMENTO_SCHEMA_VERSION = 12

# Colunas oficiais da Ficha de Monitoramento (estrutura da base tratada)
MONITORAMENTO_COLUMNS = [
    "Data do agendamento",
    "Status",
    "CSD",
    "Instalação",
    "Medidor",
    "TOI",
    "Observações de Irregulariedade",
    "Data de ensaio",
    "Nota",
    "Laudo de campo está correto?",
    "Descrição da irregularidade em campo",
    "Colaborador_1",
    "Matricula_1",
    "Colaborador_2",
    "Matricula_2",
    "Sinalização",
    "Analisador",
    "Desvios encontrados",
]

# Colunas ocultas na página Base de dados (permanecem no Excel interno)
MONITORAMENTO_VIEW_EXCLUDE = {
    "Status",
    "Laudo de campo está correto?",
    "Descrição da irregularidade em campo",
}

MONITORAMENTO_VIEW_EXCLUDE_FIELDS = {
    "status",
    "laudo_raw",
    "irregularidade_raw",
}

# Ordem de exibição na Base de dados (Analisador e Desvios visíveis após TOI)
MONITORAMENTO_VIEW_COLUMN_ORDER = [
    "Data do agendamento",
    "CSD",
    "Instalação",
    "Medidor",
    "TOI",
    "Analisador",
    "Desvios encontrados",
    "Observações de Irregulariedade",
    "Data de ensaio",
    "Nota",
    "Colaborador_1",
    "Matricula_1",
    "Tipo_1",
    "Colaborador_2",
    "Matricula_2",
    "Tipo_2",
    "Sinalização",
]

# Campos obrigatórios para validação de inconsistências
MONITORAMENTO_REQUIRED_FIELDS = {
    "data_disp": "Data do agendamento",
    "csd": "CSD",
    "instalacao": "Instalação",
    "medidor": "Medidor",
    "toi": "TOI",
}

# Campos usados para detectar registros duplicados
MONITORAMENTO_DUPLICATE_FIELDS = {
    "toi": "TOI",
    "medidor": "Medidor",
}

# Mapeamento coluna Excel → campo interno
MONITORAMENTO_FIELD_MAP = {
    "data_disp": "Data do agendamento",
    "status": "Status",
    "csd": "CSD",
    "instalacao": "Instalação",
    "medidor": "Medidor",
    "toi": "TOI",
    "mes_inicio": "Observações de Irregulariedade",
    "data_ensaio": "Data de ensaio",
    "nota": "Nota",
    "laudo_raw": "Laudo de campo está correto?",
    "irregularidade_raw": "Descrição da irregularidade em campo",
    "colaborador_1": "Colaborador_1",
    "matricula_1": "Matricula_1",
    "colaborador_2": "Colaborador_2",
    "matricula_2": "Matricula_2",
    "sinalizacao": "Sinalização",
    "analisador": "Analisador",
    "desvios_encontrados": "Desvios encontrados",
}

# Desvios observados pelo laboratório (lista oficial)
LAB_DESVIOS_CANONICOS = [
    "Sem número de invólucro",
    "Faltando lacre da tampa",
    "Sem número de medidor encontrado",
    "Sem lacre no TOI, mas com lacre fisicamente",
    "Com lacre no TOI, porém sem lacre fisicamente",
    "Lacre violado no TOI porém em ordem fisicamente",
    "TOI não enviado fisicamente",
    "CSM cortado (sem nome de equipe)",
    "Sem dispositivo no TOI, porém com dispositivo e sem lacre",
    "Nenhum documento enviado",
    "CSM não enviado fisicamente",
    "CSM incompleto",
    "TOI e CSM não enviados fisicamente",
    "Faltando lacre da tampa (equipe colocou sem lacre)",
    "Faltando lacre da tampa (equipe colocou apenas um)",
    "TOI ilegível",
    "Informações divergentes",
    "Número do invólucro errado",
    "Equipe divergente",
]

# Rótulos curtos para ranking de desvios no painel
DESVIO_DISPLAY_LABELS = {
    "Sem número de invólucro": "Sem nº Invólucro",
    "Número do invólucro errado": "Nº invólucro errado",
    "Faltando lacre da tampa": "Faltando lacre tampa",
    "Faltando lacre da tampa (equipe colocou sem lacre)": "Faltando lacre tampa",
    "Faltando lacre da tampa (equipe colocou apenas um)": "Faltando lacre tampa",
    "Sem número de medidor encontrado": "Sem nº medidor",
    "Sem lacre no TOI, mas com lacre fisicamente": "Sem lacre TOI/físico",
    "Com lacre no TOI, porém sem lacre fisicamente": "Com lacre TOI/s/físico",
    "Lacre violado no TOI porém em ordem fisicamente": "Lacre violado TOI",
    "TOI não enviado fisicamente": "TOI não enviado",
    "CSM cortado (sem nome de equipe)": "CSM cortado",
    "Sem dispositivo no TOI, porém com dispositivo e sem lacre": "Sem dispositivo TOI",
    "Nenhum documento enviado": "Nenhum doc enviado",
    "CSM não enviado fisicamente": "CSM não enviado",
    "TOI ilegível": "TOI ilegível",
    "Informações divergentes": "Informações divergentes",
    "Equipe divergente": "Equipe divergente",
}

# Desvios excluídos do ranking do painel (tratados em inconsistências)
DESVIOS_RANKING_EXCLUDE = {
    "Equipe divergente",
}

LOGO_DIR = BASE_DIR / "assets" / "logo"

# Nomes sugeridos para o arquivo da logo (também aceita qualquer .png/.svg/.jpg na pasta)
LOGO_FILENAMES = (
    "edp_logo.svg",
    "Logo edp png azul.png",
    "edp_logo.png",
    "logo.png",
    "logo.svg",
    "edp.png",
)

# Identidade visual EDP SP — alinhada ao Laudo de Perícia
COLORS = {
    "navy": "#0D2840",
    "navy_light": "#1A3D5C",
    "green": "#00A651",
    "green_dark": "#008C44",
    "cyan": "#00A9CE",
    "light_blue": "#B8D9EC",
    "light_green": "#A8E6C3",
    "grey": "#F0F2F5",
    "border": "#D4D9E1",
    "grey_text": "#4A5568",
    "text": "#2D3748",
    "white": "#FFFFFF",
    "bg": "#F7F8FA",
    "mista": "#8B95A5",
    "red": "#D0021B",
}

# Paleta média para gráficos — mais saturada, texto navy legível
CHART_PALETTE = [
    "#7EB8DA",
    "#7FD4A0",
    "#6EC4DC",
    "#B19CD9",
    "#9BAFD4",
    "#6BC4B8",
    "#F5C87A",
    "#F0A0A8",
    "#90D8B0",
    "#8ECAE6",
    "#85C998",
    "#A8B8C8",
    "#C4A8E0",
    "#78B4D4",
    "#E8C088",
    "#88AED4",
    "#C8A8D8",
    "#78C8B8",
    "#D8A8C8",
    "#98B8D0",
]

CHART_TEAM_COLORS = {
    "propria": "#7EB8DA",
    "terceirizada": "#7FD4A0",
    "mista": "#A8B8C8",
    "sem_equipe": "#B8C4D0",
    "com_desvio": "#F0A0A8",
    "sem_desvio": "#7FD4A0",
    "laudo_sim": "#7FD4A0",
    "laudo_nao": "#F0A0A8",
    "laudo_pendente": "#A8B8C8",
    "medidor_ordem": "#7FD4A0",
    "medidor_irregular": "#7EB8DA",
}

# Cores médias para desvios (pills e gráficos)
DEVIATION_PILL_COLORS = {
    "CSM cortado": "#8CB4D9",
    "TOI não enviado": "#90D8B0",
    "Sem nº Invólucro": "#7EB8DA",
    "Faltando lacre tampa": "#7FD4A0",
    "CSM não enviado": "#85C998",
    "Sem lacre TOI/físico": "#B8C4D0",
    "Nenhum doc enviado": "#C4A8E0",
    "Sem nº medidor": "#F5C87A",
    "Sem info lacres": "#B8C4D0",
    "Com lacre TOI/s/físico": "#9BAFD4",
    "Lacre violado TOI": "#F0A0A8",
    "Sem dispositivo TOI": "#6BC4B8",
    "Nº invólucro errado": "#8ECAE6",
    "TOI ilegível": "#A8B8C8",
    "Informações divergentes": "#C8A8D8",
    "Equipe divergente": "#B8C4D0",
}

DEVIATION_COLORS = DEVIATION_PILL_COLORS

IRREGULARIDADE_COLORS = {
    "Medidor reprovado no teste visual": "#8CB4D9",
    "Mancal fora de posição": "#7EB8DA",
    "Medidor em ordem": "#7FD4A0",
    "Bobina de potencial interrompida": "#9BAFD4",
    "Medidor reprovado dielétrico": "#8ECAE6",
    "Medidor não liga": "#90D8B0",
    "Sem carga de parâmetros": "#A8B8C8",
    "Sujeira interna": "#B8C4D0",
    "Display apagado": "#C4A8E0",
    "Não informado": "#B8C4D0",
}

# Senha de acesso — altere aqui ou defina a variável de ambiente DASHBOARD_PASSWORD
DASHBOARD_PASSWORD = os.environ.get("DASHBOARD_PASSWORD", "edp2026")
