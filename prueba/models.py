"""
MODELS.PY - Modelos de base de datos MongoDB usando MongoEngine
=================================================================
Este archivo define los documentos (modelos) que se almacenan en MongoDB.
MongoEngine es un ORM (Object-Relational Mapping) para MongoDB que permite
usar objetos Python en lugar de consultas directas a la base de datos.

Documentos definidos:
- usuarios: Usuarios del sistema con autenticación y roles
- Calificacion: Datos financieros de calificaciones con factores y montos
- Log: Registro de auditoría de acciones realizadas por usuarios
"""

# IMPORTACIONES DE TIPOS DE DATOS DE MONGOENGINE
# ===============================================
# Importamos los tipos de campos de MongoEngine para crear documentos en MongoDB
# Document: Clase base para crear documentos (equivalente a tabla en SQL)
# StringField: Campo de texto
# IntField: Campo de número entero
# EmailField: Campo de email con validación
# DateTimeField: Campo de fecha y hora
# DecimalField: Campo decimal para números con precisión
# BooleanField: Campo booleano (True/False)
# ReferenceField: Campo que referencia a otro documento (relación)
from mongoengine import Document, StringField, FloatField, IntField, ListField, EmbeddedDocument, EmailField, DateTimeField, DecimalField, BooleanField, ReferenceField

# Importamos datetime para usar fechas y horas
import datetime


# MODELO: USUARIOS
# ================
# Documento que representa un usuario del sistema
# Almacena información de autenticación, roles y foto de perfil
class usuarios(Document):
    # CAMPOS DEL DOCUMENTO USUARIOS
    # ==============================
    # Definimos los campos que tendrá el documento usuarios usando los tipos importados
    
    nombre = StringField(max_length=200, required=True)  # Nombre completo del usuario (obligatorio, máximo 200 caracteres)
    correo = EmailField(required=True, unique=True)      # Email del usuario (obligatorio, único en la base de datos)
    contrasena = StringField(max_length=200, required=True)  # Contraseña hasheada (obligatoria, máximo 200 caracteres)
    rol = BooleanField(default=False)                    # Rol de administrador (True=admin, False=usuario normal, por defecto False)
    foto_perfil = StringField(max_length=500, required=False, default=None)  # Ruta de la foto de perfil (opcional, máximo 500 caracteres)
    
    # METADATA DEL DOCUMENTO
    # =======================
    # meta: Diccionario que define la configuración del documento
    # collection: Nombre de la colección en MongoDB donde se guardará este documento
    # Si no se especifica, MongoEngine usa el nombre de la clase en minúsculas
    meta = {
        'collection': 'usuarios'  # Los documentos usuarios se guardan en la colección 'usuarios' de MongoDB
    }
    
    # MÉTODO __str__: Representación en string del objeto
    # ====================================================
    # Se usa para mostrar el nombre del usuario cuando se convierte el objeto a string
    # Útil para debugging y en el admin de Django
    def __str__(self):
        return self.nombre
    
# MODELO: CALIFICACION
# ====================
# Documento que representa una calificación financiera
# Almacena información de mercado, instrumentos, factores y montos financieros
class Calificacion(Document):
    # CAMPOS DE INFORMACIÓN BÁSICA
    # =============================
    Mercado = StringField(max_length=100, required=False)  # Tipo de mercado (acciones, CFI, Fondos mutuos)
    Origen = StringField(max_length=100, required=False)   # Origen de los datos (Corredor, CSV)
    Ejercicio = IntField(required=True)                    # Año o período fiscal (obligatorio)
    Instrumento = StringField(max_length=50, required=False)  # Código del instrumento financiero
    EventoCapital = StringField(max_length=100, required=False)  # Tipo de evento de capital
    FechaPago = DateTimeField(required=False)             # Fecha de pago del instrumento
    SecuenciaEvento = IntField(required=False)            # Número secuencial del evento
    Descripcion = StringField(required=False)             # Descripción adicional del registro
    FechaAct = DateTimeField(default=datetime.datetime.now)  # Fecha de última actualización (automática)
    Dividendo = DecimalField(precision=8, default=0.0)    # Monto del dividendo (8 decimales)
    
    # CAMPO BOOLEANO
    # ==============
    ISFUT = BooleanField(default=False)  # Indicador si es futuro (True) o no (False), por defecto False
    
    
    # CAMPOS FINANCIEROS ADICIONALES
    # ===============================
    ValorHistorico = DecimalField(precision=8, default=0.0)      # Valor histórico del instrumento
    FactorActualizacion = DecimalField(precision=8, default=0.0) # Factor de actualización monetaria
    Anho = IntField(required=False)                              # Año adicional (alternativo a Ejercicio)

    # FACTORES FINANCIEROS (F8 A F37)
    # ================================
    # Factores del 8 al 37 (30 campos total)
    # Estos factores se calculan dividiendo cada monto por la Suma Base (suma de montos 8-19)
    # Precisión de 8 decimales para cálculos financieros precisos
    Factor08 = DecimalField(precision=8, default=0.0)
    Factor09 = DecimalField(precision=8, default=0.0)
    Factor10 = DecimalField(precision=8, default=0.0)
    Factor11 = DecimalField(precision=8, default=0.0)
    Factor12 = DecimalField(precision=8, default=0.0)
    Factor13 = DecimalField(precision=8, default=0.0)
    Factor14 = DecimalField(precision=8, default=0.0)
    Factor15 = DecimalField(precision=8, default=0.0)
    Factor16 = DecimalField(precision=8, default=0.0)
    Factor17 = DecimalField(precision=8, default=0.0)
    Factor18 = DecimalField(precision=8, default=0.0)
    Factor19 = DecimalField(precision=8, default=0.0)
    Factor20 = DecimalField(precision=8, default=0.0)
    Factor21 = DecimalField(precision=8, default=0.0)
    Factor22 = DecimalField(precision=8, default=0.0)
    Factor23 = DecimalField(precision=8, default=0.0)
    Factor24 = DecimalField(precision=8, default=0.0)
    Factor25 = DecimalField(precision=8, default=0.0)
    Factor26 = DecimalField(precision=8, default=0.0)
    Factor27 = DecimalField(precision=8, default=0.0)
    Factor28 = DecimalField(precision=8, default=0.0)
    Factor29 = DecimalField(precision=8, default=0.0)
    Factor30 = DecimalField(precision=8, default=0.0)
    Factor31 = DecimalField(precision=8, default=0.0)
    Factor32 = DecimalField(precision=8, default=0.0)
    Factor33 = DecimalField(precision=8, default=0.0)
    Factor34 = DecimalField(precision=8, default=0.0)
    Factor35 = DecimalField(precision=8, default=0.0)
    Factor36 = DecimalField(precision=8, default=0.0)
    Factor37 = DecimalField(precision=8, default=0.0)
    
    # CAMPOS FINANCIEROS ESPECIALES
    # ==============================
    RentasExentas = DecimalField(precision=8, default=0.0)  # Rentas exentas de impuestos (GC y/o Impuesto Adicional)
    Factor19A = DecimalField(precision=8, default=0.0)      # Factor 19A: Ingresos no constitutivos de renta
    
    # MONTOS FINANCIEROS (M8 A M37)
    # ==============================
    # Montos del 8 al 37 (30 campos total)
    # Estos montos se usan para calcular los factores: Factor = Monto / SumaBase
    # Se guardan para poder recuperarlos al modificar/copiar calificaciones
    # Precisión de 2 decimales (centavos) para montos monetarios
    Monto08 = DecimalField(precision=2, default=0.0)
    Monto09 = DecimalField(precision=2, default=0.0)
    Monto10 = DecimalField(precision=2, default=0.0)
    Monto11 = DecimalField(precision=2, default=0.0)
    Monto12 = DecimalField(precision=2, default=0.0)
    Monto13 = DecimalField(precision=2, default=0.0)
    Monto14 = DecimalField(precision=2, default=0.0)
    Monto15 = DecimalField(precision=2, default=0.0)
    Monto16 = DecimalField(precision=2, default=0.0)
    Monto17 = DecimalField(precision=2, default=0.0)
    Monto18 = DecimalField(precision=2, default=0.0)
    Monto19 = DecimalField(precision=2, default=0.0)
    Monto20 = DecimalField(precision=2, default=0.0)
    Monto21 = DecimalField(precision=2, default=0.0)
    Monto22 = DecimalField(precision=2, default=0.0)
    Monto23 = DecimalField(precision=2, default=0.0)
    Monto24 = DecimalField(precision=2, default=0.0)
    Monto25 = DecimalField(precision=2, default=0.0)
    Monto26 = DecimalField(precision=2, default=0.0)
    Monto27 = DecimalField(precision=2, default=0.0)
    Monto28 = DecimalField(precision=2, default=0.0)
    Monto29 = DecimalField(precision=2, default=0.0)
    Monto30 = DecimalField(precision=2, default=0.0)
    Monto31 = DecimalField(precision=2, default=0.0)
    Monto32 = DecimalField(precision=2, default=0.0)
    Monto33 = DecimalField(precision=2, default=0.0)
    Monto34 = DecimalField(precision=2, default=0.0)
    Monto35 = DecimalField(precision=2, default=0.0)
    Monto36 = DecimalField(precision=2, default=0.0)
    Monto37 = DecimalField(precision=2, default=0.0)
    
    # SUMA BASE
    # =========
    # Suma de los montos del 8 al 19 (Monto08 + Monto09 + ... + Monto19)
    # Se usa como denominador para calcular factores: Factor = Monto / SumaBase
    # Se guarda para poder hacer el cálculo inverso: Monto = Factor * SumaBase
    SumaBase = DecimalField(precision=2, default=0.0)

    # METADATA DEL DOCUMENTO
    # =======================
    meta = { 
        'collection': 'calificaciones'  # Los documentos Calificacion se guardan en la colección 'calificaciones'
    }

    # MÉTODO __str__: Representación en string del objeto
    # ====================================================
    # Muestra el ejercicio y el instrumento para identificar fácilmente la calificación
    def __str__(self):
        return f"{self.Ejercicio} - {self.Instrumento}"


# MODELO: LOG
# ===========
# Documento que registra todas las acciones realizadas por usuarios (auditoría)
# Permite rastrear quién hizo qué, cuándo y sobre qué documento
class Log(Document):
    # CAMPOS DE FECHA Y USUARIO
    # ==========================
    fecharegistrada = DateTimeField(default=datetime.datetime.now)  # Fecha y hora de la acción (automática)
    Usuarioid = ReferenceField(usuarios, required=True)  # Usuario que realizó la acción (obligatorio)
                                                                   # ReferenceField crea un enlace directo al documento usuarios
    usuario_afectado = ReferenceField(usuarios, required=False, null=True)  # Usuario afectado por la acción (opcional)
                                                                           # Útil para acciones como "Crear Usuario" o "Modificar Usuario"
    correoElectronico = EmailField()  # Email del usuario que realizó la acción (para referencia rápida)
    
    # CAMPOS DE ACCIÓN
    # ================
    # ACCION_CHOICES: Tupla que define las acciones válidas que se pueden registrar
    # choices: Limita las opciones a esta lista para mantener consistencia
    ACCION_CHOICES = (
        'Crear Usuario',           # Se creó un nuevo usuario
        'Modificar Usuario',       # Se modificó un usuario existente
        'Eliminar Usuario',        # Se eliminó un usuario
        'Crear Calificacion',      # Se creó una nueva calificación
        'Modificar Calificacion',  # Se modificó una calificación existente
        'Eliminar Calificacion',   # Se eliminó una calificación
        'Carga Masiva'             # Se realizó una carga masiva desde CSV
    )
    accion = StringField(max_length=50, choices=ACCION_CHOICES, required=True)  # Tipo de acción realizada (obligatorio)
    
    # CAMPOS DE DOCUMENTO AFECTADO
    # =============================
    iddocumento = ReferenceField(Calificacion, required=False, null=True)  # Calificación afectada por la acción (opcional)
                                                                           # Útil para acciones sobre calificaciones
    
    # CAMPO DE CAMBIOS DETALLADOS
    # ============================
    # Almacena un JSON string con los cambios realizados (campos modificados, valores anteriores y nuevos)
    # Permite ver exactamente qué cambió en una modificación
    # Formato: [{"campo": "nombre", "valor_anterior": "valor1", "valor_nuevo": "valor2"}, ...]
    cambios_detallados = StringField(required=False)  # JSON string con los cambios detallados (opcional)
    
    # METADATA DEL DOCUMENTO
    # =======================
    meta = {
        'collection': 'log'  # Los documentos Log se guardan en la colección 'log' de MongoDB
    }
    
    # MÉTODO __str__: Representación en string del objeto
    # ====================================================
    # Muestra el ID del log, correo del usuario y la acción realizada
    # Útil para debugging y en el admin de Django
    def __str__(self):
        return f"[{self.id}] {self.correoElectronico} - {self.accion}"