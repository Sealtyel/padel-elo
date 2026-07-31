#!/usr/bin/env python3
"""
Sistema ELO para ranking de Padel.
Soporta partidos de dobles con jugadores que no siempre asisten.
"""

import csv
import json
import re
from collections import defaultdict
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

# === Configuración ELO ===
INITIAL_ELO = 1500
K_FACTOR = 40  # K alto porque hay pocos partidos aún

# === Filtros de jugadores (players.json) ===
def load_player_config():
    try:
        with open("players.json") as f:
            data = json.load(f)
        return data.get("players", {})
    except FileNotFoundError:
        return {}

def visible_in_chart(player, config):
    return config.get(player, {}).get("chart", True)

def visible_in_ranking(player, config):
    return config.get(player, {}).get("ranking", True)

# === Datos de partidos ===
MATCHES_CSV = """Fecha,Ronda,Pista,Equipo 1,Equipo 2,Marcador
3 /Mar/26,1,1,Daniel / Pável,Alfredo / Javier,3 - 2
3 /Mar/26,1,2,Densopapi / Jorge,Francisco / Guillermo,5 - 0
3 /Mar/26,2,1,Javier / Oscar,Guillermo / Jorge,3 - 2
3 /Mar/26,2,2,Daniel / Francisco,Alfredo / Moy,1 - 4
3 /Mar/26,3,1,Densopapi / Oscar,Francisco / Moy,4 - 1
3 /Mar/26,3,2,Alfredo / Guillermo,Jorge / Pável,4 - 1
3 /Mar/26,4,1,Alfredo / Pável,Moy / Oscar,1 - 4
3 /Mar/26,4,2,Densopapi / Francisco,Daniel / Javier,1 - 4
3 /Mar/26,5,1,Javier / Moy,Guillermo / Pável,4 - 1
3 /Mar/26,5,2,Daniel / Densopapi,Jorge / Oscar,3 - 2
3 /Mar/26,6,1,Javier / Jorge,Daniel / Moy,1 - 4
3 /Mar/26,6,2,Alfredo / Francisco,Guillermo / Oscar,3 - 2
3 /Mar/26,7,1,Francisco / Jorge,Moy / Pável,0 - 5
3 /Mar/26,7,2,Densopapi / Javier,Alfredo / Oscar,4 - 1
3 /Mar/26,8,1,Alfredo / Densopapi,Jorge / Moy,3 - 2
3 /Mar/26,8,2,Francisco / Pável,Daniel / Guillermo,1 - 4
3 /Mar/26,9,1,Oscar / Pável,Daniel / Jorge,2 - 3
3 /Mar/26,9,2,Guillermo / Javier,Densopapi / Moy,0 - 5
3 /Mar/26,10,1,Alfredo / Daniel,Densopapi / Guillermo,5 - 0
3 /Mar/26,10,2,Francisco / Oscar,Javier / Pável,2 - 3
19 /Mar/26,1,1,Moy / Francisco,Densopapi / Jorge,0 - 5
19 /Mar/26,2,1,Moy / Densopapi,Francisco / Javier,5 - 0
19 /Mar/26,3,1,Moy / Jorge,Javier / Densopapi,3 - 2
19 /Mar/26,4,1,Moy / Javier,Francisco / Jorge,4 - 1
19 /Mar/26,5,1,Densopapi / Francisco,Jorge / Javier,1 - 4
19 /Mar/26,6,1,Jorge / Javier,Moy / Densopapi,1 - 6
19 /Mar/26,7,1,Javier / Moy,Jorge / Densopapi,5 - 6
26 /Mar/26,1,1,Moy / Javier,Jorge / Oscar,3 - 2
26 /Mar/26,2,1,Densopapi / Moy,Javier / Jorge,4 - 1
26 /Mar/26,3,1,Densopapi / Javier,Moy / Oscar,1 - 4
26 /Mar/26,4,1,Densopapi / Jorge,Javier / Oscar,3 - 2
26 /Mar/26,5,1,Densopapi / Oscar,Moy / Jorge,4 - 1
26 /Mar/26,6,1,Densopapi / Oscar,Moy / Jorge,6 - 1
26 /Mar/26,7,1,Densopapi / Jorge,Moy / Javier,2 - 3
1 /Apr/26,1,1,Moy / Javier,Densopapi / Jorge,6 - 5
1 /Apr/26,2,1,Moy / Javier,Densopapi / Jorge,5 - 6
1 /Apr/26,3,1,Moy / Javier,Densopapi / Jorge,6 - 3
1 /Apr/26,4,1,Moy / Javier,Densopapi / Jorge,3 - 1
17 /Apr/26,1,1,Guillermo / Daniel,Jorge / Javier,5 - 0
17 /Apr/26,1,2,Densopapi / Igor,Oscar / Ivan,3 - 2
17 /Apr/26,1,3,Alfredo / Roy,Manuel / Franco,2 - 3
17 /Apr/26,2,1,Guillermo / Densopapi,Daniel / Igor,2 - 3
17 /Apr/26,2,2,Jorge / Manuel,Javier / Franco,0 - 5
17 /Apr/26,2,3,Francisco / Oscar,Moy / Ivan,2 - 3
17 /Apr/26,3,1,Daniel / Franco,Igor / Javier,3 - 2
17 /Apr/26,3,2,Guillermo / Ivan,Densopapi / Moy,0 - 5
17 /Apr/26,3,3,Manuel / Alfredo,Jorge / Roy,4 - 1
17 /Apr/26,4,1,Daniel / Densopapi,Franco / Moy,4 - 1
17 /Apr/26,4,2,Igor / Manuel,Javier / Alfredo,2 - 3
17 /Apr/26,4,3,Francisco / Ivan,Oscar / Guillermo,0 - 5
17 /Apr/26,5,1,Daniel / Javier,Densopapi / Alfredo,3 - 2
17 /Apr/26,5,2,Franco / Guillermo,Moy / Oscar,0 - 5
17 /Apr/26,5,3,Manuel / Jorge,Igor / Roy,5 - 0
17 /Apr/26,6,1,Daniel / Oscar,Javier / Moy,3 - 2
17 /Apr/26,6,2,Densopapi / Jorge,Alfredo / Manuel,4 - 1
17 /Apr/26,6,3,Francisco / Franco,Ivan / Guillermo,2 - 3
17 /Apr/26,7,1,Densopapi / Oscar,Jorge / Daniel,2 - 3
17 /Apr/26,7,2,Javier / Guillermo,Moy / Ivan,1 - 4
17 /Apr/26,7,3,Francisco / Alfredo,Roy / Igor,3 - 2
17 /Apr/26,8,1,Ivan / Daniel,Moy / Oscar,2 - 3
17 /Apr/26,8,2,Densopapi / Javier,Alfredo / Guillermo,4 - 1
28 /Apr/26,1,1,Oscar / Igor,Javier / Jorge,3 - 2
28 /Apr/26,1,2,Alfredo / Marco,David / Manuel,4 - 1
28 /Apr/26,1,3,Densopapi / Moy,Daniel / Alonso,1 - 4
28 /Apr/26,2,1,Oscar / Alfredo,Igor / Marco,2 - 3
28 /Apr/26,2,2,Daniel / Jorge,Alonso / Javier,4 - 1
28 /Apr/26,2,3,Ivan / Manuel,Chayito / David,4 - 1
28 /Apr/26,3,1,Igor / Jorge,Marco / Daniel,1 - 4
28 /Apr/26,3,2,Oscar / Ivan,Alfredo / Manuel,2 - 3
28 /Apr/26,3,3,Densopapi / Alonso,Moy / Javier,2 - 3
28 /Apr/26,4,1,Marco / Manuel,Daniel / Alfredo,0 - 5
28 /Apr/26,4,2,Moy / Igor,Javier / Jorge,5 - 0
28 /Apr/26,4,3,Chayito / Ivan,David / Oscar,0 - 5
28 /Apr/26,5,1,Daniel / Igor,Alfredo / Moy,3 - 2
28 /Apr/26,5,2,Manuel / Ivan,Oscar / Marco,1 - 4
28 /Apr/26,5,3,Densopapi / Jorge,Alonso / Javier,2 - 3
28 /Apr/26,6,1,Daniel / Oscar,Igor / Marco,5 - 0
28 /Apr/26,6,2,Alfredo / Alonso,Moy / Javier,1 - 4
28 /Apr/26,6,3,Chayito / Manuel,David / Ivan,1 - 4
7 /May/26,1,1,Moy / Oscar,Franco / Manuel,4 - 1
7 /May/26,1,2,Densopapi / Marco,Javier / Jorge,2 - 3
7 /May/26,2,1,Moy / Franco,Oscar / Roy,4 - 1
7 /May/26,2,2,Densopapi / Javier,Marco / Chayito,4 - 1
7 /May/26,3,1,Moy / Manuel,Franco / Roy,4 - 1
7 /May/26,3,2,Densopapi / Jorge,Javier / Chayito,4 - 1
7 /May/26,4,1,Moy / Roy,Oscar / Manuel,3 - 2
7 /May/26,4,2,Densopapi / Chayito,Marco / Jorge,2 - 3
7 /May/26,5,1,Oscar / Franco,Manuel / Roy,5 - 0
7 /May/26,5,2,Marco / Javier,Jorge / Chayito,4 - 1
7 /May/26,6,1,Moy / Manuel,Oscar / Franco,4 - 6
7 /May/26,6,2,Oscar / Franco,Densopapi / Jorge,7 - 5
7 /May/26,7,1,Oscar / Jorge,Densopapi / Javier,2 - 6
15 /May/26,1,1,Moy / Franco,Igor / Jorge,3 - 2
15 /May/26,1,2,Densopapi / Javier,Marco / Manuel,3 - 2
15 /May/26,2,1,Moy / Igor,Franco / Francisco,5 - 0
15 /May/26,2,2,Densopapi / Marco,Javier / Angel,4 - 1
15 /May/26,3,1,Moy / Jorge,Igor / Francisco,5 - 0
15 /May/26,3,2,Densopapi / Manuel,Marco / Angel,2 - 3
15 /May/26,4,1,Moy / Francisco,Franco / Jorge,2 - 3
15 /May/26,4,2,Densopapi / Angel,Javier / Manuel,5 - 0
15 /May/26,5,1,Franco / Igor,Jorge / Francisco,2 - 3
15 /May/26,5,2,Javier / Marco,Manuel / Angel,5 - 0
15 /May/26,6,1,Franco / Jorge,Moy / Roy,5 - 7
15 /May/26,6,2,Javier / Denso,Marco / Angel,6 - 3
15 /May/26,7,1,Densopapi / Javier,Moy / Igor,6 - 4
15 /May/26,7,2,Densopapi / Francisco,Manuel / Marco,4 - 1
21 /May/26,1,1,Javier / Franco,Manuel / Densopapi,4 - 1
21 /May/26,1,2,Moy / Jorge,Marco / Igor,4 - 1
21 /May/26,2,1,Javier / Densopapi,Manuel / Chayito,5 - 0
21 /May/26,2,2,Moy / Marco,Jorge / Ivan,4 - 1
21 /May/26,3,1,Javier / Chayito,Franco / Densopapi,1 - 4
21 /May/26,3,2,Moy / Igor,Marco / Ivan,4 - 1
21 /May/26,4,1,Franco / Manuel,Densopapi / Chayito,1 - 4
21 /May/26,4,2,Moy / Ivan,Jorge / Igor,4 - 1
21 /May/26,5,1,Javier / Manuel,Franco / Chayito,3 - 2
21 /May/26,5,2,Jorge / Marco,Igor / Ivan,2 - 3
21 /May/26,6,1,Franco / Javier,Densopapi / Chayito,6 - 2
21 /May/26,6,2,Jorge / Moy,Igor / Ivan,6 - 0
21 /May/26,7,2,Javier / Franco,Moy / Jorge,3 - 6
21 /May/26,8,2,Moy / Javier,Jorge / Densopapi,6 - 7
28 /May/26,1,1,Alfredo / Ivan,Manuel / Chayito,5 - 0
28 /May/26,1,2,Densopapi / Moy,Javier / Jorge,3 - 2
28 /May/26,2,1,Alfredo / Manuel,Ivan / Chayito,3 - 2
28 /May/26,2,2,Densopapi / Javier,Moy / Jorge,5 - 0
28 /May/26,3,1,Alfredo / Chayito,Ivan / Manuel,3 - 2
28 /May/26,3,2,Moy / Javier,Densopapi / Jorge,3 - 2
28 /May/26,4,2,Alfredo / Chayito,Moy / Javier,0 - 6
28 /May/26,5,1,Moy / Javier,Jorge / Densopapi,1 - 6
28 /May/26,6,1,Jorge / Densopapi,Ivan / Manuel,6 - 1
28 /May/26,7,1,Ivan / Densopapi,Jorge / Javier,3 - 1
28 /May/26,8,1,Ivan / Densopapi,Moy / Javier,1 - 3
28 /May/26,9,1,Jorge / Densopapi,Moy / Javier,3 - 1
5 /Jun/26,1,1,Moy / Javier,Ivan / Jorge,2 - 3
5 /Jun/26,2,1,Moy / Ivan,Igor / Densopapi,2 - 3
5 /Jun/26,3,1,Igor / Javier,Densopapi / Jorge,1 - 4
5 /Jun/26,4,1,Moy / Igor,Densopapi / Ivan,3 - 2
5 /Jun/26,5,1,Igor / Jorge,Densopapi / Javier,2 - 3
5 /Jun/26,6,1,Moy / Jorge,Ivan / Javier,4 - 1
5 /Jun/26,7,1,Ivan / Densopapi,Jorge / Javier,3 - 0
5 /Jun/26,8,1,Ivan / Densopapi,Moy / Igor,3 - 1
5 /Jun/26,9,1,Javier / Jorge,Moy / Igor,0 - 3
5 /Jun/26,10,1,Ivan / Densopapi,Moy / Igor,3 - 2
5 /Jun/26,11,1,Jorge / Javier,Ivan / Densopapi,3 - 2
5 /Jun/26,12,1,Moy / Densopapi,Javier / Jorge,3 - 1
12 /Jun/26,1,1,Moy / Alfredo,Jorge / Chayito,5 - 0
12 /Jun/26,1,2,Oscar / Densopapi,Manuel / Javier,3 - 2
12 /Jun/26,2,1,Moy / Franco,Igor / Chayito,3 - 2
12 /Jun/26,2,2,Densopapi / Marco,Oscar / Javier,2 - 3
12 /Jun/26,3,1,Alfredo / Franco,Moy / Jorge,0 - 5
12 /Jun/26,3,2,Marco / Javier,Manuel / Oscar,3 - 2
12 /Jun/26,4,1,Jorge / Alfredo,Franco / Igor,5 - 0
12 /Jun/26,4,2,Manuel / Densopapi,Oscar / Marco,3 - 2
12 /Jun/26,5,1,Moy / Chayito,Igor / Alfredo,4 - 1
12 /Jun/26,5,2,Javier / Denso,Manuel / Marco,4 - 1
12 /Jun/26,6,1,Jorge / Igor,Franco / Chayito,4 - 1
12 /Jun/26,6,2,Igor / Moy,Alfredo / Jorge,3 - 2
12 /Jun/26,7,1,Moy / Igor,Oscar / Denso,3 - 4
26 /Jun/26,1,1,Densopapi / Daniel,Ivan / Marco,4 - 1
26 /Jun/26,1,2,Chayito / Igor,Moy / Manuel,3 - 2
26 /Jun/26,2,1,Densopapi / Marco,Javier / Alfredo,1 - 4
26 /Jun/26,2,2,Chayito / Moy,Manuel / Oscar,2 - 3
26 /Jun/26,3,1,Daniel / Javier,Ivan / Alfredo,3 - 2
26 /Jun/26,3,2,Chayito / Manuel,Igor / Oscar,1 - 4
26 /Jun/26,4,1,Densopapi / Ivan,Daniel / Marco,2 - 3
26 /Jun/26,4,2,Chayito / Oscar,Igor / Moy,0 - 5
26 /Jun/26,5,1,Densopapi / Javier,Daniel / Alfredo,1 - 4
26 /Jun/26,5,2,Igor / Manuel,Moy / Oscar,0 - 5
26 /Jun/26,6,1,Ivan / Javier,Marco / Alfredo,5 - 0
26 /Jun/26,6,2,Oscar / Chayito,Igor / Moy,0 - 5
26 /Jun/26,7,1,Daniel / Ivan,Alfredo / Javier,3 - 2
26 /Jun/26,8,1,Daniel / Ivan,Moy / Igor,4 - 3
1 /Jul/26,1,1,Moy / Javier,Alfredo / Igor,3 - 2
1 /Jul/26,1,2,Densopapi / Chayito,Jorge / Ivan,1 - 4
1 /Jul/26,2,1,Moy / Alfredo,Javier / Manuel,3 - 2
1 /Jul/26,2,2,Densopapi / Jorge,Chayito / Marco,4 - 1
1 /Jul/26,3,1,Moy / Igor,Alfredo / Manuel,5 - 0
1 /Jul/26,3,2,Densopapi / Ivan,Jorge / Marco,3 - 2
1 /Jul/26,4,1,Moy / Manuel,Javier / Igor,4 - 1
1 /Jul/26,4,2,Densopapi / Marco,Chayito / Ivan,4 - 1
1 /Jul/26,5,1,Javier / Alfredo,Igor / Manuel,3 - 2
1 /Jul/26,5,2,Chayito / Jorge,Ivan / Marco,0 - 5
1 /Jul/26,6,2,Marco / Densopapi,Ivan / Jorge,6 - 2
1 /Jul/26,7,1,Moy / Igor,Marco / Densopapi,6 - 3
1 /Jul/26,7,2,Javier / Alfredo,Jorge / Ivan,4 - 6
9 /Jul/26,1,1,Marco / Manuel,Chayito / Densopapi,4 - 1
9 /Jul/26,1,2,Franco / Igor,Ivan / Javier,1 - 4
9 /Jul/26,2,1,Moy / Densopapi,Chayito / Manuel,4 - 1
9 /Jul/26,2,2,Franco / Ivan,Igor / Jorge,3 - 2
9 /Jul/26,3,1,Moy / Marco,Manuel / Densopapi,3 - 2
9 /Jul/26,3,2,Franco / Javier,Ivan / Jorge,1 - 4
9 /Jul/26,4,1,Chayito / Marco,Manuel / Moy,0 - 5
9 /Jul/26,4,2,Franco / Jorge,Igor / Javier,3 - 2
9 /Jul/26,5,1,Chayito / Moy,Densopapi / Marco,1 - 4
9 /Jul/26,5,2,Igor / Ivan,Javier / Jorge,3 - 2
9 /Jul/26,6,1,Densopapi / Moy,Marco / Manuel,6 - 0
9 /Jul/26,6,2,Javier / Ivan,Jorge / Franco,6 - 0
9 /Jul/26,7,2,Densopapi / Moy,Javier / Ivan,6 - 2
9 /Jul/26,8,2,Densopapi / Ivan,Jorge / Javier,6 - 2
31 /Jul/26,1,1,Densopapi / Chayito,Jose / Alfredo,2 - 3
31 /Jul/26,1,2,Moy / Ivan,Javier / Jorge,3 - 2
31 /Jul/26,2,1,Moy / Jose,Ivan / Alfredo,1 - 4
31 /Jul/26,2,2,Densopapi / Jorge,Chayito / Javier,4 - 1
31 /Jul/26,3,1,Densopapi / Ivan,Jorge / Alfredo,4 - 1
31 /Jul/26,3,2,Chayito / Moy,Javier / Jose,1 - 4
31 /Jul/26,4,1,Densopapi / Javier,Ivan / Jose,3 - 2
31 /Jul/26,4,2,Alfredo / Oscar,Moy / Jorge,1 - 4
31 /Jul/26,5,1,Densopapi / Jorge,Javier / Moy,3 - 2
31 /Jul/26,5,2,Oscar / Ivan,Chayito / Jose,5 - 0
31 /Jul/26,6,1,Densopapi / Oscar,Jorge / Ivan,5 - 0
31 /Jul/26,6,2,Chayito / Javier,Alfredo / Moy,1 - 4
31 /Jul/26,7,1,Moy / Oscar,Alfredo / Densopapi,2 - 3
31 /Jul/26,7,2,Chayito / Jose,Ivan / Javier,0 - 5
31 /Jul/26,8,1,Javier / Alfredo,Ivan / Densopapi,1 - 4
31 /Jul/26,8,2,Jose / Moy,Oscar / Chayito,3 - 2
31 /Jul/26,9,1,Jose / Densopapi,Ivan / Moy,4 - 1"""


def normalize_name(name: str) -> str:
    """Normaliza nombres (Denso -> Densopapi)."""
    name = name.strip()
    if name == "Denso":
        name = "Densopapi"
    if name == "Chayito":
        name = "Francisco"
    return name


def parse_team(team_str: str) -> list[str]:
    """Extrae los dos jugadores de un equipo."""
    # Soporta "A / B" y "A/B"
    players = re.split(r'\s*/\s*', team_str.strip())
    return [normalize_name(p) for p in players]


def parse_score(score_str: str) -> tuple[int, int]:
    """Extrae los games de cada equipo."""
    parts = score_str.strip().split("-")
    return int(parts[0].strip()), int(parts[1].strip())


def expected_score(rating_a: float, rating_b: float) -> float:
    """Probabilidad esperada de que A gane."""
    return 1.0 / (1.0 + 10 ** ((rating_b - rating_a) / 400))


def compute_margin_multiplier(score_winner: int, score_loser: int) -> float:
    """
    Multiplier basado en la diferencia de marcador.
    Una victoria 5-0 pesa más que una 3-2.
    """
    diff = score_winner - score_loser
    total = score_winner + score_loser
    if total == 0:
        return 1.0
    return 1.0 + (diff / total) * 0.5


def process_matches():
    """Procesa todos los partidos y calcula ELO."""
    elo = defaultdict(lambda: INITIAL_ELO)
    match_count = defaultdict(int)
    wins = defaultdict(int)
    losses = defaultdict(int)
    # history entry: (fecha, elo_after, partner, score_str, won, match_idx)
    history = defaultdict(list)

    # Para snapshots por fecha
    wins_by_date = defaultdict(lambda: defaultdict(int))
    losses_by_date = defaultdict(lambda: defaultdict(int))
    matches_by_date = defaultdict(lambda: defaultdict(int))
    snapshots_by_date = {}  # fecha -> {player: elo}
    date_order = []  # fechas en orden de aparición
    date_start_index = {}  # fecha -> match_idx donde empieza

    lines = MATCHES_CSV.strip().split("\n")
    reader = csv.DictReader(lines)

    prev_fecha = None
    match_idx = 0
    for row in reader:
        team1 = parse_team(row["Equipo 1"])
        team2 = parse_team(row["Equipo 2"])
        score1, score2 = parse_score(row["Marcador"])
        fecha = row["Fecha"].strip()

        if fecha != prev_fecha:
            if prev_fecha is not None:
                snapshots_by_date[prev_fecha] = dict(elo)
            if fecha not in date_order:
                date_order.append(fecha)
                date_start_index[fecha] = match_idx
            prev_fecha = fecha

        avg_elo_1 = (elo[team1[0]] + elo[team1[1]]) / 2
        avg_elo_2 = (elo[team2[0]] + elo[team2[1]]) / 2

        if score1 > score2:
            actual_1 = 1.0
            margin_mult = compute_margin_multiplier(score1, score2)
            for p in team1:
                wins[p] += 1
                wins_by_date[fecha][p] += 1
            for p in team2:
                losses[p] += 1
                losses_by_date[fecha][p] += 1
        else:
            actual_1 = 0.0
            margin_mult = compute_margin_multiplier(score2, score1)
            for p in team2:
                wins[p] += 1
                wins_by_date[fecha][p] += 1
            for p in team1:
                losses[p] += 1
                losses_by_date[fecha][p] += 1

        expected_1 = expected_score(avg_elo_1, avg_elo_2)
        delta = K_FACTOR * margin_mult * (actual_1 - expected_1)

        for p in team1:
            elo[p] += delta
            match_count[p] += 1
            matches_by_date[fecha][p] += 1
            partner = team1[1] if p == team1[0] else team1[0]
            won = score1 > score2
            history[p].append((fecha, round(elo[p]), partner, " & ".join(team2), score1, score2, won, match_idx))

        for p in team2:
            elo[p] -= delta
            match_count[p] += 1
            matches_by_date[fecha][p] += 1
            partner = team2[1] if p == team2[0] else team2[0]
            won = score2 > score1
            history[p].append((fecha, round(elo[p]), partner, " & ".join(team1), score2, score1, won, match_idx))

        match_idx += 1

    if prev_fecha is not None:
        snapshots_by_date[prev_fecha] = dict(elo)

    return (elo, match_count, wins, losses, history,
            snapshots_by_date, date_order, wins_by_date, losses_by_date, matches_by_date,
            date_start_index, match_idx)


def print_date_ranking(fecha, snapshot, wins_date, losses_date, matches_date, prev_snapshot=None):
    """Imprime el ranking de una fecha específica."""
    # Solo jugadores que participaron ese día
    players_today = set(matches_date.keys())
    # Todos los jugadores conocidos hasta esa fecha
    all_players = set(snapshot.keys())

    ranked = sorted(snapshot.items(), key=lambda x: x[1], reverse=True)

    print(f"\n{'#':<4} {'Jugador':<15} {'ELO':>6} {'Δ':>6} {'Día W':>6} {'Día L':>6} {'Asistió':>8}")
    print("-" * 55)

    for i, (player, rating) in enumerate(ranked, 1):
        played = "✅" if player in players_today else "❌"
        w = wins_date.get(player, 0)
        l = losses_date.get(player, 0)

        # Calcular delta respecto al snapshot anterior o al ELO inicial
        if prev_snapshot and player in prev_snapshot:
            delta = rating - prev_snapshot[player]
        else:
            delta = rating - INITIAL_ELO

        delta_str = f"+{delta:.0f}" if delta >= 0 else f"{delta:.0f}"

        medal = ""
        if i == 1:
            medal = " 🥇"
        elif i == 2:
            medal = " 🥈"
        elif i == 3:
            medal = " 🥉"

        w_str = str(w) if player in players_today else "-"
        l_str = str(l) if player in players_today else "-"

        print(f"{i:<4} {player:<15} {rating:>6.0f} {delta_str:>6} {w_str:>6} {l_str:>6} {played:>8}{medal}")


def print_rankings(elo, match_count, wins, losses, history,
                   snapshots_by_date, date_order, wins_by_date, losses_by_date, matches_by_date,
                   player_config=None):
    """Imprime rankings por fecha y el ranking final."""
    if player_config is None:
        player_config = {}

    # === Rankings por fecha ===
    prev_snapshot = None
    for fecha in date_order:
        snapshot = snapshots_by_date[fecha]
        players_today = set(matches_by_date[fecha].keys())

        print("=" * 70)
        print(f"📅  RANKING DESPUÉS DE: {fecha}  ({len(players_today)} jugadores)")
        print("=" * 70)

        print_date_ranking(
            fecha, snapshot,
            wins_by_date[fecha], losses_by_date[fecha], matches_by_date[fecha],
            prev_snapshot
        )
        prev_snapshot = snapshot

    # === Ranking acumulado final ===
    ranked = sorted(
        [(p, r) for p, r in elo.items() if visible_in_ranking(p, player_config)],
        key=lambda x: x[1], reverse=True
    )

    print("\n" + "=" * 70)
    print("🏆  RANKING ELO FINAL - PADEL (ACUMULADO)")
    print("=" * 70)
    print(f"\n{'#':<4} {'Jugador':<15} {'ELO':>6} {'W':>4} {'L':>4} {'Win%':>6} {'Partidos':>9} {'Sesiones':>9}")
    print("-" * 62)

    # Contar sesiones por jugador
    sessions = defaultdict(int)
    for fecha in date_order:
        for p in matches_by_date[fecha]:
            sessions[p] += 1

    for i, (player, rating) in enumerate(ranked, 1):
        w = wins[player]
        l = losses[player]
        total = match_count[player]
        win_pct = (w / total * 100) if total > 0 else 0

        medal = ""
        if i == 1:
            medal = " 🥇"
        elif i == 2:
            medal = " 🥈"
        elif i == 3:
            medal = " 🥉"

        print(f"{i:<4} {player:<15} {rating:>6.0f} {w:>4} {l:>4} {win_pct:>5.1f}% {total:>9} {sessions[player]:>8}{medal}")

    print()

    # Estadísticas adicionales
    print("=" * 70)
    print("📊  ESTADÍSTICAS ADICIONALES")
    print("=" * 70)

    changes = [(p, elo[p] - INITIAL_ELO) for p in elo]
    changes.sort(key=lambda x: x[1], reverse=True)

    print(f"\n  Mayor subida:  {changes[0][0]} (+{changes[0][1]:.0f})")
    print(f"  Mayor bajada:  {changes[-1][0]} ({changes[-1][1]:.0f})")

    # Evolución ELO por jugador
    print("\n📈  Evolución ELO por jugador:")
    for player in sorted(elo.keys()):
        elos_str = "1500"
        for fecha in date_order:
            snap = snapshots_by_date[fecha]
            if player in snap:
                elos_str += f" → {snap[player]:.0f}"
        print(f"  {player:<15} {elos_str}")

    print()


def plot_elo_evolution(elo, history, date_order, date_start_index, total_matches, player_config=None):
    """Grafica la evolución del ELO partido a partido con hover interactivo."""
    if player_config is None:
        player_config = {}
    all_players = sorted(p for p in elo.keys() if visible_in_chart(p, player_config))
    colors = plt.cm.tab10.colors
    markers = ["o", "s", "^", "D", "v", "P", "*", "X", "h", "+"]

    fig, ax = plt.subplots(figsize=(14, 8))

    # Líneas separadoras entre sesiones
    for fecha in date_order:
        x = date_start_index[fecha] - 0.5
        if x > -0.5:
            ax.axvline(x, color="gray", linestyle="--", linewidth=0.8, alpha=0.5)

    # Etiquetas de fecha en el centro de cada sesión
    date_list = list(date_order)
    for k, fecha in enumerate(date_list):
        start = date_start_index[fecha]
        end = date_start_index[date_list[k + 1]] if k + 1 < len(date_list) else total_matches
        mid = (start + end - 1) / 2
        ax.text(mid, 1200, fecha.strip(), ha="center", fontsize=8, color="gray", alpha=0.8)

    scatter_list = []
    final_points = []

    for i, player in enumerate(all_players):
        color = colors[i % len(colors)]
        marker = markers[i % len(markers)]
        h = history[player]

        x_vals = [0]
        y_vals = [INITIAL_ELO]
        tooltips = []

        for entry in h:
            fecha, elo_val, partner, rivals, my_score, their_score, won, midx = entry
            x_vals.append(midx + 1)
            y_vals.append(elo_val)
            my_tag  = "[W]" if won else "[L]"
            opp_tag = "[L]" if won else "[W]"
            tooltips.append(
                f"{my_tag}  {player} & {partner}  {my_score}\n"
                f"{opp_tag}  {rivals}  {their_score}\n"
                f"ELO: {elo_val}"
            )

        ax.plot(x_vals, y_vals, color=color, linewidth=1.5, alpha=0.8)

        sc = ax.scatter(x_vals[1:], y_vals[1:],
                        color=color, marker=marker, s=55, zorder=5)
        sc._player_tooltips = tooltips
        scatter_list.append(sc)

        # Guardar punto final para las etiquetas del lado derecho
        final_points.append((y_vals[-1], x_vals[-1], player, color))

    # --- Etiquetas derechas con separación anti-overlap ---
    MIN_GAP = 18  # puntos de ELO mínimos entre etiquetas
    final_points.sort(key=lambda t: t[0], reverse=True)

    label_y = [p[0] for p in final_points]
    # Empujar hacia abajo las etiquetas que se solapan
    for i in range(1, len(label_y)):
        if label_y[i - 1] - label_y[i] < MIN_GAP:
            label_y[i] = label_y[i - 1] - MIN_GAP

    x_end = max(p[1] for p in final_points)
    x_label = x_end + 0.6

    for (actual_y, x_last, player, color), adj_y in zip(final_points, label_y):
        # Línea conectora desde el punto final a la etiqueta
        ax.plot([x_last, x_label - 0.2], [actual_y, adj_y],
                color=color, linewidth=0.6, alpha=0.5, clip_on=False)
        ax.text(x_label, adj_y, f"{player}  {actual_y:.0f}",
                va="center", fontsize=8, color=color,
                fontweight="bold", clip_on=False)

    # Ampliar el margen derecho para que quepan las etiquetas
    ax.set_xlim(right=x_end + 1)

    # Tooltip único reutilizable
    annot = ax.annotate(
        "", xy=(0, 0), xytext=(12, 12), textcoords="offset points",
        bbox=dict(boxstyle="round,pad=0.4", fc="white", alpha=0.9, edgecolor="gray"),
        fontsize=9, zorder=10,
    )
    annot.set_visible(False)

    def on_move(event):
        if event.inaxes != ax:
            if annot.get_visible():
                annot.set_visible(False)
                fig.canvas.draw_idle()
            return

        hit_any = False
        for sc in scatter_list:
            cont, ind = sc.contains(event)
            if cont:
                idx = ind["ind"][0]
                pos = sc.get_offsets()[idx]
                annot.xy = pos
                annot.set_text(sc._player_tooltips[idx])

                # Ajustar offset para que no se salga del gráfico
                x_frac = (event.xdata - ax.get_xlim()[0]) / (ax.get_xlim()[1] - ax.get_xlim()[0])
                y_frac = (event.ydata - ax.get_ylim()[0]) / (ax.get_ylim()[1] - ax.get_ylim()[0])
                x_off = -90 if x_frac > 0.75 else 12
                y_off = -55 if y_frac > 0.75 else 12
                annot.set_position((x_off, y_off))

                annot.set_visible(True)
                hit_any = True
                break

        if not hit_any and annot.get_visible():
            annot.set_visible(False)

        fig.canvas.draw_idle()

    fig.canvas.mpl_connect("motion_notify_event", on_move)

    ax.axhline(INITIAL_ELO, color="gray", linestyle="--", linewidth=1, alpha=0.5)
    ax.yaxis.set_minor_locator(ticker.MultipleLocator(10))
    ax.grid(True, which="major", linestyle="--", alpha=0.4)
    ax.grid(True, which="minor", linestyle=":", alpha=0.2)
    ax.set_title("Evolución ELO por partido · Padel", fontsize=14, fontweight="bold")
    ax.set_xlabel("Partido #", fontsize=11)
    ax.set_ylabel("ELO", fontsize=11)
    ax.legend(loc="upper left", fontsize=8, framealpha=0.8)

    plt.tight_layout()
    plt.savefig("elo_evolution.png", dpi=150)
    print("\n📊 Gráfica guardada en: elo_evolution.png")
    plt.show()


if __name__ == "__main__":
    player_config = load_player_config()
    results = process_matches()
    print_rankings(*results[:10], player_config=player_config)
    plot_elo_evolution(results[0], results[4], results[6], results[10], results[11], player_config=player_config)
