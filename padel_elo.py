#!/usr/bin/env python3
"""
Sistema ELO para ranking de Padel.
Soporta partidos de dobles con jugadores que no siempre asisten.
"""

import csv
import re
from collections import defaultdict
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

# === Configuración ELO ===
INITIAL_ELO = 1500
K_FACTOR = 40  # K alto porque hay pocos partidos aún

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
19 /Mar/26,7,1,Javier / Moy,Jorge / Densopapi,5 - 6"""


def normalize_name(name: str) -> str:
    """Normaliza nombres (Denso -> Densopapi)."""
    name = name.strip()
    if name == "Denso":
        name = "Densopapi"
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
    history = defaultdict(list)  # historial de ELO por jugador

    # Para snapshots por fecha
    wins_by_date = defaultdict(lambda: defaultdict(int))
    losses_by_date = defaultdict(lambda: defaultdict(int))
    matches_by_date = defaultdict(lambda: defaultdict(int))
    snapshots_by_date = {}  # fecha -> {player: elo}
    date_order = []  # fechas en orden de aparición

    lines = MATCHES_CSV.strip().split("\n")
    reader = csv.DictReader(lines)

    prev_fecha = None
    for row in reader:
        team1 = parse_team(row["Equipo 1"])
        team2 = parse_team(row["Equipo 2"])
        score1, score2 = parse_score(row["Marcador"])
        fecha = row["Fecha"].strip()

        if fecha != prev_fecha:
            if prev_fecha is not None:
                # Guardar snapshot al terminar la fecha anterior
                snapshots_by_date[prev_fecha] = dict(elo)
            if fecha not in date_order:
                date_order.append(fecha)
            prev_fecha = fecha

        # Rating promedio de cada equipo
        avg_elo_1 = (elo[team1[0]] + elo[team1[1]]) / 2
        avg_elo_2 = (elo[team2[0]] + elo[team2[1]]) / 2

        # Resultado: 1 = equipo1 gana, 0 = equipo2 gana
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

        # Actualizar ELO de cada jugador
        delta = K_FACTOR * margin_mult * (actual_1 - expected_1)

        for p in team1:
            elo[p] += delta
            match_count[p] += 1
            matches_by_date[fecha][p] += 1
            history[p].append((fecha, round(elo[p])))

        for p in team2:
            elo[p] -= delta
            match_count[p] += 1
            matches_by_date[fecha][p] += 1
            history[p].append((fecha, round(elo[p])))

    # Guardar snapshot de la última fecha
    if prev_fecha is not None:
        snapshots_by_date[prev_fecha] = dict(elo)

    return (elo, match_count, wins, losses, history,
            snapshots_by_date, date_order, wins_by_date, losses_by_date, matches_by_date)


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
                   snapshots_by_date, date_order, wins_by_date, losses_by_date, matches_by_date):
    """Imprime rankings por fecha y el ranking final."""

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
    ranked = sorted(elo.items(), key=lambda x: x[1], reverse=True)

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


def plot_elo_evolution(elo, snapshots_by_date, date_order):
    """Grafica la evolución del ELO de cada jugador por fecha de sesión."""
    all_players = sorted(elo.keys())
    x_labels = ["Inicio"] + date_order
    x_pos = list(range(len(x_labels)))

    fig, ax = plt.subplots(figsize=(12, 7))

    colors = plt.cm.tab10.colors
    markers = ["o", "s", "^", "D", "v", "P", "*", "X", "h", "+"]

    for i, player in enumerate(all_players):
        y_values = [INITIAL_ELO]
        for fecha in date_order:
            snap = snapshots_by_date.get(fecha, {})
            y_values.append(snap.get(player, y_values[-1]))

        ax.plot(
            x_pos, y_values,
            label=player,
            color=colors[i % len(colors)],
            marker=markers[i % len(markers)],
            linewidth=2,
            markersize=7,
        )

        # Etiqueta al final de la línea
        ax.annotate(
            player,
            xy=(x_pos[-1], y_values[-1]),
            xytext=(5, 0),
            textcoords="offset points",
            va="center",
            fontsize=8,
            color=colors[i % len(colors)],
        )

    ax.set_xticks(x_pos)
    ax.set_xticklabels(x_labels, fontsize=10)
    ax.yaxis.set_minor_locator(ticker.MultipleLocator(10))
    ax.grid(True, which="major", linestyle="--", alpha=0.5)
    ax.grid(True, which="minor", linestyle=":", alpha=0.3)
    ax.axhline(INITIAL_ELO, color="gray", linestyle="--", linewidth=1, alpha=0.6, label="ELO inicial (1500)")

    ax.set_title("Evolución ELO por sesión · Padel", fontsize=14, fontweight="bold")
    ax.set_xlabel("Fecha de sesión", fontsize=11)
    ax.set_ylabel("ELO", fontsize=11)
    ax.legend(loc="upper left", fontsize=8, framealpha=0.8)

    plt.tight_layout()
    plt.savefig("elo_evolution.png", dpi=150)
    print("\n📊 Gráfica guardada en: elo_evolution.png")
    plt.show()


if __name__ == "__main__":
    results = process_matches()
    print_rankings(*results)
    plot_elo_evolution(results[0], results[5], results[6])
