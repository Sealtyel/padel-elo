# Padel ELO

Sistema de ranking ELO para torneos de pádel de dobles. Calcula y visualiza la evolución del rating de cada jugador a lo largo de las sesiones.

---

## ¿Qué es ELO?

ELO es un sistema de rating que estima la fuerza relativa de los jugadores. Originalmente diseñado para ajedrez, funciona así:

- Cada jugador empieza con **1500 puntos**.
- Antes de cada partido, el sistema predice el resultado en base a la diferencia de ratings entre equipos.
- Si ganas contra un rival mejor rankeado, **sumas más puntos** que si ganas contra alguien peor.
- Si pierdes contra alguien de menor rating, **pierdes más puntos**.
- Con el tiempo, el ELO converge hacia el nivel real de cada jugador.

### Cómo se calcula aquí

1. **Rating de equipo**: se promedia el ELO de los dos jugadores del equipo.
2. **Probabilidad esperada** usando la fórmula estándar:

   ```
   E(A) = 1 / (1 + 10^((ELO_B - ELO_A) / 400))
   ```

3. **Multiplicador por margen**: una victoria 5-0 pesa más que una 3-2.

   ```
   multiplicador = 1 + (diferencia / total_games) × 0.5
   ```

4. **Delta ELO** aplicado a cada jugador del equipo:

   ```
   Δ = K × multiplicador × (resultado - esperado)
   ```

   Donde `K = 40` (factor alto porque hay pocos partidos).

---

## Cómo correr el proyecto

### Requisitos

- Python 3.10+
- `matplotlib`

```bash
pip install matplotlib
```

### Ejecutar

```bash
python3 padel_elo.py
```

---

## Output

El script produce dos tipos de salida:

### 1. Consola — Rankings por sesión

Después de cada fecha de juego, muestra una tabla con el ELO actualizado, la variación respecto a la sesión anterior, y el resultado del día (victorias/derrotas):

```
======================================================================
📅  RANKING DESPUÉS DE: 3/Mar/26  (10 jugadores)
======================================================================
#    Jugador          ELO      Δ   Día W   Día L  Asistió
-------------------------------------------------------
1    Moy             1605    +105       7       3       ✅ 🥇
2    Daniel          1583     +83       6       4       ✅ 🥈
...
```

### 2. Consola — Ranking final acumulado

Tabla global con ELO total, victorias, derrotas, porcentaje de victorias, partidos jugados y sesiones asistidas:

```
======================================================================
🏆  RANKING ELO FINAL - PADEL (ACUMULADO)
======================================================================
#    Jugador          ELO     W    L   Win%  Partidos  Sesiones
--------------------------------------------------------------
1    Moy             1605    13    7  65.0%        20         2 🥇
...
```

### 3. Consola — Estadísticas adicionales

- Mayor subida y bajada de ELO total.
- Evolución numérica por jugador: `1500 → 1563 → 1605`.

### 4. Gráfica — `elo_evolution.png`

Una gráfica de líneas con la evolución del ELO de cada jugador sesión a sesión, guardada automáticamente en el directorio del proyecto.

![Ejemplo de gráfica ELO](elo_evolution.png?v=11)

---

## Resultados

Los resultados de los partidos están registrados en el siguiente spreadsheet:

[📊 Resultados Padel](https://docs.google.com/spreadsheets/d/1lnZlkSRlh7VjVhLlCfvkIZWXSgJMMqoK693xAvxxh3o/edit?gid=408319547#gid=408319547)

### 3/Mar/26

| # | Jugador | ELO |
|---|---------|-----|
| 🥇 | Daniel | 1634 |
| 🥈 | Moy | 1600 |
| 🥉 | Densopapi | 1591 |
| 4 | Alfredo | 1554 |
| 5 | Javier | 1546 |
| 6 | Oscar | 1458 |
| 7 | Pável | 1446 |
| 8 | Jorge | 1412 |
| 9 | Guillermo | 1402 |
| 10 | Francisco | 1357 |

### 19/Mar/26

| # | Jugador | ELO |
|---|---------|-----|
| 🥇 | Daniel | 1634 |
| 🥈 | Densopapi | 1630 |
| 🥉 | Moy | 1625 |
| 4 | Alfredo | 1554 |
| 5 | Javier | 1497 |
| 6 | Jorge | 1480 |
| 7 | Oscar | 1458 |
| 8 | Pável | 1446 |
| 9 | Guillermo | 1402 |
| 10 | Francisco | 1274 |

### 26/Mar/26

| # | Jugador | ELO |
|---|---------|-----|
| 🥇 | Densopapi | 1667 |
| 🥈 | Moy | 1653 |
| 🥉 | Daniel | 1634 |
| 4 | Alfredo | 1554 |
| 5 | Oscar | 1505 |
| 6 | Javier | 1475 |
| 7 | Pável | 1446 |
| 8 | Guillermo | 1402 |
| 9 | Jorge | 1390 |
| 10 | Francisco | 1274 |

### 1/Apr/26

| # | Jugador | ELO |
|---|---------|-----|
| 🥇 | Moy | 1689 |
| 🥈 | Daniel | 1634 |
| 🥉 | Densopapi | 1631 |
| 4 | Alfredo | 1554 |
| 5 | Javier | 1510 |
| 6 | Oscar | 1505 |
| 7 | Pável | 1446 |
| 8 | Guillermo | 1402 |
| 9 | Jorge | 1355 |
| 10 | Francisco | 1274 |

### 17/Apr/26

| # | Jugador | ELO |
|---|---------|-----|
| 🥇 | Daniel | 1761 |
| 🥈 | Moy | 1729 |
| 🥉 | Densopapi | 1669 |
| 4 | Oscar | 1542 |
| 5 | Alfredo | 1525 |
| 6 | Javier | 1518 |
| 7 | Manuel | 1503 |
| 8 | Franco | 1501 |
| 9 | Ivan | 1467 |
| 10 | Pável | 1446 |
| 11 | Igor | 1435 |
| 12 | Roy | 1395 |
| 13 | Jorge | 1384 |
| 14 | Guillermo | 1379 |
| 15 | Francisco | 1247 |

### 28/Apr/26

| # | Jugador | ELO |
|---|---------|-----|
| 🥇 | Daniel | 1879 |
| 🥈 | Moy | 1735 |
| 🥉 | Densopapi | 1595 |
| 4 | Oscar | 1569 |
| 5 | Marco | 1548 |
| 6 | Alfredo | 1523 |
| 7 | Javier | 1523 |
| 8 | Franco | 1501 |
| 9 | David | 1494 |
| 10 | Igor | 1492 |
| 11 | Alonso | 1491 |
| 12 | Manuel | 1460 |
| 13 | Pável | 1446 |
| 14 | Ivan | 1442 |
| 15 | Roy | 1395 |
| 16 | Guillermo | 1379 |
| 17 | Jorge | 1336 |
| 18 | Francisco | 1192 |

### 7/May/26

| # | Jugador | ELO |
|---|---------|-----|
| 🥇 | Daniel | 1879 |
| 🥈 | Moy | 1773 |
| 🥉 | Oscar | 1592 |
| 4 | Densopapi | 1581 |
| 5 | Javier | 1577 |
| 6 | Franco | 1553 |
| 7 | Marco | 1532 |
| 8 | Alfredo | 1523 |
| 9 | David | 1494 |
| 10 | Igor | 1492 |
| 11 | Alonso | 1491 |
| 12 | Pável | 1446 |
| 13 | Ivan | 1442 |
| 14 | Manuel | 1395 |
| 15 | Guillermo | 1379 |
| 16 | Roy | 1361 |
| 17 | Jorge | 1356 |
| 18 | Francisco | 1134 |

### 15/May/26

| # | Jugador | ELO |
|---|---------|-----|
| 🥇 | Daniel | 1879 |
| 🥈 | Moy | 1774 |
| 🥉 | Densopapi | 1694 |
| 4 | Javier | 1606 |
| 5 | Oscar | 1592 |
| 6 | Marco | 1535 |
| 7 | Alfredo | 1523 |
| 8 | Franco | 1521 |
| 9 | David | 1494 |
| 10 | Alonso | 1491 |
| 11 | Angel | 1480 |
| 12 | Pável | 1446 |
| 13 | Ivan | 1442 |
| 14 | Igor | 1423 |
| 15 | Jorge | 1402 |
| 16 | Guillermo | 1379 |
| 17 | Roy | 1377 |
| 18 | Manuel | 1287 |
| 19 | Francisco | 1157 |

### 21/May/26

| # | Jugador | ELO |
|---|---------|-----|
| 🥇 | Daniel | 1879 |
| 🥈 | Moy | 1839 |
| 🥉 | Densopapi | 1731 |
| 4 | Javier | 1599 |
| 5 | Oscar | 1592 |
| 6 | Alfredo | 1523 |
| 7 | Franco | 1505 |
| 8 | David | 1494 |
| 9 | Alonso | 1491 |
| 10 | Marco | 1486 |
| 11 | Angel | 1480 |
| 12 | Pável | 1446 |
| 13 | Jorge | 1442 |
| 14 | Ivan | 1433 |
| 15 | Igor | 1416 |
| 16 | Guillermo | 1379 |
| 17 | Roy | 1377 |
| 18 | Manuel | 1253 |
| 19 | Francisco | 1134 |

### 28/May/26

| # | Jugador | ELO |
|---|---------|-----|
| 🥇 | Daniel | 1879 |
| 🥈 | Densopapi | 1832 |
| 🥉 | Moy | 1788 |
| 4 | Oscar | 1592 |
| 5 | Javier | 1568 |
| 6 | Alfredo | 1566 |
| 7 | Franco | 1505 |
| 8 | Jorge | 1452 |
| 9 | Igor | 1416 |
| 10 | Ivan | 1396 |
| 11 | Guillermo | 1379 |
| 12 | Roy | 1377 |
| 13 | Manuel | 1228 |
| 14 | Francisco | 1126 |

### 5/Jun/26

| # | Jugador | ELO |
|---|---------|-----|
| 🥇 | Densopapi | 1887 |
| 🥈 | Daniel | 1879 |
| 🥉 | Moy | 1760 |
| 4 | Oscar | 1592 |
| 5 | Alfredo | 1566 |
| 6 | Franco | 1505 |
| 7 | Javier | 1498 |
| 8 | Jorge | 1488 |
| 9 | Igor | 1419 |
| 10 | Ivan | 1401 |
| 11 | Guillermo | 1379 |
| 12 | Roy | 1377 |
| 13 | Manuel | 1228 |
| 14 | Francisco | 1126 |

### 12/Jun/26

| # | Jugador | ELO |
|---|---------|-----|
| 🥇 | Densopapi | 1903 |
| 🥈 | Daniel | 1879 |
| 🥉 | Moy | 1826 |
| 4 | Oscar | 1601 |
| 5 | Javier | 1548 |
| 6 | Alfredo | 1527 |
| 7 | Jorge | 1525 |
| 8 | Franco | 1448 |
| 9 | Marco | 1446 |
| 10 | Ivan | 1401 |
| 11 | Igor | 1382 |
| 12 | Guillermo | 1379 |
| 13 | Roy | 1377 |
| 14 | Manuel | 1222 |
| 15 | Francisco | 1126 |

### 26/Jun/26

| # | Jugador | ELO |
|---|---------|-----|
| 🥇 | Daniel | 1970 |
| 🥈 | Densopapi | 1824 |
| 🥉 | Moy | 1777 |
| 4 | Oscar | 1615 |
| 5 | Javier | 1584 |
| 6 | Alfredo | 1530 |
| 7 | Jorge | 1525 |
| 8 | Ivan | 1435 |
| 9 | Igor | 1427 |
| 10 | Franco | 1448 |
| 11 | Marco | 1394 |
| 12 | Guillermo | 1379 |
| 13 | Roy | 1377 |
| 14 | Manuel | 1201 |
| 15 | Francisco | 1103 |

---

## Agregar partidos

Los resultados están en la variable `MATCHES_CSV` dentro del script. Cada fila sigue este formato:

```
Fecha,Ronda,Pista,Equipo 1,Equipo 2,Marcador
19/Mar/26,1,1,Jugador A / Jugador B,Jugador C / Jugador D,4 - 2
```

Agrega nuevas filas al final del CSV para incluir sesiones futuras.
