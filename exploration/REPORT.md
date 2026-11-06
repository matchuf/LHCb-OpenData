# Inventario de archivos ROOT

Generado por explore_root.py; los ROOT se abren solo en lectura.

| Archivo | Árbol | Entradas | Variables | Eventos únicos leídos |
|---|---|---:|---:|---:|
| job0.root | GetIntegratedLuminosity/LumiTuple | 1 | 2 |  |
| job1.root | B02Ks2mupmum/DecayTree | 4 | 501 | 4 |
| job1.root | GetIntegratedLuminosity/LumiTuple | 1 | 2 |  |
| job2.root | B02K0mupmum/DecayTree | 3042 | 498 | 2609 |
| job2.root | GetIntegratedLuminosity/LumiTuple | 1 | 2 |  |
| job3.root | B02Ks2mupmum/DecayTree | 1 | 501 | 1 |
| job3.root | GetIntegratedLuminosity/LumiTuple | 1 | 2 |  |
| job4.root | B02Ks2mupmum/DecayTree | 5 | 501 | 5 |
| job4.root | GetIntegratedLuminosity/LumiTuple | 1 | 2 |  |
| job5.root | B02K0mupmum/DecayTree | 2989 | 498 | 2592 |
| job5.root | GetIntegratedLuminosity/LumiTuple | 1 | 2 |  |
| job6.root | B02K0mupmum/DecayTree | 805 | 498 | 674 |
| job6.root | GetIntegratedLuminosity/LumiTuple | 1 | 2 |  |
| job7.root | B02K0mupmum/DecayTree | 864 | 498 | 751 |
| job7.root | GetIntegratedLuminosity/LumiTuple | 1 | 2 |  |

Las entradas de DecayTree son candidatos. Los eventos únicos se cuentan con (runNumber, eventNumber) dentro de cada archivo y muestra leída.

Estadísticas e histogramas: primeras N entradas, sin cortes adicionales, sin pesos y sin excluir posibles centinelas.
Los arrays se aplanan para estadísticas/histogramas: PV cuenta vértices y COV cuenta elementos de matriz, no candidatos.
Los esquemas y números de entradas describen el árbol completo. first_entries.json contiene las primeras cinco filas.

Cada carpeta de árbol contiene branches.csv, statistics.csv, histograms.csv, summary.json y first_entries.json.
Los DecayTree incluyen overview.png y derived_m_mumu.csv, si están disponibles los cuadrimomentos.
