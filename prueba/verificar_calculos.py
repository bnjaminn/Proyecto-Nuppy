"""
Script para verificar los cálculos de factores
Ejecutar desde la raíz del proyecto Django: python manage.py shell < verificar_calculos.py
O ejecutar directamente: python verificar_calculos.py
"""

def calcular_factor(numerador, denominador):
    """Función auxiliar para calcular factores (igual que en views.py)"""
    if denominador == 0:
        return 0.0
    resultado = float(numerador) / float(denominador)
    resultado = min(resultado, 1.0)  # No puede ser mayor que 1
    return round(resultado, 8)  # Redondeo al 8vo decimal


def verificar_caso_prueba(nombre, factores_montos, rentas_exentas, factor19a):
    """Verifica un caso de prueba completo"""
    print(f"\n{'='*60}")
    print(f"Caso de Prueba: {nombre}")
    print(f"{'='*60}")
    
    # Calcular sumas
    suma_8_a_10 = factores_montos['Factor08'] + factores_montos['Factor09'] + factores_montos['Factor10']
    suma_8_a_19 = sum(factores_montos[f'Factor{i:02d}'] for i in range(8, 20))
    
    print(f"\nSuma Factor08 a Factor10: {suma_8_a_10}")
    print(f"Suma Factor08 a Factor19: {suma_8_a_19}")
    
    # Calcular factores
    resultados = {}
    
    # Factores 13-17, 20-37
    for i in range(13, 18):
        field_name = f'Factor{i:02d}'
        if suma_8_a_19 > 0:
            resultados[field_name] = calcular_factor(factores_montos[field_name], suma_8_a_19)
        else:
            resultados[field_name] = 0.0
    
    for i in range(20, 38):
        field_name = f'Factor{i:02d}'
        if suma_8_a_19 > 0:
            resultados[field_name] = calcular_factor(factores_montos[field_name], suma_8_a_19)
        else:
            resultados[field_name] = 0.0
    
    # Factor 18
    if suma_8_a_10 > 0:
        resultados['Factor18'] = calcular_factor(rentas_exentas, suma_8_a_10)
    else:
        resultados['Factor18'] = 0.0
    
    # Factor 19
    if suma_8_a_19 > 0:
        resultados['Factor19'] = calcular_factor(factor19a, suma_8_a_19)
    else:
        resultados['Factor19'] = 0.0
    
    # Mostrar resultados
    print(f"\n{'Factor':<12} {'Monto Ingresado':<20} {'Resultado Calculado':<20}")
    print("-" * 60)
    
    for i in range(13, 18):
        field_name = f'Factor{i:02d}'
        print(f"{field_name:<12} {factores_montos[field_name]:<20.8f} {resultados[field_name]:<20.8f}")
    
    print(f"{'Factor18':<12} {rentas_exentas:<20.8f} {resultados['Factor18']:<20.8f}")
    print(f"{'Factor19':<12} {factor19a:<20.8f} {resultados['Factor19']:<20.8f}")
    
    for i in range(20, 38):
        field_name = f'Factor{i:02d}'
        print(f"{field_name:<12} {factores_montos[field_name]:<20.8f} {resultados[field_name]:<20.8f}")
    
    # Verificaciones
    print(f"\n{'Verificaciones:'}")
    errores = []
    for factor, valor in resultados.items():
        if valor > 1.0:
            errores.append(f"{factor} = {valor} (excede 1.0)")
        if valor < 0.0:
            errores.append(f"{factor} = {valor} (es negativo)")
    
    if errores:
        print("  ❌ ERRORES ENCONTRADOS:")
        for error in errores:
            print(f"    - {error}")
    else:
        print("  ✅ Todos los valores están entre 0 y 1")
    
    return resultados


# CASO DE PRUEBA 1: Cálculo Básico
print("\n" + "="*60)
print("INICIANDO VERIFICACIÓN DE CÁLCULOS")
print("="*60)

factores1 = {}
for i in range(8, 38):
    factores1[f'Factor{i:02d}'] = 0.0

factores1['Factor08'] = 100.0
factores1['Factor09'] = 200.0
factores1['Factor10'] = 300.0
factores1['Factor11'] = 150.0
factores1['Factor12'] = 250.0
factores1['Factor13'] = 50.0
factores1['Factor14'] = 75.0
factores1['Factor15'] = 100.0
factores1['Factor16'] = 125.0
factores1['Factor17'] = 175.0
factores1['Factor20'] = 200.0
factores1['Factor21'] = 300.0

verificar_caso_prueba("Cálculo Básico", factores1, 150.0, 200.0)

# CASO DE PRUEBA 2: Valores que Exceden 1
factores2 = {}
for i in range(8, 38):
    factores2[f'Factor{i:02d}'] = 0.0

factores2['Factor08'] = 100.0
factores2['Factor09'] = 100.0
factores2['Factor10'] = 100.0
factores2['Factor11'] = 100.0
factores2['Factor12'] = 100.0
factores2['Factor20'] = 2000.0

verificar_caso_prueba("Valores que Exceden 1", factores2, 500.0, 3000.0)

# CASO DE PRUEBA 3: Suma Cero
factores3 = {}
for i in range(8, 38):
    factores3[f'Factor{i:02d}'] = 0.0

verificar_caso_prueba("División por Cero", factores3, 100.0, 200.0)

# CASO DE PRUEBA 4: Verificación Rápida
factores4 = {}
for i in range(8, 38):
    factores4[f'Factor{i:02d}'] = 0.0

factores4['Factor08'] = 100.0
factores4['Factor09'] = 200.0
factores4['Factor10'] = 300.0
factores4['Factor13'] = 50.0

verificar_caso_prueba("Verificación Rápida", factores4, 150.0, 100.0)

print(f"\n{'='*60}")
print("VERIFICACIÓN COMPLETADA")
print(f"{'='*60}")

