# Pruebas de Cálculo de Factores

Este documento contiene casos de prueba para verificar que los cálculos de factores se realizan correctamente.

## Reglas de Cálculo

- **Factores 13-17, 20-37**: Se calculan dividiendo el monto del factor entre la suma de factores 8 a 19
- **Factor 18**: Se calcula dividiendo RentasExentas entre la suma de factores 8 a 10
- **Factor 19**: Se calcula dividiendo Factor19A entre la suma de factores 8 a 19
- Todos los valores se redondean al 8vo decimal
- Los valores no pueden ser mayores que 1

---

## Caso de Prueba 1: Cálculo Básico

### Valores de Entrada:
```
Factor08 = 100.0
Factor09 = 200.0
Factor10 = 300.0
Factor11 = 150.0
Factor12 = 250.0
Factor13 = 50.0
Factor14 = 75.0
Factor15 = 100.0
Factor16 = 125.0
Factor17 = 175.0
Factor18 = 0.0 (se calculará)
Factor19 = 0.0 (se calculará)
Factor20 = 200.0
Factor21 = 300.0
... (resto de factores en 0.0)
RentasExentas = 150.0
Factor19A = 200.0
```

### Cálculos Esperados:

**Suma 8 a 10** = 100 + 200 + 300 = **600.0**

**Suma 8 a 19** = 100 + 200 + 300 + 150 + 250 + 50 + 75 + 100 + 125 + 175 + 0 + 0 = **1525.0**

**Factor 13** = 50.0 / 1525.0 = **0.03278689** (redondeado a 8 decimales)

**Factor 14** = 75.0 / 1525.0 = **0.04918033**

**Factor 15** = 100.0 / 1525.0 = **0.06557377**

**Factor 16** = 125.0 / 1525.0 = **0.08196721**

**Factor 17** = 175.0 / 1525.0 = **0.11475410**

**Factor 18** = 150.0 / 600.0 = **0.25** (o 0.25000000)

**Factor 19** = 200.0 / 1525.0 = **0.13114754**

**Factor 20** = 200.0 / 1525.0 = **0.13114754**

**Factor 21** = 300.0 / 1525.0 = **0.19672131**

---

## Caso de Prueba 2: Valores que Exceden 1

### Valores de Entrada:
```
Factor08 = 100.0
Factor09 = 100.0
Factor10 = 100.0
Factor11 = 100.0
Factor12 = 100.0
Factor13 = 0.0
Factor14 = 0.0
Factor15 = 0.0
Factor16 = 0.0
Factor17 = 0.0
Factor18 = 0.0 (se calculará)
Factor19 = 0.0 (se calculará)
Factor20 = 2000.0  (valor muy alto)
... (resto de factores en 0.0)
RentasExentas = 500.0
Factor19A = 3000.0  (valor muy alto)
```

### Cálculos Esperados:

**Suma 8 a 10** = 100 + 100 + 100 = **300.0**

**Suma 8 a 19** = 100 + 100 + 100 + 100 + 100 + 0 + 0 + 0 + 0 + 0 + 0 + 0 = **500.0**

**Factor 20** = 2000.0 / 500.0 = 4.0, pero debe limitarse a **1.0** (no puede ser mayor que 1)

**Factor 19** = 3000.0 / 500.0 = 6.0, pero debe limitarse a **1.0**

**Factor 18** = 500.0 / 300.0 = 1.666..., pero debe limitarse a **1.0**

---

## Caso de Prueba 3: Suma Cero (División por Cero)

### Valores de Entrada:
```
Factor08 = 0.0
Factor09 = 0.0
Factor10 = 0.0
Factor11 = 0.0
Factor12 = 0.0
... (todos los factores en 0.0)
RentasExentas = 100.0
Factor19A = 200.0
```

### Cálculos Esperados:

**Suma 8 a 10** = 0.0

**Suma 8 a 19** = 0.0

**Factor 18** = 100.0 / 0.0 = **0.0** (evitar división por cero)

**Factor 19** = 200.0 / 0.0 = **0.0** (evitar división por cero)

**Todos los demás factores** = **0.0**

---

## Caso de Prueba 4: Valores Decimales Pequeños

### Valores de Entrada:
```
Factor08 = 0.00000001
Factor09 = 0.00000002
Factor10 = 0.00000003
Factor11 = 0.00000001
Factor12 = 0.00000001
Factor13 = 0.00000005
... (resto de factores en 0.0)
RentasExentas = 0.00000010
Factor19A = 0.00000020
```

### Cálculos Esperados:

**Suma 8 a 10** = 0.00000006

**Suma 8 a 19** = 0.00000008

**Factor 13** = 0.00000005 / 0.00000008 = **0.62500000**

**Factor 18** = 0.00000010 / 0.00000006 = **1.0** (limitado a 1)

**Factor 19** = 0.00000020 / 0.00000008 = **1.0** (limitado a 1)

---

## Caso de Prueba 5: Valores Reales (Ejemplo Práctico)

### Valores de Entrada:
```
Factor08 = 192770580.0
Factor09 = 64161878.0
Factor10 = 0.0
Factor11 = 111812850.0
Factor12 = 0.0
Factor13 = 0.0
Factor14 = 0.0
Factor15 = 0.0
Factor16 = 0.0
Factor17 = 0.0
Factor18 = 0.0 (se calculará)
Factor19 = 0.0 (se calculará)
Factor20 = 0.0
... (resto de factores en 0.0)
RentasExentas = 71298705.0
Factor19A = 0.0
```

### Cálculos Esperados:

**Suma 8 a 10** = 192770580 + 64161878 + 0 = **256932458.0**

**Suma 8 a 19** = 192770580 + 64161878 + 0 + 111812850 + 0 + 0 + 0 + 0 + 0 + 0 + 0 + 0 = **368745308.0**

**Factor 18** = 71298705.0 / 256932458.0 = **0.27750000** (aproximadamente)

---

## Instrucciones para Probar

1. **Abrir el modal de factores** después de crear una calificación
2. **Ingresar los valores** del caso de prueba en los campos correspondientes
3. **Hacer clic en "Calcular"**
4. **Verificar que los valores calculados** coincidan con los esperados
5. **Verificar que los valores no excedan 1.0**
6. **Verificar que los valores estén redondeados a 8 decimales**

---

## Valores de Verificación Rápida

Para una verificación rápida, usa estos valores simples:

```
Factor08 = 100
Factor09 = 200
Factor10 = 300
Factor11 = 0
Factor12 = 0
Factor13 = 50
Factor14 = 0
Factor15 = 0
Factor16 = 0
Factor17 = 0
Factor18 = 0 (se calculará)
Factor19 = 0 (se calculará)
RentasExentas = 150
Factor19A = 100
```

**Resultados esperados:**
- Factor 13 = 50 / 600 = **0.08333333**
- Factor 18 = 150 / 600 = **0.25** (o 0.25000000)
- Factor 19 = 100 / 600 = **0.16666667**

---

## Notas Importantes

- Los factores 8-12 y otros campos son los **MONTOS** que se ingresan
- Los factores 13-37 son los **RESULTADOS CALCULADOS** (proporciones)
- El Factor 18 usa la suma de 8-10, no 8-19
- El Factor 19 usa Factor19A como numerador
- Todos los valores deben estar entre 0 y 1 (inclusive)

