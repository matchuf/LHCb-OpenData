Test production results from the LHCb Open Data project following a request for Dark Matter search analysis.

Production configuration files:
info.yaml,		
B02K0mupmum.yaml,		
B02Ks2mupmum.yaml,

Production knowledge graphs:
B02K0mupmum.html,
B02Ks2mupmum.html

Test production results:
job0.root,
job1.root,
job2.root,
job3.root,
job4.root,
job5.root,
job6.root,
job7.root,
test-results.md

## Initial ROOT exploration

[Guía en español](EXPLORACION.md): estructura de los árboles, familias de variables,
hallazgos iniciales e instrucciones para repetir la exploración en lxplus.

- [Inventario de los ocho archivos](exploration/REPORT.md)
- [Distribuciones iniciales de job2](exploration/job2/B02K0mupmum__DecayTree/overview.png)
- [Explorador reproducible](explore_root.py)

Con Python 3 y un entorno virtual activo:

```bash
python -m pip install -r requirements-exploration.txt
python explore_root.py --max-entries 0
```

Esta orden lee todas las entradas de las pequeñas muestras de prueba. Para archivos
grandes, omite `--max-entries 0` para explorar las primeras 50000 entradas por árbol.
Los archivos ROOT se abren solo en lectura. Los resultados se guardan en `exploration/`.
