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
19 /Mar/26,7,1,Javier / Moy,Jorge / Densopapi,5 - 6
26 /Mar/26,1,1,Moy / Javier,Jorge / Oscar,3 - 2
26 /Mar/26,2,1,Densopapi / Moy,Javier / Jorge,4 - 1
26 /Mar/26,3,1,Densopapi / Javier,Moy / Oscar,1 - 4
26 /Mar/26,4,1,Densopapi / Jorge,Javier / Oscar,3 - 2
26 /Mar/26,5,1,Densopapi / Oscar,Moy / Jorge,4 - 1
26 /Mar/26,6,1,Densopapi / Oscar,Moy / Jorge,6 - 1
26 /Mar/26,7,1,Densopapi / Jorge,Moy / Javier,2 - 3"""


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


def plot_elo_evolution(elo, history, date_order, date_start_index, total_matches):
    """Grafica la evolución del ELO partido a partido con hover interactivo."""
    all_players = sorted(elo.keys())
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
    results = process_matches()
    print_rankings(*results[:10])
    plot_elo_evolution(results[0], results[4], results[6], results[10], results[11])
