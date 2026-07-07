"""Processamento e agregação dos dados de TOI."""

from __future__ import annotations

import re
from collections import Counter, defaultdict
from pathlib import Path

import pandas as pd

from config import DATA_FILE

DEVIATION_PATTERNS: list[tuple[str, str, int]] = [
    ("Sem nº Invólucro", r"sem n[uú]mero de inv[oó]lucro|sem n[uú]mero inv[oó]lucro", re.I),
    ("Nº invólucro errado", r"n[uú]mero.*inv[oó]lucro errado|inv[oó]lucro errado", re.I),
    ("CSM cortado", r"csm cortado", re.I),
    ("TOI não enviado", r"toi n[aã]o enviado", re.I),
    ("TOI ilegível", r"toi ileg[ií]vel", re.I),
    ("Faltando lacre tampa", r"faltando lacre|sem lacre da tampa", re.I),
    ("CSM não enviado", r"csm n[aã]o enviado", re.I),
    (
        "Sem lacre TOI/físico",
        r"sem lacre no toi.*(mas|por[eé]m|porem).*com lacre|sem lacre toi|sem lacre f[ií]sico|com lacre no toi.*sem",
        re.I,
    ),
    ("Nenhum doc enviado", r"nenhum documento|nenhum doc", re.I),
    ("Sem nº medidor", r"sem n[uú]mero de medidor|sem n[uú]mero medidor", re.I),
    ("Sem info lacres", r"sem info.*lacres|sem informa", re.I),
    ("Informações divergentes", r"informa[cç][oõ]es divergentes", re.I),
    ("Com lacre TOI/s/físico", r"com lacre toi.*sem|lacres? toi.*sem f[ií]sico", re.I),
    ("Lacre violado TOI", r"lacre violado", re.I),
    ("Sem dispositivo TOI", r"sem dispositivo no toi|sem dispositivo toi", re.I),
]

RANKING_ORDER = [
    "Sem nº Invólucro",
    "CSM cortado",
    "TOI não enviado",
    "Faltando lacre tampa",
    "CSM não enviado",
    "Sem lacre TOI/físico",
    "Nenhum doc enviado",
    "Sem nº medidor",
    "Sem info lacres",
    "Com lacre TOI/s/físico",
    "Lacre violado TOI",
    "Sem dispositivo TOI",
    "Nº invólucro errado",
    "TOI ilegível",
    "Informações divergentes",
]


def is_terceirizada(matricula: object) -> bool:
    return str(matricula).upper().startswith("RT")


def team_type(m1: object, m2: object) -> str:
    t1, t2 = is_terceirizada(m1), is_terceirizada(m2)
    if t1 and t2:
        return "Terceirizada"
    if not t1 and not t2:
        return "Própria"
    return "Mista"


def make_pair_key(m1: object, m2: object) -> str:
    a, b = sorted([str(m1), str(m2)])
    return f"{a} {b}"


def extract_deviations(text: object) -> list[str]:
    if pd.isna(text):
        return []
    found: list[str] = []
    for name, pattern, flags in DEVIATION_PATTERNS:
        if re.search(pattern, str(text), flags):
            found.append(name)
    return found


def _desc_column(df: pd.DataFrame) -> str:
    for col in df.columns:
        lower = col.lower()
        if "descri" in lower or "descrição" in lower.replace("", ""):
            return col
    for col in df.columns:
        if df[col].dtype == object and df[col].astype(str).str.contains(
            "invólucro|involucro|csm|lacre", case=False, na=False
        ).any():
            return col
    raise KeyError("Coluna de descrição não encontrada")


def _deviation_column(df: pd.DataFrame) -> str | None:
    for col in df.columns:
        if col.lower() in ("desvio", "desvios"):
            return col
    return None


def row_deviations(row: pd.Series, desc_col: str, dev_col: str | None) -> list[str]:
    found: list[str] = []
    for field in (desc_col, dev_col):
        if not field or field not in row.index or pd.isna(row[field]):
            continue
        for name in extract_deviations(row[field]):
            if name not in found:
                found.append(name)
    return found


def load_data(path: str | None = None) -> pd.DataFrame:
    file_path = Path(path) if path else DATA_FILE
    df = pd.read_excel(file_path)
    desc_col = _desc_column(df)
    dev_col = _deviation_column(df)

    df = df.copy()
    df = df.dropna(subset=["Matricula", "Matricula_2", "TOI"], how="any")
    df["descricao"] = df[desc_col]
    df["tipo"] = df.apply(
        lambda r: team_type(r["Matricula"], r["Matricula_2"]), axis=1
    )
    df["dupla"] = df.apply(
        lambda r: make_pair_key(r["Matricula"], r["Matricula_2"]), axis=1
    )
    df["deviations"] = df.apply(
        lambda r: row_deviations(r, desc_col, dev_col), axis=1
    )
    df["has_deviation"] = df["deviations"].apply(len) > 0
    df["mat1"] = df["Matricula"].astype(str)
    df["mat2"] = df["Matricula_2"].astype(str)
    return df


def get_deviation_df(df: pd.DataFrame | None = None) -> pd.DataFrame:
    data = df if df is not None else load_data()
    return data[data["has_deviation"]].copy()


def toi_summary(df: pd.DataFrame | None = None) -> dict:
    data = df if df is not None else load_data()
    toi_flags = data.groupby("TOI")["has_deviation"].any()
    com = int(toi_flags.sum())
    sem = int((~toi_flags).sum())
    total = com + sem
    return {
        "total": total,
        "com_desvio": com,
        "sem_desvio": sem,
        "pct_com": round(com / total * 100, 1) if total else 0,
        "pct_sem": round(sem / total * 100, 1) if total else 0,
    }


def deviation_ranking(df: pd.DataFrame | None = None) -> pd.DataFrame:
    dev_df = get_deviation_df(df)
    counter: Counter[str] = Counter()
    for devs in dev_df["deviations"]:
        counter.update(devs)

    rows = []
    for name in RANKING_ORDER:
        if name in counter:
            rows.append({"tipo": name, "count": counter[name]})
    for name, count in counter.most_common():
        if name not in RANKING_ORDER:
            rows.append({"tipo": name, "count": count})

    return pd.DataFrame(rows)


def team_comparison(df: pd.DataFrame | None = None, top_n: int = 6) -> pd.DataFrame:
    dev_df = get_deviation_df(df)
    rows = []
    for tipo in ["Própria", "Terceirizada"]:
        sub = dev_df[dev_df["tipo"] == tipo]
        total = len(sub)
        if total == 0:
            continue
        counter: Counter[str] = Counter()
        for devs in sub["deviations"]:
            counter.update(devs)
        for dev_type in RANKING_ORDER[:top_n]:
            rows.append(
                {
                    "tipo_desvio": dev_type,
                    "equipe": tipo,
                    "count": counter.get(dev_type, 0),
                    "pct": round(counter.get(dev_type, 0) / total * 100, 1),
                }
            )
    return pd.DataFrame(rows)


def top_duplas(df: pd.DataFrame | None = None, n: int = 12) -> pd.DataFrame:
    dev_df = get_deviation_df(df)
    grouped = (
        dev_df.groupby(["dupla", "tipo", "Matricula", "Matricula_2"])
        .size()
        .reset_index(name="tois")
        .sort_values("tois", ascending=False)
        .head(n)
    )
    total_dev = len(dev_df)
    grouped["pct_total"] = (grouped["tois"] / total_dev * 100).round(1)

    predominant = []
    for _, row in grouped.iterrows():
        sub = dev_df[dev_df["dupla"] == row["dupla"]]
        counter: Counter[str] = Counter()
        for devs in sub["deviations"]:
            counter.update(devs)
        predominant.append(counter.most_common(3))
    grouped["predominantes"] = predominant
    return grouped.reset_index(drop=True)


def dupla_deviation_profile(
    df: pd.DataFrame | None = None, n: int = 6
) -> tuple[list[str], pd.DataFrame]:
    dev_df = get_deviation_df(df)
    top = (
        dev_df.groupby("dupla")
        .size()
        .sort_values(ascending=False)
        .head(n)
        .index.tolist()
    )

    profile_types = [
        "CSM cortado",
        "TOI não enviado",
        "Sem nº Invólucro",
        "Faltando lacre tampa",
        "CSM não enviado",
    ]
    rows = []
    for dupla in top:
        sub = dev_df[dev_df["dupla"] == dupla]
        counter: Counter[str] = Counter()
        for devs in sub["deviations"]:
            counter.update(devs)
        row: dict = {"dupla": dupla}
        for pt in profile_types:
            row[pt] = counter.get(pt, 0)
        rows.append(row)
    return top, pd.DataFrame(rows)


def individual_appearances(df: pd.DataFrame | None = None) -> pd.DataFrame:
    dev_df = get_deviation_df(df)
    counter: Counter[str] = Counter()
    tipo_map: dict[str, str] = {}

    for _, row in dev_df.iterrows():
        for mat in [row["mat1"], row["mat2"]]:
            counter[mat] += 1
            if mat not in tipo_map:
                tipo_map[mat] = "Terceirizada" if is_terceirizada(mat) else "Própria"

    rows = [
        {"matricula": m, "count": c, "tipo": tipo_map[m]}
        for m, c in counter.most_common()
    ]
    return pd.DataFrame(rows)


def top_individuals_by_type(
    df: pd.DataFrame | None = None, n: int = 8
) -> tuple[pd.DataFrame, pd.DataFrame]:
    ind = individual_appearances(df)
    propria = ind[ind["tipo"] == "Própria"].head(n).reset_index(drop=True)
    terc = ind[ind["tipo"] == "Terceirizada"].head(n).reset_index(drop=True)
    return propria, terc


def city_breakdown(df: pd.DataFrame | None = None) -> pd.DataFrame:
    dev_df = get_deviation_df(df)
    rows = []
    for cidade, sub in dev_df.groupby("CIDADE"):
        propria = (sub["tipo"] == "Própria").sum()
        terc = (sub["tipo"] == "Terceirizada").sum()
        mista = (sub["tipo"] == "Mista").sum()
        total = len(sub)
        if propria >= terc:
            pred = "Própria"
            pred_pct = round(propria / total * 100) if total else 0
        else:
            pred = "Terceirizada"
            pred_pct = round(terc / total * 100) if total else 0
        rows.append(
            {
                "cidade": cidade,
                "propria": int(propria),
                "terceirizada": int(terc),
                "mista": int(mista),
                "total": int(total),
                "predominancia": pred,
                "pred_pct": pred_pct,
            }
        )
    return pd.DataFrame(rows).sort_values("total", ascending=False)


def person_pattern_cards(df: pd.DataFrame | None = None, n: int = 3) -> list[dict]:
    """Identifica padrões 'Erro segue a PESSOA' vs 'Parceiro influencia'."""
    dev_df = get_deviation_df(df)
    ind = individual_appearances(df)
    candidates = ind.head(30)["matricula"].tolist()

    pessoa_cards: list[dict] = []
    parceiro_cards: list[dict] = []

    for mat in candidates:
        records = dev_df[(dev_df["mat1"] == mat) | (dev_df["mat2"] == mat)]
        if len(records) < 3:
            continue

        partner_totals: dict[str, int] = defaultdict(int)
        partner_dev_types: dict[str, Counter[str]] = defaultdict(Counter)

        for _, row in records.iterrows():
            partner = row["mat2"] if row["mat1"] == mat else row["mat1"]
            partner_totals[partner] += 1
            partner_dev_types[partner].update(row["deviations"])

        unique_partners = sorted(
            [
                {
                    "parceiro": p,
                    "deviations": ", ".join(
                        f"{d} ×{c}" for d, c in partner_dev_types[p].most_common(2)
                    )
                    or "—",
                    "total": partner_totals[p],
                }
                for p in partner_totals
            ],
            key=lambda x: x["total"],
            reverse=True,
        )

        all_top_types = [
            c.most_common(1)[0][0] if c else None
            for c in partner_dev_types.values()
        ]
        unique_tops = set(t for t in all_top_types if t)

        if len(unique_tops) == 1 and len(partner_dev_types) >= 2:
            dominant = unique_tops.pop()
            card = {
                "matricula": mat,
                "tipo": "Terceirizada" if is_terceirizada(mat) else "Própria",
                "insight": "Erro segue a PESSOA",
                "descricao": (
                    f'"{dominant}" em TODOS os {len(partner_dev_types)} parceiros '
                    "— independe de quem trabalha junto."
                ),
                "parceiros": unique_partners[:5],
            }
            pessoa_cards.append(card)
        elif len(unique_tops) >= 2:
            card = {
                "matricula": mat,
                "tipo": "Terceirizada" if is_terceirizada(mat) else "Própria",
                "insight": "Parceiro influencia",
                "descricao": (
                    "Tipos de erro mudam com cada parceiro — "
                    "desvio vem do outro membro."
                ),
                "parceiros": unique_partners[:5],
            }
            parceiro_cards.append(card)

    # Mix: prefer diversity of insight types
    result: list[dict] = []
    if parceiro_cards:
        result.append(parceiro_cards[0])
    for card in pessoa_cards:
        if len(result) >= n:
            break
        if card["matricula"] not in [c["matricula"] for c in result]:
            result.append(card)
    for card in parceiro_cards[1:] + pessoa_cards:
        if len(result) >= n:
            break
        if card["matricula"] not in [c["matricula"] for c in result]:
            result.append(card)
    return result[:n]


def kpi_metrics(df: pd.DataFrame | None = None) -> dict:
    data = df if df is not None else load_data()
    dev_df = get_deviation_df(data)
    summary = toi_summary(data)
    return {
        "total_registros": len(data),
        "tois_unicos": data["TOI"].nunique(),
        "tois_com_desvio": summary["com_desvio"],
        "tois_sem_desvio": summary["sem_desvio"],
        "total_ocorrencias": sum(deviation_ranking(data)["count"]),
        "cidades": data["CIDADE"].nunique(),
        "duplas": dev_df["dupla"].nunique(),
    }
