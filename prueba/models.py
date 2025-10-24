from mongoengine import Document, StringField, FloatField, IntField, ListField, EmbeddedDocument, EmailField, DateTimeField, DecimalField, BooleanField #estas importaciones son OBLIGATORIAS PARA CREAR EL DOCUMENTO
import datetime

class usuarios(Document):
    nombre = StringField(max_length=200, required=True)
    correo = EmailField(required=True, unique=True) 
    contrasena = StringField(max_length=200, required=True) 
    rol = BooleanField(default=False) 
    meta = {
        'collection': 'usuarios'
    }
    def __str__(self):
        return self.nombre
    

class Calificacion(Document):
    
    Mercado = StringField(max_length=100, required=False) 
    Ejercicio = IntField(required=True) 
    Instrumento = StringField(max_length=50, required=False) 
    FechaPago = DateTimeField(required=False)
    SecuenciaEvento = IntField(required=False)
    Descripcion = StringField(required=False)
    FechaAct = DateTimeField(default=datetime.datetime.now)

    # --- Campos del mockup 1 ---
    Dividendo = DecimalField(precision=8, default=0.0)
    
    # ¡CAMBIO AQUÍ! ISFUT ahora es Boolean
    ISFUT = BooleanField(default=False) # Valor por defecto es 'no chequeado'
    
    # --- Campos del mockup 2 ---
    ValorHistorico = DecimalField(precision=8, default=0.0)
    FactorActualizacion = DecimalField(precision=8, default=0.0)
    Anho = IntField(required=False)

    # --- Factores 8-37 ---
    Factor08 = DecimalField(precision=8, default=0.0)
    # ... (Factor09 to Factor37) ...
    Factor37 = DecimalField(precision=8, default=0.0)

    meta = { 'collection': 'calificaciones' }

    def __str__(self):
        return f"{self.Ejercicio} - {self.Instrumento}"