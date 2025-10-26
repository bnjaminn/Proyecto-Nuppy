#Importamos los tipos de datos de MONGODB que usaremos para crear la base de los documentos, junto con el datetime
from mongoengine import Document, StringField, FloatField, IntField, ListField, EmbeddedDocument, EmailField, DateTimeField, DecimalField, BooleanField #estas importaciones son OBLIGATORIAS PARA CREAR EL DOCUMENTO
import datetime

#modelo para usuarios
class usuarios(Document):
    #aca definimos los campos que tendra el modelo o documento usuarios si nos damos cuenta usamos las importaciones que hicimos al principio de lo contrario no funcionaria
    nombre = StringField(max_length=200, required=True)
    correo = EmailField(required=True, unique=True) 
    contrasena = StringField(max_length=200, required=True) 
    rol = BooleanField(default=False) 
    meta = {
        'collection': 'usuarios' #meta es para hacer referencia a que carpeta/coleccion se guardara el documento de la base de datos en este caso es usuarios
    }
    def __str__(self):
        return self.nombre
    
#sin terminar aun no funciona IGNORAR
class Calificacion(Document):
    Mercado = StringField(max_length=100, required=False) 
    Ejercicio = IntField(required=True) 
    Instrumento = StringField(max_length=50, required=False) 
    FechaPago = DateTimeField(required=False)
    SecuenciaEvento = IntField(required=False)
    Descripcion = StringField(required=False)
    FechaAct = DateTimeField(default=datetime.datetime.now)
    Dividendo = DecimalField(precision=8, default=0.0)
    
    #ISFUTes Boolean
    ISFUT = BooleanField(default=False) # Valor por defecto es 'no chequeado'
    
    
    ValorHistorico = DecimalField(precision=8, default=0.0)
    FactorActualizacion = DecimalField(precision=8, default=0.0)
    Anho = IntField(required=False)

    
    Factor08 = DecimalField(precision=8, default=0.0)
    
    Factor37 = DecimalField(precision=8, default=0.0)

    meta = { 'collection': 'calificaciones' }

    def __str__(self):
        return f"{self.Ejercicio} - {self.Instrumento}"