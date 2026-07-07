"""Processamento da Ficha de Monitoramento — Qualidade do TOI."""

from __future__ import annotations

import ast
import re
import sys
from collections import Counter, defaultdict
from collections.abc import Sequence
from pathlib import Path

import pandas as pd

from config import (
    APONTAMENTOS_LAB_FILE,
    DESVIO_DISPLAY_LABELS,
    DESVIOS_RANKING_EXCLUDE,
    LAB_DESVIOS_CANONICOS,
    MONITORAMENTO_COLUMNS,
    MONITORAMENTO_DUPLICATE_FIELDS,
    MONITORAMENTO_FIELD_MAP,
    MONITORAMENTO_FILE,
    MONITORAMENTO_REQUIRED_FIELDS,
    MONITORAMENTO_SHEET,
    MONITORAMENTO_VIEW_EXCLUDE,
    MONITORAMENTO_VIEW_EXCLUDE_FIELDS,
    MONITORAMENTO_VIEW_COLUMN_ORDER,
)

IRREGULARIDADE_ALIASES = {
    "REPROVADO NO TESTE VISUAL": "Medidor reprovado no teste visual",
    "MEDIDOR REPROVADO NO TESTE VISUAL": "Medidor reprovado no teste visual",
    "MEDIDOR REPROVADO NO VISUAL": "Medidor reprovado no teste visual",
    "MEDIDOR REPROVADO NO TESTE VISUAL.": "Medidor reprovado no teste visual",
    "MANCAL FORA DE POSIÇÃO": "Mancal fora de posição",
    "MANCAL FORA DE POSIO": "Mancal fora de posição",
    "MEDIDOR EM ORDEM": "Medidor em ordem",
    "DENTRO DA CLASSE": "Medidor em ordem",
    "MEDIDOR COM BOBINA DE POTENCIAL INTERROMPIDA": "Bobina de potencial interrompida",
    "MEDIDOR REPROVADO DIELETRICO": "Medidor reprovado dielétrico",
    "MEDIDOR NÃO LIGA": "Medidor não liga",
    "MEDIDOR NAO LIGA": "Medidor não liga",
    "MEDIDOR SEM CARGA DE PARAMETROS": "Sem carga de parâmetros",
    "MEDIDOR COM SUJEIRA INTERNA": "Sujeira interna",
    "MEDIDOR COM DISPLAY APAGADO": "Display apagado",
    "MEDIDOR COM BLOCO DE TERMINAIS DANIFICADO": "Bloco de terminais danificado",
    "MEDIDOR COM BAIXA INTENSIDADE LUMINOSA NO DISPLAY": "Baixa intensidade no display",
    "MEDIDOR COM ELEMENTO FRENADOR DESMAGNETIZADO": "Elemento frenador desmagnetizado",
    "MEDIDOR COM HARDWARE ALTERADO": "Hardware alterado",
}

# Compatibilidade com layout antigo da ficha
LEGACY_COLUMN_ALIASES: dict[str, list[str]] = {
    "Data do agendamento": [
        "Data do agendamento",
        "Data disponível",
        "Data disponivel",
    ],
    "Descrição da irregularidade em campo": [
        "Descrição da irregularidade em campo",
        "Descrição da irregularidade em  campo",
        "Descrição Irregularidade",
        "Descricao Irregularidade",
    ],
    "Observações de Irregulariedade": [
        "Observações de Irregulariedade",
        "Observacoes de Irregulariedade",
        "Observações de Irregularidade",
    ],
    "Sinalização": ["Sinalização", "Sinalizacao"],
    "Laudo de campo está correto?": [
        "Laudo de campo está correto?",
        "Laudo de campo está correto? ",
        "Laudo de campo esta correto?",
    ],
    "Inspeção de campo realizada por": [
        "Inspeção de campo realizada por:",
        "Inspecao de campo realizada por:",
    ],
}

INSPETOR_ISSUE_PATTERNS: list[tuple[str, str]] = [
    ("Sem nº invólucro", r"sem o n[uú]mero do inv[oó]lucro|sem n[uú]mero.*inv[oó]lucro"),
    ("CSM cortado", r"csm cortado"),
    ("CSM incompleto", r"csm incompleto"),
    ("Documentação incompleta", r"documenta[cç][aã]o incompleta"),
    ("Dados da equipe ausentes", r"sem os dados da equipe|dados da equipe"),
]

LAB_DESVIO_PATTERNS: list[tuple[str, str]] = [
    ("Sem número de invólucro", r"sem n[uú]mero de inv[oó]lucro|sem n[uú]mero inv[oó]lucro"),
    ("Número do invólucro errado", r"n[uú]mero do inv[oó]lucro errado|inv[oó]lucro errado"),
    (
        "Faltando lacre da tampa (equipe colocou apenas um)",
        r"faltando lacre da tampa \(equipe colocou apenas um\)",
    ),
    (
        "Faltando lacre da tampa (equipe colocou sem lacre)",
        r"faltando lacre da tampa \(equipe colocou sem lacre\)",
    ),
    ("Faltando lacre da tampa", r"faltando lacre da tampa|sem lacre da tampa"),
    ("Sem número de medidor encontrado", r"sem n[uú]mero de medidor|sem n[uú]mero medidor"),
    (
        "Sem lacre no TOI, mas com lacre fisicamente",
        r"sem lacre no toi.*com lacre fisicamente",
    ),
    (
        "Com lacre no TOI, porém sem lacre fisicamente",
        r"com lacre no toi.*sem lacre fisicamente",
    ),
    (
        "Lacre violado no TOI porém em ordem fisicamente",
        r"lacre violado no toi",
    ),
    ("TOI não enviado fisicamente", r"toi n[aã]o enviado fisicamente|toi n[aã]o enviado"),
    ("CSM cortado (sem nome de equipe)", r"csm cortado"),
    (
        "Sem dispositivo no TOI, porém com dispositivo e sem lacre",
        r"sem dispositivo no toi",
    ),
    ("Nenhum documento enviado", r"nenhum documento enviado|nenhum doc"),
    ("CSM não enviado fisicamente", r"csm n[aã]o enviado fisicamente|csm n[aã]o enviado"),
    ("CSM incompleto", r"csm incompleto"),
    (
        "TOI e CSM não enviados fisicamente",
        r"toi\s*&\s*csm n[aã]o enviados fisicamente|toi e csm n[aã]o enviados",
    ),
    ("TOI ilegível", r"toi ileg[ií]vel"),
    ("Informações divergentes", r"informa[cç][oõ]es divergentes"),
    ("Equipe divergente", r"equipe divergente"),
]


def create_empty_base(path: Path | None = None) -> Path:
    """Cria arquivo Excel vazio com a estrutura oficial de colunas."""
    file_path = path or MONITORAMENTO_FILE
    file_path.parent.mkdir(parents=True, exist_ok=True)
    empty = pd.DataFrame(columns=MONITORAMENTO_COLUMNS)
    with pd.ExcelWriter(file_path, engine="openpyxl") as writer:
        empty.to_excel(writer, sheet_name=MONITORAMENTO_SHEET, index=False)
        pd.DataFrame().to_excel(writer, sheet_name="Planilha1", index=False)
    return file_path


def _normalize_header(name: str) -> str:
    return re.sub(r"\s+", " ", str(name).strip().lower())


def _resolve_column(raw: pd.DataFrame, target: str) -> str | None:
    if target in raw.columns:
        return target
    aliases = LEGACY_COLUMN_ALIASES.get(target, [target])
    norm_map = {_normalize_header(c): c for c in raw.columns}
    for alias in aliases:
        key = _normalize_header(alias)
        if key in norm_map:
            return norm_map[key]
    target_norm = _normalize_header(target)
    for norm, original in norm_map.items():
        if target_norm in norm or norm in target_norm:
            return original
    return None


def _read_raw(path: Path) -> pd.DataFrame:
    if not path.is_file():
        create_empty_base(path)
    raw = pd.read_excel(path, sheet_name=MONITORAMENTO_SHEET)
    raw.columns = [str(c).strip() for c in raw.columns]
    return raw


def import_from_excel(
    source: str | Path,
    dest: str | Path | None = None,
    sheet_name: str | int | None = 0,
) -> int:
    """Importa planilha externa para a base oficial do dashboard."""
    source_path = Path(source)
    dest_path = Path(dest) if dest else MONITORAMENTO_FILE
    raw = pd.read_excel(source_path, sheet_name=sheet_name)
    raw.columns = [str(c).strip() for c in raw.columns]

    out = pd.DataFrame()
    for col in MONITORAMENTO_COLUMNS:
        resolved = _resolve_column(raw, col)
        out[col] = raw[resolved] if resolved else pd.NA

    dest_path.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(dest_path, engine="openpyxl") as writer:
        out.to_excel(writer, sheet_name=MONITORAMENTO_SHEET, index=False)
        pd.DataFrame().to_excel(writer, sheet_name="Planilha1", index=False)
    return len(out)


def _build_inspetor_text(row: pd.Series) -> str:
    parts = []
    for field in (
        "colaborador_1",
        "matricula_1",
        "colaborador_2",
        "matricula_2",
        "sinalizacao",
        "nota",
        "mes_inicio",
    ):
        val = row.get(field)
        if pd.notna(val) and str(val).strip():
            parts.append(str(val).strip())
    return " · ".join(parts)


def normalize_irregularidade(text: object) -> str:
    if pd.isna(text) or not str(text).strip():
        return "Não informado"
    key = str(text).strip().upper().rstrip(".")
    if key in IRREGULARIDADE_ALIASES:
        return IRREGULARIDADE_ALIASES[key]
    return str(text).strip().title()


def normalize_laudo(value: object) -> str:
    if pd.isna(value):
        return "Pendente"
    v = str(value).strip().lower()
    if v in ("sim", "s", "yes"):
        return "Sim"
    if v in ("não", "nao", "n", "no"):
        return "Não"
    return "Pendente"


def is_medidor_ordem(irregularidade: str) -> bool:
    low = irregularidade.lower()
    return "em ordem" in low or "dentro da classe" in low


def extract_inspetor_issues(text: object) -> list[str]:
    if pd.isna(text):
        return []
    found: list[str] = []
    raw = str(text)
    for name, pattern in INSPETOR_ISSUE_PATTERNS:
        if re.search(pattern, raw, re.I):
            found.append(name)
    return found


def ensure_monitoramento_schema(df: pd.DataFrame) -> pd.DataFrame:
    """Garante colunas internas esperadas (ex.: após cache antigo ou Excel legado)."""
    out = df.copy()
    for internal in MONITORAMENTO_FIELD_MAP:
        if internal not in out.columns:
            out[internal] = pd.NA
    for col in ("irregularidade", "laudo", "medidor_ordem", "inspetor", "inspetor_issues", "mes"):
        if col not in out.columns:
            out[col] = pd.NA
    return out


def load_monitoramento(path: str | None = None) -> pd.DataFrame:
    file_path = Path(path) if path else MONITORAMENTO_FILE
    raw = _read_raw(file_path)

    df = pd.DataFrame()
    for internal, excel_col in MONITORAMENTO_FIELD_MAP.items():
        resolved = _resolve_column(raw, excel_col)
        if resolved:
            df[internal] = raw[resolved]
        else:
            df[internal] = pd.NA

    # Layout legado: inspeção de campo em coluna única
    legacy_insp = _resolve_column(raw, "Inspeção de campo realizada por")
    if legacy_insp and df["colaborador_1"].isna().all():
        df["sinalizacao"] = raw[legacy_insp]

    df["data_disp"] = pd.to_datetime(df["data_disp"], errors="coerce")
    df["csd"] = df["csd"].astype(str).str.strip().replace("nan", pd.NA)
    df["irregularidade"] = df["irregularidade_raw"].apply(normalize_irregularidade)
    df["laudo"] = df["laudo_raw"].apply(normalize_laudo)
    df["medidor_ordem"] = df["irregularidade"].apply(is_medidor_ordem)
    df["inspetor"] = df.apply(_build_inspetor_text, axis=1)
    df["inspetor_issues"] = df["inspetor"].apply(extract_inspetor_issues)
    df["mes"] = df["data_disp"].dt.to_period("M").astype(str)
    return ensure_monitoramento_schema(df)


def export_base_view(df: pd.DataFrame) -> pd.DataFrame:
    """Retorna DataFrame com colunas oficiais para exibição/exportação."""
    view_columns = [c for c in MONITORAMENTO_VIEW_COLUMN_ORDER if c not in MONITORAMENTO_VIEW_EXCLUDE]
    rows = []
    for _, row in df.iterrows():
        item = {}
        for internal, label in MONITORAMENTO_FIELD_MAP.items():
            if internal in MONITORAMENTO_VIEW_EXCLUDE_FIELDS:
                continue
            val = row.get(internal, pd.NA)
            if internal == "data_disp" and pd.notna(val):
                item[label] = val.strftime("%d/%m/%Y %H:%M")
            elif internal in ("analisador", "desvios_encontrados"):
                item[label] = "" if _is_blank(val) else str(val).strip()
            else:
                item[label] = val if pd.notna(val) else ""
        item["Tipo_1"] = _tipo_colaborador_from_value(row.get("matricula_1"))
        item["Tipo_2"] = _tipo_colaborador_from_value(row.get("matricula_2"))
        rows.append(item)
    out = pd.DataFrame(rows, columns=view_columns)
    return out[view_columns]


def has_desvios_laboratorio(value: object) -> bool:
    return bool(parse_desvios_encontrados(value))


def count_desvios_laboratorio(df: pd.DataFrame) -> int:
    df = ensure_monitoramento_schema(df)
    if df.empty:
        return 0
    return int(df["desvios_encontrados"].apply(has_desvios_laboratorio).sum())


def count_total_desvios_encontrados(df: pd.DataFrame) -> int:
    """Total de desvios apontados (cada ocorrência em Desvios encontrados)."""
    df = ensure_monitoramento_schema(df)
    if df.empty:
        return 0
    return int(
        df["desvios_encontrados"]
        .apply(lambda v: len(parse_desvios_encontrados(v)))
        .sum()
    )


def _tipo_equipe_registro(row: pd.Series) -> str:
    """Classifica a dupla do registro: Própria, Terceirizada ou Mista."""
    m1 = _normalize_matricula(row.get("matricula_1"))
    m2 = _normalize_matricula(row.get("matricula_2"))
    t1 = bool(m1) and m1.upper().startswith("RT")
    t2 = bool(m2) and m2.upper().startswith("RT")
    if m1 and m2:
        if t1 and t2:
            return "Terceirizada"
        if not t1 and not t2:
            return "Própria"
        return "Mista"
    if m1:
        return "Terceirizada" if t1 else "Própria"
    if m2:
        return "Terceirizada" if t2 else "Própria"
    return ""


def desvios_por_tipo_equipe(df: pd.DataFrame) -> dict:
    """TOIs com desvio do laboratório, agrupados por tipo de equipe."""
    data = ensure_monitoramento_schema(df)
    sub = data[data["desvios_encontrados"].apply(has_desvios_laboratorio)]
    propria = terceirizada = mista = sem_equipe = 0
    for _, row in sub.iterrows():
        tipo = _tipo_equipe_registro(row)
        if tipo == "Própria":
            propria += 1
        elif tipo == "Terceirizada":
            terceirizada += 1
        elif tipo == "Mista":
            mista += 1
        else:
            sem_equipe += 1
    total = len(sub)
    return {
        "propria": propria,
        "terceirizada": terceirizada,
        "mista": mista,
        "sem_equipe": sem_equipe,
        "total": total,
        "pct_propria": round(propria / total * 100, 1) if total else 0,
        "pct_terceirizada": round(terceirizada / total * 100, 1) if total else 0,
        "pct_mista": round(mista / total * 100, 1) if total else 0,
        "pct_sem_equipe": round(sem_equipe / total * 100, 1) if total else 0,
    }


def pct_tois_com_desvio(df: pd.DataFrame) -> float:
    """Percentual de TOIs com pelo menos um desvio do laboratório."""
    df = ensure_monitoramento_schema(df)
    total = len(df)
    if total == 0:
        return 0.0
    return round(count_desvios_laboratorio(df) / total * 100, 1)


def filter_desvios_laboratorio(df: pd.DataFrame, mode: str) -> pd.DataFrame:
    """Filtra por desvios lab.: 'com', 'sem' ou qualquer outro valor (sem filtro)."""
    df = ensure_monitoramento_schema(df)
    if mode == "com":
        return df[df["desvios_encontrados"].apply(has_desvios_laboratorio)]
    if mode == "sem":
        return df[~df["desvios_encontrados"].apply(has_desvios_laboratorio)]
    return df


def filter_por_tipo_equipe(
    df: pd.DataFrame, tipo: str, apenas_com_desvio: bool = True
) -> pd.DataFrame:
    """Filtra registros pelo tipo de equipe (Própria, Terceirizada, Mista, Sem equipe)."""
    data = ensure_monitoramento_schema(df)
    if apenas_com_desvio:
        data = data[data["desvios_encontrados"].apply(has_desvios_laboratorio)]
    if tipo == "Sem equipe":
        mask = data.apply(lambda r: _tipo_equipe_registro(r) == "", axis=1)
    else:
        mask = data.apply(lambda r: _tipo_equipe_registro(r) == tipo, axis=1)
    return data[mask].reset_index(drop=True)


def filter_por_desvio_tipo(df: pd.DataFrame, tipo_label: str) -> pd.DataFrame:
    """Filtra TOIs que possuem o tipo de desvio informado (rótulo do painel)."""
    data = ensure_monitoramento_schema(df)

    def matches(value: object) -> bool:
        return any(
            _desvio_rank_label(d) == tipo_label for d in parse_desvios_encontrados(value)
        )

    return data[data["desvios_encontrados"].apply(matches)].reset_index(drop=True)


def filter_por_csd(df: pd.DataFrame, csd: str) -> pd.DataFrame:
    data = ensure_monitoramento_schema(df)
    return data[data["csd"].astype(str).str.strip() == str(csd).strip()].reset_index(drop=True)


def filter_por_matricula(df: pd.DataFrame, matricula: str) -> pd.DataFrame:
    data = ensure_monitoramento_schema(df)
    mat = str(matricula).strip()
    m1 = data["matricula_1"].astype(str).str.strip()
    m2 = data["matricula_2"].astype(str).str.strip()
    return data[(m1 == mat) | (m2 == mat)].reset_index(drop=True)


def filter_medidor_resultado(df: pd.DataFrame, em_ordem: bool) -> pd.DataFrame:
    data = ensure_monitoramento_schema(df)
    if em_ordem:
        return data[data["medidor_ordem"]].reset_index(drop=True)
    return data[~data["medidor_ordem"]].reset_index(drop=True)


def expand_desvios_ocorrencias(df: pd.DataFrame) -> pd.DataFrame:
    """Uma linha por ocorrência de desvio (coluna desvio_item)."""
    data = ensure_monitoramento_schema(df)
    data = data[data["desvios_encontrados"].apply(has_desvios_laboratorio)]
    rows: list[pd.Series] = []
    for _, row in data.iterrows():
        for desvio in parse_desvios_encontrados(row["desvios_encontrados"]):
            item = row.copy()
            item["desvio_item"] = _desvio_rank_label(desvio)
            rows.append(item)
    if not rows:
        return data.iloc[0:0].copy()
    return pd.DataFrame(rows).reset_index(drop=True)


def periodo_agendamento(df: pd.DataFrame) -> str:
    """Período do primeiro ao último registro da base (data do agendamento)."""
    data = ensure_monitoramento_schema(df)
    if data.empty:
        return "Sem dados"
    valid = data[data["data_disp"].notna()]
    if valid.empty:
        return "Sem datas"
    inicio = valid.iloc[0]["data_disp"]
    fim = valid.iloc[-1]["data_disp"]
    return f"{inicio.strftime('%d/%m/%Y')} até {fim.strftime('%d/%m/%Y')}"


def kpi_metrics(df: pd.DataFrame | None = None) -> dict:
    data = df if df is not None else load_monitoramento()
    laudo = laudo_summary(data)
    csds = data["csd"].dropna().nunique() if not data.empty else 0
    csds = csds - (1 if (data["csd"] == "nan").any() else 0) if not data.empty else 0
    return {
        "total_ensaios": len(data),
        "csds": max(int(csds), 0),
        "laudos_incorretos": laudo["nao"],
        "laudos_corretos": laudo["sim"],
        "laudos_pendentes": laudo["pendente"],
        "taxa_conformidade": laudo["pct_sim"],
        "tipos_irregularidade": int(data["irregularidade"].nunique()) if not data.empty else 0,
        "medidores_ordem": int(data["medidor_ordem"].sum()) if not data.empty else 0,
        "medidores_irregulares": int((~data["medidor_ordem"]).sum()) if not data.empty else 0,
        "periodo": periodo_agendamento(data),
        "tois_com_desvio": count_desvios_laboratorio(data),
        "total_desvios_encontrados": count_total_desvios_encontrados(data),
        "pct_tois_com_desvio": pct_tois_com_desvio(data),
    }


def laudo_summary(df: pd.DataFrame | None = None) -> dict:
    data = df if df is not None else load_monitoramento()
    if data.empty:
        return {
            "sim": 0, "nao": 0, "pendente": 0, "total": 0,
            "pct_sim": 0, "pct_nao": 0, "pct_pendente": 0,
        }
    counts = data["laudo"].value_counts()
    sim = int(counts.get("Sim", 0))
    nao = int(counts.get("Não", 0))
    pendente = int(counts.get("Pendente", 0))
    avaliados = sim + nao
    return {
        "sim": sim,
        "nao": nao,
        "pendente": pendente,
        "total": len(data),
        "pct_sim": round(sim / avaliados * 100, 1) if avaliados else 0,
        "pct_nao": round(nao / avaliados * 100, 1) if avaliados else 0,
        "pct_pendente": round(pendente / len(data) * 100, 1) if len(data) else 0,
    }


def medidor_summary(df: pd.DataFrame | None = None) -> dict:
    data = df if df is not None else load_monitoramento()
    if data.empty:
        return {"em_ordem": 0, "irregular": 0, "pct_ordem": 0, "pct_irregular": 0}
    ordem = int(data["medidor_ordem"].sum())
    irreg = int((~data["medidor_ordem"]).sum())
    total = ordem + irreg
    return {
        "em_ordem": ordem,
        "irregular": irreg,
        "pct_ordem": round(ordem / total * 100, 1) if total else 0,
        "pct_irregular": round(irreg / total * 100, 1) if total else 0,
    }


def irregularidade_ranking(df: pd.DataFrame | None = None, top_n: int = 12) -> pd.DataFrame:
    data = df if df is not None else load_monitoramento()
    sub = data[~data["medidor_ordem"]] if not data.empty else data
    if sub.empty:
        return pd.DataFrame(columns=["tipo", "count"])
    counts = sub["irregularidade"].value_counts().head(top_n)
    return pd.DataFrame({"tipo": counts.index, "count": counts.values})


def csd_breakdown(df: pd.DataFrame | None = None) -> pd.DataFrame:
    """Resumo por CSD: total de ensaios e % de TOIs com desvio do laboratório."""
    data = ensure_monitoramento_schema(df if df is not None else load_monitoramento())
    cols = ["csd", "total", "com_desvio", "pct_desvio"]
    if data.empty:
        return pd.DataFrame(columns=cols)
    rows = []
    valid = data[data["csd"].notna() & (data["csd"] != "nan")]
    for csd, sub in valid.groupby("csd"):
        total = len(sub)
        com_desvio = int(sub["desvios_encontrados"].apply(has_desvios_laboratorio).sum())
        rows.append(
            {
                "csd": csd,
                "total": total,
                "com_desvio": com_desvio,
                "pct_desvio": round(com_desvio / total * 100, 1) if total else 0,
            }
        )
    if not rows:
        return pd.DataFrame(columns=cols)
    return pd.DataFrame(rows).sort_values("total", ascending=False)


def timeline_monthly(df: pd.DataFrame | None = None) -> pd.DataFrame:
    data = df if df is not None else load_monitoramento()
    cols = ["mes", "total", "irregularidades", "laudo_nao"]
    if data.empty:
        return pd.DataFrame(columns=cols)
    rows = []
    for mes, sub in data.groupby("mes"):
        if mes == "NaT" or not mes:
            continue
        rows.append(
            {
                "mes": mes,
                "total": len(sub),
                "irregularidades": int((~sub["medidor_ordem"]).sum()),
                "laudo_nao": int((sub["laudo"] == "Não").sum()),
            }
        )
    if not rows:
        return pd.DataFrame(columns=cols)
    return pd.DataFrame(rows).sort_values("mes")


def inspetor_issues_ranking(df: pd.DataFrame | None = None) -> pd.DataFrame:
    data = df if df is not None else load_monitoramento()
    counter: Counter[str] = Counter()
    for issues in data["inspetor_issues"]:
        counter.update(issues)
    if not counter:
        return pd.DataFrame(columns=["tipo", "count"])
    return pd.DataFrame(
        [{"tipo": k, "count": v} for k, v in counter.most_common()]
    )


def filter_ficha(df: pd.DataFrame, query: str, csd: str | None = None) -> pd.DataFrame:
    out = df.copy()
    if csd and csd != "Todos":
        out = out[out["csd"] == csd]
    if query.strip():
        q = query.strip().lower()
        text_cols = [
            "csd", "toi", "medidor", "instalacao", "status",
            "mes_inicio", "irregularidade", "irregularidade_raw", "inspetor",
            "sinalizacao", "colaborador_1", "colaborador_2",
            "matricula_1", "matricula_2", "nota",
            "analisador", "desvios_encontrados",
        ]
        mask = pd.Series(False, index=out.index)
        for col in text_cols:
            if col in out.columns:
                mask |= out[col].astype(str).str.lower().str.contains(q, na=False)
        out = out[mask]
    return out


def _normalize_matricula(value: object) -> str:
    if pd.isna(value):
        return ""
    text = str(value).strip()
    if not text or text.lower() == "nan":
        return ""
    if text.endswith(".0"):
        text = text[:-2]
    return text.upper()


def _normalize_nome(value: object) -> str:
    if pd.isna(value):
        return ""
    text = str(value).strip()
    return text.title() if text and text.lower() != "nan" else ""


def _tipo_colaborador(matricula: str) -> str:
    return "Terceirizada" if matricula.upper().startswith("RT") else "Própria"


def _tipo_colaborador_from_value(value: object) -> str:
    mat = _normalize_matricula(value)
    if not mat:
        return ""
    return _tipo_colaborador(mat)


def colaboradores_resumo(df: pd.DataFrame | None = None) -> pd.DataFrame:
    """Lista única de colaboradores (nome + matrícula) a partir das duplas."""
    data = df if df is not None else load_monitoramento()
    cols = ["colaborador", "nome", "matricula", "tipo", "aparicoes", "csds"]
    if data.empty:
        return pd.DataFrame(columns=cols)

    registros: dict[str, dict] = {}
    for _, row in data.iterrows():
        csd = row.get("csd")
        for nome_col, mat_col in (("colaborador_1", "matricula_1"), ("colaborador_2", "matricula_2")):
            mat = _normalize_matricula(row.get(mat_col))
            if not mat:
                continue
            nome = _normalize_nome(row.get(nome_col))
            if mat not in registros:
                registros[mat] = {
                    "nome": nome,
                    "aparicoes": 0,
                    "csds": set(),
                }
            elif nome and not registros[mat]["nome"]:
                registros[mat]["nome"] = nome
            registros[mat]["aparicoes"] += 1
            if pd.notna(csd) and str(csd).strip() and str(csd) != "nan":
                registros[mat]["csds"].add(str(csd).strip())

    rows = []
    for mat, info in registros.items():
        nome = info["nome"] or "—"
        rows.append(
            {
                "colaborador": f"{nome} — Matrícula {mat}",
                "nome": nome,
                "matricula": mat,
                "tipo": _tipo_colaborador(mat),
                "aparicoes": info["aparicoes"],
                "csds": len(info["csds"]),
            }
        )
    return pd.DataFrame(rows).sort_values(["nome", "matricula"]).reset_index(drop=True)


def filter_colaboradores(resumo: pd.DataFrame, query: str, tipo: str | None = None) -> pd.DataFrame:
    out = resumo.copy()
    if tipo and tipo != "Todos":
        out = out[out["tipo"] == tipo]
    if query.strip():
        q = query.strip().lower()
        mask = (
            out["nome"].str.lower().str.contains(q, na=False)
            | out["matricula"].str.lower().str.contains(q, na=False)
            | out["colaborador"].str.lower().str.contains(q, na=False)
        )
        out = out[mask]
    return out


def _equipe_key(row: pd.Series) -> str | None:
    """Identificador único da equipe (dupla de matrículas) em um registro."""
    m1 = _normalize_matricula(row.get("matricula_1"))
    m2 = _normalize_matricula(row.get("matricula_2"))
    if m1 and m2:
        return "|".join(sorted([m1, m2]))
    if m1:
        return m1
    if m2:
        return m2
    return None


def _equipe_display_label(key: str | None) -> str:
    """Rótulo da equipe apenas com matrículas (ex.: 6636 · 6472)."""
    if not key:
        return "Sem matrícula"
    return " · ".join(key.split("|"))


def csds_resumo(df: pd.DataFrame | None = None) -> pd.DataFrame:
    """Lista única de CSDs presentes na base."""
    data = df if df is not None else load_monitoramento()
    cols = ["csd", "ensaios", "rotatividade_equipe", "colaboradores"]
    if data.empty:
        return pd.DataFrame(columns=cols)

    valid = data[data["csd"].notna() & (data["csd"] != "nan")]
    rows = []
    for csd, sub in valid.groupby("csd"):
        colabs: set[str] = set()
        equipes: set[str] = set()
        for _, row in sub.iterrows():
            for mat_col in ("matricula_1", "matricula_2"):
                mat = _normalize_matricula(row.get(mat_col))
                if mat:
                    colabs.add(mat)
            equipe = _equipe_key(row)
            if equipe:
                equipes.add(equipe)
        rows.append(
            {
                "csd": csd,
                "ensaios": len(sub),
                "rotatividade_equipe": len(equipes),
                "colaboradores": len(colabs),
            }
        )
    if not rows:
        return pd.DataFrame(columns=cols)
    return pd.DataFrame(rows).sort_values("csd").reset_index(drop=True)


def filter_csds(resumo: pd.DataFrame, query: str) -> pd.DataFrame:
    out = resumo.copy()
    if query.strip():
        q = query.strip().lower()
        out = out[out["csd"].str.lower().str.contains(q, na=False)]
    return out


def _normalize_instalacao(value: object) -> str:
    return _normalize_key(value)


def _match_key(toi: object, instalacao: object) -> str:
    toi_key = _normalize_key(toi)
    inst_key = _normalize_instalacao(instalacao)
    if not toi_key or not inst_key:
        return ""
    return f"{toi_key}|{inst_key}"


def _normalize_lab_desvio(text: object) -> str | None:
    if _is_blank(text):
        return None
    raw = str(text).strip()
    if _normalize_header(raw).startswith("unnamed"):
        return None
    low = raw.lower()
    for canonical, pattern in LAB_DESVIO_PATTERNS:
        if re.search(pattern, low, re.I):
            return canonical
    for canonical in LAB_DESVIOS_CANONICOS:
        if canonical.lower() == low:
            return canonical
    return raw


def parse_desvios_encontrados(value: object) -> list[str]:
    if _is_blank(value):
        return []
    text = str(value).strip()
    if text.startswith("[") and text.endswith("]"):
        try:
            parsed = ast.literal_eval(text)
            if isinstance(parsed, list):
                out: list[str] = []
                for item in parsed:
                    norm = _normalize_lab_desvio(item)
                    if norm and norm not in out:
                        out.append(norm)
                return out
        except (SyntaxError, ValueError):
            pass
    parts = re.split(r"[;|\n]+", text)
    out = []
    for part in parts:
        norm = _normalize_lab_desvio(part)
        if norm and norm not in out:
            out.append(norm)
    return out


def format_desvios_encontrados(desvios: list[str]) -> str:
    return "; ".join(desvios)


def _desvio_rank_label(canonical: str) -> str:
    return DESVIO_DISPLAY_LABELS.get(canonical, canonical)


def desvios_ranking(df: pd.DataFrame | None = None) -> pd.DataFrame:
    """Ranking de ocorrências por tipo de desvio (coluna Desvios encontrados)."""
    data = ensure_monitoramento_schema(df if df is not None else load_monitoramento())
    exclude = {d.lower() for d in DESVIOS_RANKING_EXCLUDE}
    counter: Counter[str] = Counter()
    for val in data["desvios_encontrados"]:
        for desvio in parse_desvios_encontrados(val):
            if desvio.lower() in exclude:
                continue
            counter[_desvio_rank_label(desvio)] += 1
    if not counter:
        return pd.DataFrame(columns=["tipo", "count"])
    rows = [{"tipo": label, "count": count} for label, count in counter.most_common()]
    return pd.DataFrame(rows).sort_values("count", ascending=True)


def _count_desvios_row(value: object) -> int:
    """Conta desvios de um registro, excluindo tipos de inconsistência administrativa."""
    exclude = {d.lower() for d in DESVIOS_RANKING_EXCLUDE}
    return sum(
        1
        for desvio in parse_desvios_encontrados(value)
        if desvio.lower() not in exclude
    )


def timeline_desvios_monthly(df: pd.DataFrame | None = None) -> pd.DataFrame:
    """Totais mensais de desvios com base na data do agendamento."""
    data = ensure_monitoramento_schema(df if df is not None else load_monitoramento())
    cols = ["mes", "ensaios", "tois_com_desvio", "ocorrencias_desvio", "pct_com_desvio"]
    if data.empty:
        return pd.DataFrame(columns=cols)

    rows = []
    for mes, sub in data.groupby("mes"):
        if not mes or mes == "NaT":
            continue
        ensaios = len(sub)
        com = sub[sub["desvios_encontrados"].apply(has_desvios_laboratorio)]
        com_desvio = len(com)
        ocorrencias = int(com["desvios_encontrados"].apply(_count_desvios_row).sum())
        rows.append(
            {
                "mes": mes,
                "ensaios": ensaios,
                "tois_com_desvio": com_desvio,
                "ocorrencias_desvio": ocorrencias,
                "pct_com_desvio": round(com_desvio / ensaios * 100, 1) if ensaios else 0,
            }
        )
    if not rows:
        return pd.DataFrame(columns=cols)
    return pd.DataFrame(rows).sort_values("mes")


def timeline_desvios_por_equipe(df: pd.DataFrame | None = None) -> pd.DataFrame:
    """TOIs com desvio por mês e dupla de matrículas."""
    data = ensure_monitoramento_schema(df if df is not None else load_monitoramento())
    cols = ["mes", "equipe", "count"]
    if data.empty:
        return pd.DataFrame(columns=cols)

    com = data[data["desvios_encontrados"].apply(has_desvios_laboratorio)].copy()
    com["_equipe_key"] = com.apply(_equipe_key, axis=1)
    com["equipe"] = com["_equipe_key"].map(_equipe_display_label)

    rows = []
    for mes, sub in com.groupby("mes"):
        if not mes or mes == "NaT":
            continue
        for equipe, cnt in sub.groupby("equipe").size().items():
            rows.append({"mes": mes, "equipe": equipe, "count": int(cnt)})
    if not rows:
        return pd.DataFrame(columns=cols)
    return pd.DataFrame(rows).sort_values(["mes", "count"], ascending=[True, False])


def _pessoa_display_label(mat: str) -> str:
    return mat


def timeline_desvios_por_pessoa(df: pd.DataFrame | None = None) -> pd.DataFrame:
    """TOIs com desvio por mês e colaborador (matrícula)."""
    data = ensure_monitoramento_schema(df if df is not None else load_monitoramento())
    cols = ["mes", "pessoa", "count"]
    if data.empty:
        return pd.DataFrame(columns=cols)

    com = data[data["desvios_encontrados"].apply(has_desvios_laboratorio)].copy()
    rows: list[dict] = []
    for _, row in com.iterrows():
        mes = row.get("mes")
        if not mes or mes == "NaT":
            continue
        for mat_col in ("matricula_1", "matricula_2"):
            mat = _normalize_matricula(row.get(mat_col))
            if not mat:
                continue
            pessoa = _pessoa_display_label(mat)
            rows.append({"mes": mes, "pessoa": pessoa, "count": 1})

    if not rows:
        return pd.DataFrame(columns=cols)
    agg = (
        pd.DataFrame(rows)
        .groupby(["mes", "pessoa"], as_index=False)["count"]
        .sum()
    )
    return agg.sort_values(["mes", "count"], ascending=[True, False])


def _mes_display(mes: str) -> str:
    try:
        return pd.Period(mes, freq="M").strftime("%m/%Y")
    except (ValueError, TypeError):
        return str(mes)


def _classificar_tendencia_colaborador(
    monthly_stats: list[tuple[str, int, int]],
) -> str:
    pcts: list[float] = []
    for _mes, total, com in monthly_stats:
        if total > 0:
            pcts.append(com / total * 100)
    if len(pcts) < 2:
        return "Poucos dados"
    mid = max(1, len(pcts) // 2)
    first = sum(pcts[:mid]) / len(pcts[:mid])
    second = sum(pcts[mid:]) / len(pcts[mid:])
    diff = second - first
    if diff > 5:
        return "Piorou"
    if diff < -5:
        return "Melhorou"
    return "Estável"


def _classificar_influencia_colaborador(
    partner_dev_types: dict[str, Counter],
) -> str:
    if len(partner_dev_types) < 2:
        return "Indeterminado"
    tops: list[str] = []
    for counter in partner_dev_types.values():
        if counter:
            tops.append(counter.most_common(1)[0][0])
    unique = set(tops)
    if len(unique) == 1:
        return "Influencia"
    if len(unique) >= 2:
        return "Influenciado"
    return "Indeterminado"


def colaborador_analise(df: pd.DataFrame | None = None) -> pd.DataFrame:
    """Resumo analítico por matrícula: parceiros, tendência, influência e desvios."""
    data = ensure_monitoramento_schema(df if df is not None else load_monitoramento())
    cols = [
        "matricula",
        "tipo",
        "total_tois",
        "com_desvio",
        "pct_desvio",
        "parceiros",
        "tendencia",
        "influencia",
        "tois_por_mes",
        "tipos_desvio",
    ]
    if data.empty:
        return pd.DataFrame(columns=cols)

    exclude = {d.lower() for d in DESVIOS_RANKING_EXCLUDE}
    persons: dict[str, dict] = {}

    def _person(mat: str) -> dict:
        if mat not in persons:
            persons[mat] = {
                "total_tois": 0,
                "com_desvio": 0,
                "parceiros": set(),
                "mes_total": defaultdict(int),
                "mes_desvio": defaultdict(int),
                "desvios_counter": Counter(),
                "partner_dev_types": defaultdict(Counter),
            }
        return persons[mat]

    for _, row in data.iterrows():
        m1 = _normalize_matricula(row.get("matricula_1"))
        m2 = _normalize_matricula(row.get("matricula_2"))
        mes = row.get("mes")
        com_desvio = has_desvios_laboratorio(row.get("desvios_encontrados"))
        desvios = [
            d
            for d in parse_desvios_encontrados(row.get("desvios_encontrados"))
            if d.lower() not in exclude
        ]

        pairs: list[tuple[str, str | None]] = []
        if m1 and m2:
            pairs = [(m1, m2), (m2, m1)]
        elif m1:
            pairs = [(m1, None)]
        elif m2:
            pairs = [(m2, None)]

        for mat, partner in pairs:
            p = _person(mat)
            p["total_tois"] += 1
            if mes and str(mes) not in ("NaT", ""):
                p["mes_total"][mes] += 1
            if com_desvio:
                p["com_desvio"] += 1
                if mes and str(mes) not in ("NaT", ""):
                    p["mes_desvio"][mes] += 1
                for desvio in desvios:
                    p["desvios_counter"][desvio] += 1
                    if partner:
                        p["partner_dev_types"][partner][desvio] += 1
            if partner:
                p["parceiros"].add(partner)

    rows: list[dict] = []
    for mat, p in persons.items():
        monthly = sorted(p["mes_total"].keys())
        monthly_stats = [
            (m, p["mes_total"][m], p["mes_desvio"].get(m, 0)) for m in monthly
        ]
        tois_mes = " | ".join(f"{_mes_display(m)}: {p['mes_total'][m]}" for m in monthly)
        tipos = "; ".join(
            f"{_desvio_rank_label(k)} ({v})"
            for k, v in p["desvios_counter"].most_common(8)
        )
        total = p["total_tois"]
        com = p["com_desvio"]
        pct = round(com / total * 100, 1) if total else 0.0
        rows.append(
            {
                "matricula": mat,
                "tipo": _tipo_colaborador(mat),
                "total_tois": total,
                "com_desvio": com,
                "pct_desvio": pct,
                "parceiros": len(p["parceiros"]),
                "tendencia": _classificar_tendencia_colaborador(monthly_stats),
                "influencia": _classificar_influencia_colaborador(p["partner_dev_types"]),
                "tois_por_mes": tois_mes,
                "tipos_desvio": tipos or "—",
            }
        )

    return (
        pd.DataFrame(rows)
        .sort_values(["total_tois", "pct_desvio"], ascending=[False, False])
        .reset_index(drop=True)
    )


def _equipe_mats_from_row(
    row: pd.Series,
    mat_cols: tuple[str, str] = ("matricula_1", "matricula_2"),
) -> set[str]:
    mats: set[str] = set()
    for col in mat_cols:
        mat = _normalize_matricula(row.get(col))
        if mat:
            mats.add(mat)
    return mats


def _resolve_apontamentos_columns(raw: pd.DataFrame) -> dict[str, str | None]:
    norm_map = {_normalize_header(str(c)): c for c in raw.columns}

    def pick(*aliases: str) -> str | None:
        for alias in aliases:
            key = _normalize_header(alias)
            if key in norm_map:
                return norm_map[key]
        return None

    matricula_1 = pick("matricula", "matricula_1", "matrícula", "matrícula_1")
    matricula_2 = pick(
        "matricula_2",
        "matrícula_2",
        "matricula.1",
        "matrícula.1",
        "matrícula_2",
    )
    if matricula_1 and matricula_2 == matricula_1:
        mat_cols = [
            c
            for c in raw.columns
            if _normalize_header(str(c)) in {"matricula", "matrícula"}
        ]
        if len(mat_cols) >= 2:
            matricula_1, matricula_2 = mat_cols[0], mat_cols[1]

    return {
        "toi": pick("toi", "tois"),
        "instalacao": pick("inst.", "inst", "instalação", "instalacao"),
        "analisador": pick("analisador", "técnico", "tecnico"),
        "descricao": pick("descrição", "descricao", "descrição do desvio"),
        "categorias": pick(
            "categorias",
            "categoria",
            "desvio",
            "divergência",
            "divergencia",
        ),
        "matricula_1": matricula_1,
        "matricula_2": matricula_2,
        "colaborador_1": pick("colarador 1", "colaborador 1", "colaborador_1"),
        "colaborador_2": pick("colaborador 2", "colaborador_2"),
    }


def _is_drm_protected_excel(path: Path) -> bool:
    try:
        import olefile

        if not olefile.isOleFile(str(path)):
            return False
        with olefile.OleFileIO(str(path)) as ole:
            return ole.exists("EncryptedPackage")
    except Exception:  # noqa: BLE001
        return False


def _read_apontamentos_via_com(path: Path) -> pd.DataFrame:
    """Lê planilha protegida (IRM) via Excel instalado no Windows."""
    if sys.platform != "win32":
        raise ValueError(
            f"Arquivo protegido não pode ser lido sem Excel no Windows: {path.name}"
        )
    try:
        import win32com.client  # type: ignore[import-untyped]
    except ImportError as exc:
        raise ValueError(
            "Instale pywin32 para importar planilhas protegidas por DRM: pip install pywin32"
        ) from exc

    import datetime as dt

    excel = win32com.client.Dispatch("Excel.Application")
    excel.Visible = False
    excel.DisplayAlerts = False
    wb = None
    try:
        wb = excel.Workbooks.Open(str(path.resolve()))
        best_sheet = None
        best_header_row = None
        for sheet in wb.Sheets:
            for row_idx in range(1, 16):
                if str(sheet.Cells(row_idx, 1).Value or "").strip().upper() == "TOI":
                    if best_header_row is None or row_idx < best_header_row:
                        best_sheet = sheet
                        best_header_row = row_idx
                    break
        if best_sheet is None or best_header_row is None:
            raise ValueError(f"Nenhuma aba com coluna TOI encontrada em {path.name}")

        used_cols = best_sheet.UsedRange.Columns.Count
        used_rows = best_sheet.UsedRange.Rows.Count
        headers: list[str] = []
        seen: dict[str, int] = {}
        for col_idx in range(1, used_cols + 1):
            header = best_sheet.Cells(best_header_row, col_idx).Value
            base = str(header).strip() if header not in (None, "") else f"_col_{col_idx}"
            count = seen.get(base, 0)
            seen[base] = count + 1
            headers.append(base if count == 0 else f"{base}_{count + 1}")

        rows: list[dict[str, object]] = []
        for row_idx in range(best_header_row + 1, used_rows + 1):
            toi_val = best_sheet.Cells(row_idx, 1).Value
            if toi_val is None or str(toi_val).strip() == "":
                continue
            item: dict[str, object] = {}
            for col_idx, header in enumerate(headers, start=1):
                val = best_sheet.Cells(row_idx, col_idx).Value
                if isinstance(val, dt.datetime):
                    val = val.replace(tzinfo=None).strftime("%Y-%m-%d %H:%M:%S")
                item[header] = val
            rows.append(item)
        return pd.DataFrame(rows)
    finally:
        if wb is not None:
            wb.Close(False)
        excel.Quit()


def _find_apontamentos_header_row(raw: pd.DataFrame) -> int | None:
    for idx in range(min(15, len(raw))):
        val = raw.iloc[idx, 0]
        if str(val).strip().upper() == "TOI":
            return idx
    return None


def _fix_apontamentos_column_names(
    raw: pd.DataFrame,
    title_row: pd.Series | None,
) -> pd.DataFrame:
    """Corrige colunas cujo cabeçalho veio com valor de exemplo (ex.: planilha TOIs com divergências)."""
    if title_row is None:
        return raw
    rename: dict[str, str] = {}
    for i, col in enumerate(raw.columns):
        if i >= len(title_row):
            break
        title = title_row.iloc[i]
        if pd.isna(title) or not str(title).strip():
            continue
        title_str = str(title).strip()
        title_norm = _normalize_header(title_str)
        col_norm = _normalize_header(str(col))
        if title_norm in {"desvio", "divergencia", "divergência", "incio da análise", "inicio da analise"}:
            if col_norm != title_norm:
                rename[str(col)] = title_str
    if rename:
        raw = raw.rename(columns=rename)
    return raw


def _read_apontamentos_sheet_pandas(path: Path, sheet_name: str | int | None = None) -> pd.DataFrame:
    engines: list[str | None] = ["openpyxl", "xlrd", None]
    last_error: Exception | None = None
    for engine in engines:
        try:
            xl = pd.ExcelFile(path, engine=engine) if engine else pd.ExcelFile(path)
            target_sheet: str | int = sheet_name if sheet_name is not None else 0
            header_row: int | None = None
            for sheet in xl.sheet_names:
                preview = pd.read_excel(path, sheet_name=sheet, header=None, nrows=15, engine=engine)
                header_row = _find_apontamentos_header_row(preview)
                if header_row is not None:
                    target_sheet = sheet
                    break
            if header_row is None:
                raw = pd.read_excel(path, sheet_name=target_sheet, engine=engine)
                raw.columns = [str(c).strip() for c in raw.columns]
                return raw
            title_preview = pd.read_excel(
                path,
                sheet_name=target_sheet,
                header=None,
                nrows=header_row,
                engine=engine,
            )
            title_row = title_preview.iloc[header_row - 1] if header_row > 0 else None
            raw = pd.read_excel(path, sheet_name=target_sheet, header=header_row, engine=engine)
            raw.columns = [
                str(c).strip() if not pd.isna(c) else f"_col_{i}"
                for i, c in enumerate(raw.columns)
            ]
            raw = _fix_apontamentos_column_names(raw, title_row)
            return raw
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            continue
    if last_error:
        raise last_error
    return pd.DataFrame()


def _read_apontamentos(source: str | Path) -> pd.DataFrame:
    path = Path(source)
    if not path.is_file():
        raise FileNotFoundError(f"Arquivo de apontamentos não encontrado: {path}")

    if _is_drm_protected_excel(path):
        return _read_apontamentos_via_com(path)

    errors: list[str] = []
    for engine in ("openpyxl", "xlrd", None):
        try:
            raw = _read_apontamentos_sheet_pandas(path)
            if raw.empty:
                return raw
            return raw
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{engine or 'auto'}: {exc}")

    if sys.platform == "win32":
        try:
            return _read_apontamentos_via_com(path)
        except Exception as exc:  # noqa: BLE001
            errors.append(f"excel-com: {exc}")

    raise ValueError("Não foi possível ler o arquivo de apontamentos. " + " | ".join(errors))


def _apontamentos_desvio_columns(raw: pd.DataFrame, cols: dict[str, str | None]) -> list[str]:
    """Colunas extras cujo cabeçalho ou conteúdo representa tipos de desvio."""
    reserved = {
        cols.get("toi"),
        cols.get("instalacao"),
        cols.get("analisador"),
        cols.get("descricao"),
        cols.get("categorias"),
        cols.get("matricula_1"),
        cols.get("matricula_2"),
        cols.get("colaborador_1"),
        cols.get("colaborador_2"),
    }
    reserved_norm = {
        _normalize_header(str(c))
        for c in reserved
        if c is not None
    }
    reserved_norm.update(
        {
            "csd",
            "cidade",
            "data",
            "nota",
            "medidor",
            "status",
            "incio da análise",
            "inicio da analise",
        }
    )

    desvio_cols: list[str] = []
    for col in raw.columns:
        if col in reserved or col is None:
            continue
        norm = _normalize_header(str(col))
        if norm in reserved_norm or norm.startswith("_col_") or norm.startswith("unnamed"):
            continue
        if norm in {"matricula", "matrícula"}:
            continue
        if _normalize_lab_desvio(col):
            desvio_cols.append(col)
    return desvio_cols


def _merge_apontamentos_frames(frames: list[pd.DataFrame]) -> pd.DataFrame:
    if not frames:
        return pd.DataFrame(columns=["match_key", "analisador", "desvios", "equipe_mats"])
    grouped: dict[str, dict] = {}
    for frame in frames:
        if frame.empty:
            continue
        for _, row in frame.iterrows():
            key = row["match_key"]
            if key not in grouped:
                grouped[key] = {
                    "match_key": key,
                    "analisador": set(),
                    "desvios": list(row.get("desvios") or []),
                    "equipe_mats": set(row.get("equipe_mats") or set()),
                }
            else:
                for desvio in row.get("desvios") or []:
                    if desvio not in grouped[key]["desvios"]:
                        grouped[key]["desvios"].append(desvio)
                grouped[key]["equipe_mats"].update(row.get("equipe_mats") or set())
            analisador = str(row.get("analisador", "")).strip()
            if analisador and analisador.lower() != "nan":
                for part in re.split(r"[,;]+", analisador):
                    part = part.strip()
                    if part:
                        grouped[key]["analisador"].add(part)
    out_rows = []
    for info in grouped.values():
        out_rows.append(
            {
                "match_key": info["match_key"],
                "analisador": ", ".join(sorted(info["analisador"])),
                "desvios": info["desvios"],
                "equipe_mats": info["equipe_mats"],
            }
        )
    return pd.DataFrame(out_rows)


def _parse_apontamentos_rows(raw: pd.DataFrame) -> pd.DataFrame:
    cols = _resolve_apontamentos_columns(raw)
    if not cols["toi"] or not cols["instalacao"]:
        raise ValueError("A planilha de apontamentos precisa conter colunas TOI e Instalação.")

    extra_desvio_cols = _apontamentos_desvio_columns(raw, cols)
    rows = []
    for _, row in raw.iterrows():
        key = _match_key(row.get(cols["toi"]), row.get(cols["instalacao"]))
        if not key:
            continue

        desvios: list[str] = []
        if cols["categorias"]:
            desvios.extend(parse_desvios_encontrados(row.get(cols["categorias"])))
        if cols["descricao"]:
            for item in parse_desvios_encontrados(row.get(cols["descricao"])):
                if item not in desvios:
                    desvios.append(item)
        for col in extra_desvio_cols:
            header_item = _normalize_lab_desvio(col)
            if header_item and header_item not in desvios:
                desvios.append(header_item)
            cell_item = row.get(col)
            for item in parse_desvios_encontrados(cell_item):
                if item not in desvios:
                    desvios.append(item)

        ap_mats: set[str] = set()
        for mat_col in (cols["matricula_1"], cols["matricula_2"]):
            if mat_col:
                mat = _normalize_matricula(row.get(mat_col))
                if mat:
                    ap_mats.add(mat)

        rows.append(
            {
                "match_key": key,
                "toi": row.get(cols["toi"]),
                "instalacao": row.get(cols["instalacao"]),
                "analisador": "" if cols["analisador"] is None else row.get(cols["analisador"], ""),
                "desvios": desvios,
                "equipe_mats": ap_mats,
            }
        )

    if not rows:
        return pd.DataFrame(columns=["match_key", "analisador", "desvios", "equipe_mats"])

    grouped: dict[str, dict] = {}
    for item in rows:
        key = item["match_key"]
        if key not in grouped:
            grouped[key] = {
                "match_key": key,
                "analisador": set(),
                "desvios": [],
                "equipe_mats": set(),
            }
        analisador = str(item["analisador"]).strip()
        if analisador and analisador.lower() != "nan":
            grouped[key]["analisador"].add(analisador)
        for desvio in item["desvios"]:
            if desvio not in grouped[key]["desvios"]:
                grouped[key]["desvios"].append(desvio)
        grouped[key]["equipe_mats"].update(item["equipe_mats"])

    out_rows = []
    for info in grouped.values():
        out_rows.append(
            {
                "match_key": info["match_key"],
                "analisador": ", ".join(sorted(info["analisador"])),
                "desvios": info["desvios"],
                "equipe_mats": info["equipe_mats"],
            }
        )
    return pd.DataFrame(out_rows)


def import_apontamentos_laboratorio(
    source: str | Path | Sequence[str | Path] | None = None,
    dest: str | Path | None = None,
) -> dict:
    """Cruza apontamentos do laboratório com a base por TOI + Instalação."""
    if source is None:
        sources: list[Path] = [APONTAMENTOS_LAB_FILE]
    elif isinstance(source, (str, Path)):
        sources = [Path(source)]
    else:
        sources = [Path(s) for s in source]

    dest_path = Path(dest) if dest else MONITORAMENTO_FILE

    parsed_frames: list[pd.DataFrame] = []
    sources_lidas: list[str] = []
    for source_path in sources:
        raw_ap = _read_apontamentos(source_path)
        parsed_frames.append(_parse_apontamentos_rows(raw_ap))
        sources_lidas.append(source_path.name)

    apontamentos = _merge_apontamentos_frames(parsed_frames)
    raw_base = _read_raw(dest_path)

    for col in MONITORAMENTO_COLUMNS:
        if col not in raw_base.columns:
            raw_base[col] = pd.NA

    lookup = {
        row["match_key"]: row
        for _, row in apontamentos.iterrows()
    }

    matched = 0
    with_desvios = 0
    equipe_divergente = 0

    for idx, row in raw_base.iterrows():
        key = _match_key(row.get("TOI"), row.get("Instalação"))
        if not key or key not in lookup:
            continue

        ap = lookup[key]
        desvios = list(ap["desvios"])
        base_mats = _equipe_mats_from_row(
            pd.Series(
                {
                    "matricula_1": row.get("Matricula_1"),
                    "matricula_2": row.get("Matricula_2"),
                }
            )
        )
        if ap["equipe_mats"] and base_mats and ap["equipe_mats"] != base_mats:
            if "Equipe divergente" not in desvios:
                desvios.insert(0, "Equipe divergente")
            equipe_divergente += 1

        raw_base.at[idx, "Analisador"] = ap["analisador"]
        raw_base.at[idx, "Desvios encontrados"] = format_desvios_encontrados(desvios)
        matched += 1
        if desvios:
            with_desvios += 1

    _save_raw_monitoramento(raw_base[MONITORAMENTO_COLUMNS], dest_path)

    return {
        "fontes": sources_lidas,
        "apontamentos_lidos": len(apontamentos),
        "registros_atualizados": matched,
        "com_desvios": with_desvios,
        "equipe_divergente": equipe_divergente,
        "nao_encontrados": max(len(apontamentos) - matched, 0),
    }


def _is_blank(value: object) -> bool:
    if pd.isna(value):
        return True
    text = str(value).strip()
    return not text or text.lower() == "nan"


def _normalize_key(value: object) -> str:
    if _is_blank(value):
        return ""
    text = str(value).strip()
    if text.endswith(".0"):
        text = text[:-2]
    return text


def _save_raw_monitoramento(raw: pd.DataFrame, path: Path | None = None) -> None:
    file_path = path or MONITORAMENTO_FILE
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(file_path, engine="openpyxl") as writer:
        raw.to_excel(writer, sheet_name=MONITORAMENTO_SHEET, index=False)
        pd.DataFrame().to_excel(writer, sheet_name="Planilha1", index=False)


def delete_monitoramento_rows(indices: list[int], path: str | Path | None = None) -> int:
    """Remove linhas da base Excel pelos índices (0-based, mesma ordem do load)."""
    file_path = Path(path) if path else MONITORAMENTO_FILE
    raw = _read_raw(file_path)
    valid = sorted({int(i) for i in indices if 0 <= int(i) < len(raw)})
    if not valid:
        return 0
    remaining = raw.drop(index=valid).reset_index(drop=True)
    _save_raw_monitoramento(remaining, file_path)
    return len(valid)


def inconsistencia_row_label(df: pd.DataFrame, idx: int) -> str:
    row = df.loc[idx]
    data = (
        row["data_disp"].strftime("%d/%m/%Y %H:%M")
        if pd.notna(row.get("data_disp"))
        else "—"
    )
    toi = row.get("toi", "—")
    medidor = row.get("medidor", "—")
    csd = row.get("csd", "—")
    return f"Linha {idx + 1} — TOI {toi} | Medidor {medidor} | CSD {csd} | {data}"


def inconsistencia_record_view(df: pd.DataFrame, indices: list[int]) -> pd.DataFrame:
    """Tabela resumida de registros com inconsistência."""
    rows = []
    for idx in indices:
        row = df.loc[idx]
        data = (
            row["data_disp"].strftime("%d/%m/%Y %H:%M")
            if pd.notna(row.get("data_disp"))
            else ""
        )
        rows.append(
            {
                "Linha": idx + 1,
                "Data do agendamento": data,
                "CSD": row.get("csd", ""),
                "Instalação": row.get("instalacao", ""),
                "Medidor": row.get("medidor", ""),
                "TOI": row.get("toi", ""),
                "Analisador": row.get("analisador", ""),
                "Desvios encontrados": row.get("desvios_encontrados", ""),
                "Colaborador_1": row.get("colaborador_1", ""),
                "Matricula_1": row.get("matricula_1", ""),
            }
        )
    return pd.DataFrame(rows)


def detect_inconsistencias(df: pd.DataFrame | None = None) -> list[dict]:
    """Detecta grupos de inconsistências na base (campos vazios e duplicidades)."""
    data = df if df is not None else load_monitoramento()
    groups: list[dict] = []
    if data.empty:
        return groups

    data = data.reset_index(drop=True)

    for idx, row in data.iterrows():
        missing = [
            label
            for field, label in MONITORAMENTO_REQUIRED_FIELDS.items()
            if _is_blank(row.get(field))
        ]
        if missing:
            groups.append(
                {
                    "id": f"missing_{idx}",
                    "tipo": "Campo faltando",
                    "descricao": f"Campos vazios: {', '.join(missing)}",
                    "indices": [int(idx)],
                    "campo_chave": None,
                }
            )

    for field, label in MONITORAMENTO_DUPLICATE_FIELDS.items():
        keys = data[field].apply(_normalize_key)
        valid_mask = keys != ""
        keyed = data[valid_mask].copy()
        keyed["_dup_key"] = keys[valid_mask]
        for key, sub in keyed.groupby("_dup_key"):
            if len(sub) <= 1:
                continue
            safe_key = re.sub(r"[^\w\-]", "_", str(key))
            groups.append(
                {
                    "id": f"dup_{field}_{safe_key}",
                    "tipo": "Registro duplicado",
                    "descricao": f"{label} {key} — {len(sub)} registros iguais",
                    "indices": [int(i) for i in sub.index.tolist()],
                    "campo_chave": label,
                }
            )

    for idx, row in data.iterrows():
        desvios = parse_desvios_encontrados(row.get("desvios_encontrados"))
        if not desvios:
            continue
        analisador = row.get("analisador", "")
        analisador_txt = (
            str(analisador).strip()
            if pd.notna(analisador) and str(analisador).strip().lower() != "nan"
            else "—"
        )
        has_equipe = any(d.lower() == "equipe divergente" for d in desvios)
        outros = [d for d in desvios if d.lower() != "equipe divergente"]
        if has_equipe:
            groups.append(
                {
                    "id": f"lab_equipe_{idx}",
                    "tipo": "Equipe divergente",
                    "descricao": (
                        f"Equipe divergente — analisador: {analisador_txt}"
                        + (f" · também: {', '.join(outros)}" if outros else "")
                    ),
                    "indices": [int(idx)],
                    "campo_chave": "Equipe",
                }
            )
        if outros:
            groups.append(
                {
                    "id": f"lab_desvio_{idx}",
                    "tipo": "Divergência do laboratório",
                    "descricao": (
                        f"{', '.join(outros)} — analisador: {analisador_txt}"
                    ),
                    "indices": [int(idx)],
                    "campo_chave": "Laboratório",
                }
            )

    return groups


def _resolve_equipe_columns(raw: pd.DataFrame) -> dict[str, str | None]:
    norm_map = {_normalize_header(str(c)): c for c in raw.columns}

    def pick(*aliases: str) -> str | None:
        for alias in aliases:
            key = _normalize_header(alias)
            if key in norm_map:
                return norm_map[key]
        return None

    matricula_1 = pick("matrícula", "matricula", "matricula_1", "matrícula_1")
    matricula_2 = pick(
        "matrícula.1",
        "matricula.1",
        "matrícula_2",
        "matricula_2",
    )
    mat_cols = [
        c
        for c in raw.columns
        if _normalize_header(str(c)) in {"matricula", "matrícula"}
        and raw[c].notna().any()
        and raw[c].astype(str).str.strip().str.lower().ne("nan").any()
    ]
    if not matricula_1 and mat_cols:
        matricula_1 = mat_cols[0]
    if not matricula_2 and len(mat_cols) >= 2:
        matricula_2 = mat_cols[1]
    elif not matricula_2 and len(mat_cols) == 1 and mat_cols[0] != matricula_1:
        matricula_2 = mat_cols[0]

    return {
        "toi": pick("toi", "tois"),
        "instalacao": pick("instalação", "instalacao", "inst.", "inst"),
        "colaborador_1": pick("colaborador 1", "colaborador_1", "colarador 1"),
        "colaborador_2": pick("colaborador 2", "colaborador_2"),
        "matricula_1": matricula_1,
        "matricula_2": matricula_2,
    }


def _first_equipe_value(row: pd.Series, columns: list[str | None], normalizer) -> str:
    for col in columns:
        if not col:
            continue
        val = normalizer(row.get(col))
        if val:
            return val
    return ""


def _read_equipe_lookup(source: str | Path) -> pd.DataFrame:
    path = Path(source)
    if not path.is_file():
        raise FileNotFoundError(f"Arquivo de equipes não encontrado: {path}")

    raw = pd.read_excel(path)
    raw.columns = [str(c).strip() for c in raw.columns]
    cols = _resolve_equipe_columns(raw)
    if not cols["toi"] or not cols["instalacao"]:
        raise ValueError("A planilha de equipes precisa conter colunas TOI e Instalação.")

    norm_map = {_normalize_header(str(c)): c for c in raw.columns}

    def cols_by(*aliases: str) -> list[str]:
        found: list[str] = []
        for alias in aliases:
            key = _normalize_header(alias)
            if key in norm_map:
                col = norm_map[key]
                if col not in found:
                    found.append(col)
        return found

    col1_candidates = cols_by("colaborador 1", "colaborador_1", "colarador 1")
    col2_candidates = cols_by("colaborador 2", "colaborador_2")
    mat1_candidates = cols_by("matrícula", "matricula", "matricula_1", "matrícula_1")
    mat2_candidates = cols_by(
        "matrícula.1",
        "matricula.1",
        "matrícula_2",
        "matricula_2",
    )

    rows: list[dict[str, str]] = []
    for _, row in raw.iterrows():
        key = _match_key(row.get(cols["toi"]), row.get(cols["instalacao"]))
        if not key:
            continue
        item = {
            "match_key": key,
            "colaborador_1": _first_equipe_value(row, col1_candidates, _normalize_nome),
            "matricula_1": _first_equipe_value(row, mat1_candidates, _normalize_matricula),
            "colaborador_2": _first_equipe_value(row, col2_candidates, _normalize_nome),
            "matricula_2": _first_equipe_value(row, mat2_candidates, _normalize_matricula),
        }
        if not any(item[field] for field in ("colaborador_1", "matricula_1", "colaborador_2", "matricula_2")):
            continue
        rows.append(item)

    if not rows:
        return pd.DataFrame(columns=["match_key", "colaborador_1", "matricula_1", "colaborador_2", "matricula_2"])

    out = pd.DataFrame(rows)
    return out.drop_duplicates(subset=["match_key"], keep="last")


def import_equipes_from_excel(
    source: str | Path,
    dest: str | Path | None = None,
) -> dict:
    """Preenche Colaborador/Matrícula faltantes na base por TOI + Instalação."""
    dest_path = Path(dest) if dest else MONITORAMENTO_FILE
    lookup_df = _read_equipe_lookup(source)
    lookup = {row["match_key"]: row for _, row in lookup_df.iterrows()}

    raw_base = _read_raw(dest_path)
    for col in MONITORAMENTO_COLUMNS:
        if col not in raw_base.columns:
            raw_base[col] = pd.NA

    field_map = (
        ("Colaborador_1", "colaborador_1", _normalize_nome),
        ("Matricula_1", "matricula_1", _normalize_matricula),
        ("Colaborador_2", "colaborador_2", _normalize_nome),
        ("Matricula_2", "matricula_2", _normalize_matricula),
    )

    matched = 0
    cells_filled = 0
    for idx, row in raw_base.iterrows():
        key = _match_key(row.get("TOI"), row.get("Instalação"))
        if not key or key not in lookup:
            continue
        matched += 1
        eq = lookup[key]
        for excel_col, field, normalizer in field_map:
            current = row.get(excel_col)
            new_val = str(eq.get(field, "") or "").strip()
            if not new_val or new_val.lower() == "nan":
                continue
            if _is_blank(current):
                raw_base.at[idx, excel_col] = normalizer(new_val) or new_val
                cells_filled += 1

    _save_raw_monitoramento(raw_base[MONITORAMENTO_COLUMNS], dest_path)
    return {
        "fonte": Path(source).name,
        "equipes_lidas": len(lookup_df),
        "registros_encontrados": matched,
        "campos_preenchidos": cells_filled,
        "nao_encontrados": max(len(lookup_df) - matched, 0),
    }


if __name__ == "__main__":
    import json

    default_sources = [
        Path(r"c:\Users\E706032\Downloads\tois com divergências alessandro.xlsx"),
        Path(r"c:\Users\E706032\Downloads\ATIVIDADES DIÁRIAS ALESSANDRO.xlsx"),
        Path(r"c:\Users\E706032\Downloads\ATIVIDADES DIÁRIAS _ LUCIANO.xlsx"),
    ]
    sources = [p for p in default_sources if p.is_file()]
    if not sources:
        raise SystemExit("Nenhum arquivo de apontamentos encontrado em Downloads.")
    result = import_apontamentos_laboratorio(sources)
    print(json.dumps(result, ensure_ascii=False, indent=2))
