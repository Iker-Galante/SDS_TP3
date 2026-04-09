# TP3 - Scanning Rate en Recinto Cerrado con Obstáculo Fijo

Simulación de Dinámica Molecular Dirigida por Eventos (EDMD) para partículas en movimiento rectilíneo uniforme dentro de un recinto circular con un obstáculo fijo central.

## Estructura del Proyecto

```
SDS_TP3/
├── simulation/          # Proyecto Java (Maven) - Motor de simulación EDMD
│   ├── pom.xml
│   └── src/main/java/ar/edu/itba/sds/
│       ├── Main.java
│       ├── EventDrivenMD.java
│       ├── Particle.java
│       ├── Event.java
│       ├── CollisionCalculator.java
│       └── OutputWriter.java
├── analysis/            # Scripts Python - Análisis y visualización
│   ├── visualize.py            # Animaciones con OVITO
│   ├── ex1_execution_time.py   # Ej 1.1: Tiempo de ejecución vs N
│   ├── ex2_scanning_rate.py    # Ej 1.2: Scanning rate J(N)
│   ├── ex3_fraction_used.py    # Ej 1.3: Fracción de partículas usadas
│   └── ex4_radial_profiles.py  # Ej 1.4: Perfiles radiales
├── output/              # Archivos de salida (generados)
├── requirements.txt     # Dependencias Python
├── run.sh              # Script helper para ejecutar todo
└── README.md
```

## Requisitos

- **Java 17+** (Maven 3.9+)
- **Python 3.10+** con `uv` para gestión de entorno virtual
- **OVITO** (opcional, para animaciones)

## Setup

### 1. Compilar la simulación Java

```bash
cd simulation
mvn clean package -q
cd ..
```

### 2. Crear entorno virtual Python

```bash
uv venv .venv
uv pip install -r requirements.txt
```

## Ejecución

### Simulación individual

```bash
java -jar simulation/target/tp3-scanning-rate-1.0-SNAPSHOT.jar \
    -N 100 -tf 50 -dt 0.1 -o output/test -seed 42
```

### Opciones de línea de comando

| Opción | Descripción | Default |
|--------|-------------|---------|
| `-N` | Número de partículas | 100 |
| `-tf` | Tiempo final de simulación (s) | 5.0 |
| `-dt` | Intervalo de salida (s) | 0.05 |
| `-o` | Directorio de salida | output |
| `-seed` | Semilla aleatoria | 42 |
| `-L` | Diámetro del recinto (m) | 80.0 |
| `-r` | Radio de partículas (m) | 1.0 |
| `-r0` | Radio del obstáculo (m) | 1.0 |
| `-v0` | Velocidad inicial (m/s) | 1.0 |
| `-m` | Masa de partículas (kg) | 1.0 |

### Análisis (usar siempre el venv)

```bash
.venv/bin/python analysis/ex1_execution_time.py   # Ej 1.1
.venv/bin/python analysis/ex2_scanning_rate.py     # Ej 1.2
.venv/bin/python analysis/ex3_fraction_used.py     # Ej 1.3
.venv/bin/python analysis/ex4_radial_profiles.py   # Ej 1.4
```

### Ejecutar todo

```bash
./run.sh
```

## Descripción del Sistema

- **Recinto**: Circular de diámetro L = 80 m
- **Obstáculo**: Circular fijo en el centro, radio r₀ = 1 m
- **Partículas**: Radio r = 1 m, velocidad v₀ = 1 m/s, masa m = 1 kg
- **Estados**:
  - 🟢 Fresca (state=0): Estado inicial
  - 🟣 Usada (state=1): Tras colisionar con el obstáculo central
  - Transición: Fresca → Usada (al tocar obstáculo), Usada → Fresca (al tocar borde)
