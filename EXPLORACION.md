# Primera exploración de los ntuples de LHCb

Se inspeccionaron los ocho ROOT locales completos con `python explore_root.py --max-entries 0`.
Los resultados describen estas muestras, no el conjunto completo de datos disponible en CERN.
`README.md` y `test-results.md` indican que son resultados de una producción de prueba.
No se aplicaron cortes adicionales ni pesos; las selecciones de producción ya están incorporadas.

## Qué contiene cada archivo

| Archivo | Año / imán según info.yaml | DecayTree | Candidatos | Variables | Eventos distintos dentro del archivo |
|---|---|---|---:|---:|---:|
| job0.root | 2011 / MagUp | Ausente | — | — | — |
| job1.root | 2012 / MagDown | B02Ks2mupmum/DecayTree | 4 | 501 | 4 |
| job2.root | 2012 / MagDown | B02K0mupmum/DecayTree | 3042 | 498 | 2609 |
| job3.root | 2012 / MagDown | B02Ks2mupmum/DecayTree | 1 | 501 | 1 |
| job4.root | 2012 / MagUp | B02Ks2mupmum/DecayTree | 5 | 501 | 5 |
| job5.root | 2012 / MagUp | B02K0mupmum/DecayTree | 2989 | 498 | 2592 |
| job6.root | 2017 / MagDown | B02K0mupmum/DecayTree | 805 | 498 | 674 |
| job7.root | 2017 / MagUp | B02K0mupmum/DecayTree | 864 | 498 | 751 |

Todos contienen `GetIntegratedLuminosity/LumiTuple`: una fila con
`IntegratedLuminosity` e `IntegratedLuminosityErr`, ambas `double`.
`job0.root` no contiene un árbol de candidatos; su ausencia por sí sola no demuestra corrupción
ni identifica la causa. Harían falta los registros de producción para explicarla.

Las configuraciones corresponden a dos selecciones diferentes:

- `B02K0mupmum.yaml`: línea `B2KstTauTau_MuMu_Line`, descriptor
  `[B0 -> (K*(892)0 -> K+ pi-) mu+ mu-]CC`; prefijos `B0`, `Kst_892_0`,
  `Kplus`, `piminus`, `muplus`, `muminus`.
- `B02Ks2mupmum.yaml`: línea `B2KpiX2MuMuDDDarkBosonLine`, descriptor
  `[B0 -> (KS0 -> mu+ mu-) K+ pi-]CC`; prefijos `B0`, `KS0`,
  `muplus`, `muminus`, `Kplus`, `piminus`.

El uso de `KS0` en este descriptor es la etiqueta del candidato dimuónico de esa
configuración. No basta para concluir que los candidatos sean decaimientos físicos
de un kaón neutro. `CC` incluye el canal conjugado de carga: los nombres de las ramas
no sustituyen la consulta de las variables `*_ID`.

Incluso entre los archivos de 2012 existen versiones de stripping diferentes; están
registradas en `info.yaml` y en `exploration/inventory.csv`. Antes de unir muestras,
hay que revisar esquema, selección, año, polaridad y posibles eventos compartidos.

## Cómo están almacenados los datos

La jerarquía observada es archivo ROOT → directorio → TTree → ramas.
Por ejemplo:

```text
job2.root
├── B02K0mupmum
│   └── DecayTree                 3042 filas de candidatos, 498 ramas
└── GetIntegratedLuminosity
    └── LumiTuple                 1 fila, 2 ramas
```

Un `TTree` almacena columnas independientes, llamadas ramas (`TBranch`), en bloques
comprimidos llamados baskets. Se pueden leer solo las columnas necesarias.
El sufijo `;1` que muestra ROOT es el ciclo del objeto, no un evento ni otro canal.
Véase la [documentación de árboles de ROOT](https://root.cern/manual/trees/).

En los árboles de 498 variables hay 305 `double`, 21 `int32_t`, 13 matrices
`float[3][3]`, 138 `bool`, 7 `uint32_t`, 4 `uint64_t`, 1 `int16_t` y
9 listas `float[]`. Los árboles de 501 tienen tres `double` adicionales en el conteo
por tipos; los prefijos de la partícula intermedia también cambian.

- Escalar: `B0_PT`, un número por candidato.
- Matriz fija: `B0_ENDVERTEX_COV_`, una matriz 3×3 por candidato.
- Lista de longitud variable: `PVX`, `PVY`, etc.; su contador es `nPV`.
- Identificador: `eventNumber` es `uint64_t`; debe conservarse como entero.

Las filas son candidatos reconstruidos. Por ejemplo, `job2.root` tiene 3042 filas
pero 2609 pares distintos `(runNumber, eventNumber)`, y 336 eventos con varias filas.
`nCandidate` y `totCandidates` ayudan a estudiar esa multiplicidad.
Los conteos de eventos se han realizado por archivo; no se comprobó aquí el solapamiento entre archivos.

## Cómo empezar a leer las variables

| Familia | Ejemplos presentes | Qué explorar |
|---|---|---|
| Cinemática | `B0_M`, `B0_MM`, `B0_P`, `B0_PT`, `muplus_PX`, `muplus_PE` | Masas, momento, momento transversal, componentes y energía |
| Geometría | `B0_ENDVERTEX_*`, `B0_OWNPV_*`, `B0_IPCHI2_OWNPV`, `B0_FDCHI2_OWNPV`, `B0_DIRA_OWNPV` | Vértices, compatibilidad con el vértice primario, desplazamiento y dirección |
| Tiempo propio | `B0_TAU`, `B0_TAUERR`, `B0_TAUCHI2` | Tiempo ajustado, incertidumbre y calidad |
| Identificación | `Kplus_PIDK`, `muplus_PIDmu`, `*_ProbNN*`, `*_isMuon` | Respuesta de identificación y disponibilidad |
| Trigger | `B0_L0Global_*`, `B0_Hlt1Phys_*`, `B0_Hlt2Phys_*` | Decisiones y categorías TIS/TOS |
| Evento | `runNumber`, `eventNumber`, `Polarity`, `nPV`, `PVX`, `totCandidates` | Identidad, condiciones, vértices y multiplicidad |

`OWNPV` señala el vértice primario asociado al candidato; `ORIVX` su vértice de origen;
`ENDVERTEX` su vértice final. `DIRA` es un coseno de alineación.
TIS y TOS describen el disparo independiente de la señal y el disparo debido a la señal;
véase la [introducción al trigger de LHCb](https://github.com/lhcb/starterkit-lessons/blob/master/second-analysis-steps/hlt-intro.md).
Los [TupleTools](https://lhcb.github.io/starterkit-lessons/first-analysis-steps/add-tupletools.html)
explican cómo se llenan estas familias.

Las gráficas conservan las unidades almacenadas. Las convenciones habituales de DaVinci
son MeV para energía y masa con c=1, MeV/c para momento, mm para posiciones y ns para tiempo;
la configuración local no incluye un diccionario explícito de unidades. Confirma estas
convenciones con las herramientas de la versión DaVinci/v46r11 antes de hacer conversiones físicas.
No se presupone que `M` y `MM` sean idénticas: en estos archivos difieren.

## Hallazgos iniciales y gráficas

Abre `exploration/job2/B02K0mupmum__DecayTree/overview.png` para empezar.
Hay una lámina equivalente por cada archivo con `DecayTree`. Las ordenadas usan
escala symlog para muestras de al menos 100 valores: lineal cerca de cero y logarítmica
para los conteos mayores. Cada panel cuenta candidatos, salvo histogramas de arrays,
que cuentan sus elementos cuando se solicitan con `--all-plots`.

1. `job2` ofrece estadística suficiente para aprender la estructura: `B0_M` va de
   1500.7 a 9690.6 en las unidades guardadas. El nombre `B0` es una hipótesis de
   reconstrucción; no implica una muestra pura de mesones B0.
2. Hay posibles valores centinela. En `job2`, `Kplus_PIDd` y `Kplus_ProbNNd`
   valen siempre −1000; `Kplus_ProbNNmu` tiene 2842 valores −1000 de 3042.
   La existencia de una rama no garantiza que tenga información utilizable.
   El explorador cuenta −1000, −999 y −1 sin eliminarlos automáticamente;
   −1 puede ser válido, por ejemplo en `Polarity`.
3. No se encontraron NaN/inf en las ramas leídas ni discrepancias entre las longitudes
   de las listas PV y `nPV`. Eso verifica consistencia de lectura, no validez física de cada valor.
4. Las selecciones `B02Ks2mupmum` suman solo diez candidatos en los tres archivos
   que contienen `DecayTree`. Sirven para inspeccionar variables y filas; tienen
   muy poca estadística para estudiar formas de distribuciones.
5. La masa dimuónica calculada usa
   `m² = (E_muplus + E_muminus)² − |p_muplus + p_muminus|²`, con c=1.
   Se guarda en `derived_m_mumu.csv`; no se encontraron m² negativos.
   En la selección con `KS0`, la masa calculada con las hijas difiere de `KS0_M`
   hasta 63.38 unidades en estas muestras. Revisa convenciones de ajuste y transporte
   de los momentos antes de intercambiar ambas definiciones de masa.
6. En `job6` y `job7`, `IntegratedLuminosityErr` coincide numéricamente con
   `IntegratedLuminosity`. Conviene aclarar ese metadato antes de usarlo para normalizar.

## Repetir la exploración en lxplus

Copia `explore_root.py`, `requirements-exploration.txt` e `info.yaml` junto a los ROOT
de tu copia. Desde esa carpeta, con Python 3 disponible:

```bash
python3 -m venv .venv-exploration
source .venv-exploration/bin/activate
python -m pip install -r requirements-exploration.txt
python explore_root.py --max-entries 0
```

La última orden lee todas las entradas. Es apropiada para estas pequeñas muestras;
para archivos grandes comienza con el límite predeterminado de 50000 filas:

```bash
python explore_root.py '/ruta/a/datos/job*.root' --output exploration_sample
```

No se ha ejecutado nada en tu cuenta lxplus desde este chat. El script se probó
con los ocho archivos locales; `exploration/versions.json` registra las versiones usadas.
No requiere instalar CERN ROOT: usa Uproot, NumPy, Awkward y Matplotlib.

Para producir una imagen por cada variable numérica, además de las láminas:

```bash
python explore_root.py job2.root --output exploration_all --all-plots
```

Esta opción produce aproximadamente 500 imágenes por árbol de candidatos.
En cualquier ejecución se generan los histogramas de todas las ramas numéricas
en `histograms.csv`, aunque no se soliciten sus PNG individuales.

## Inspección interactiva en Python

Con el entorno anterior activo:

```python
import uproot
import awkward as ak

f = uproot.open('job2.root', handler=uproot.source.file.MemmapSource)
print(f.classnames())
t = f['B02K0mupmum/DecayTree']
print(t.num_entries)
t.show()                         # nombres, tipos e interpretación
print(t.keys(filter_name='B0_*'))
print(t.arrays(['runNumber', 'eventNumber', 'B0_M', 'B0_PT'], entry_stop=5))
pv = t.arrays(['nPV', 'PVX'], entry_stop=5)
print(ak.to_list(pv))             # listas de vértices por candidato
```

Para producción grande, selecciona columnas y usa `t.iterate(...)` por bloques;
no leas todas las ramas de todos los archivos simultáneamente.
Véase la [guía de Uproot](https://uproot.readthedocs.io/en/stable/basic.html).

Si ya tienes un entorno con CERN ROOT disponible en lxplus, puedes inspeccionar
el mismo archivo directamente, sin el script:

```cpp
// Dentro de root -l
auto f = TFile::Open("job2.root");
f->ls();
auto t = f->Get<TTree>("B02K0mupmum/DecayTree");
t->Print();
t->Scan("runNumber:eventNumber:B0_M:B0_PT", "", "", 10);
t->Draw("B0_M");
```

## Productos de esta exploración

`exploration/REPORT.md` contiene el inventario; `objects.csv` lista los objetos ROOT;
`schemas.json` conserva los nombres y tipos por árbol, y `summary.json` reúne los controles.
Cada subcarpeta de árbol contiene:

- `branches.csv`: nombre, tipo, forma, categoría, contador, bytes y baskets.
- `statistics.csv`: mínimo, percentiles, máximo, media, dispersión, valores distintos,
  valores no finitos y conteos de posibles centinelas.
- `histograms.csv`: frecuencias exactas para variables con hasta doce valores distintos;
  para el resto, 50 bins que abarcan el rango completo finito.
- `first_entries.json`: primeras cinco filas con arrays y matrices conservados.
- `summary.json`: conteos, tipos y controles de lectura de ese árbol.
- `overview.png` y `derived_m_mumu.csv` en los árboles de candidatos.

Los identificadores enteros se conservan en las filas y en el conteo de eventos.
Las estadísticas continuas y los bordes de histogramas pueden usar punto flotante;
no sirven para reconstruir la identidad exacta de un evento.
Las estadísticas de matrices y listas aplanan todos sus elementos; para estudiar
un elemento de covarianza concreto, selecciona ese índice explícitamente.

El primer objetivo puede darse por cubierto cuando puedas localizar ambos tipos de
árbol, reconocer las familias de variables, distinguir candidato de evento, leer las
estructuras variables y justificar qué variables y definiciones usarás después.
