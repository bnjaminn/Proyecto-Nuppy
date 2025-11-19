#Importamos los tipos de datos de MONGODB que usaremos para crear la base de los documentos, junto con el datetime
from mongoengine import Document, StringField, FloatField, IntField, ListField, EmbeddedDocument, EmailField, DateTimeField, DecimalField, BooleanField, ReferenceField #estas importaciones son OBLIGATORIAS PARA CREAR EL DOCUMENTO
import datetime

#modelo para usuarios
class usuarios(Document):
    #aca definimos los campos que tendra el modelo o documento usuarios si nos damos cuenta usamos las importaciones que hicimos al principio de lo contrario no funcionaria
    nombre = StringField(max_length=200, required=True)
    correo = EmailField(required=True, unique=True) 
    contrasena = StringField(max_length=200, required=True) 
    rol = BooleanField(default=False)
    foto_perfil = StringField(max_length=500, required=False, default=None)  # Ruta de la foto de perfil 
    meta = {
        'collection': 'usuarios' #meta es para hacer referencia a que carpeta/coleccion se guardara el documento de la base de datos en este caso es usuarios
    }
    def __str__(self):
        return self.nombre
    
#sin terminar aun no funciona IGNORAR
class Calificacion(Document):
    Mercado = StringField(max_length=100, required=False) 
    Origen = StringField(max_length=100, required=False)  # Campo para guardar el origen (Corredor, CSV)
    Ejercicio = IntField(required=True) 
    Instrumento = StringField(max_length=50, required=False) 
    EventoCapital = StringField(max_length=100, required=False)  # Campo agregado según mockup
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

    # Factores del 8 al 37 (30 campos total)
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
    
    # Campos adicionales según mockup
    RentasExentas = DecimalField(precision=8, default=0.0)  # Rentas Exentas de Impto. GC Y/O Impto Adicional
    Factor19A = DecimalField(precision=8, default=0.0)  # Factor-19A Ingreso no Constitutivos de Renta
    
    # Montos del 8 al 37 (para poder recuperarlos al modificar/copiar)
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
    
    # Suma base (suma de montos del 8 al 19) para poder hacer el cálculo inverso
    SumaBase = DecimalField(precision=2, default=0.0)

    meta = { 'collection': 'calificaciones' }

    def __str__(self):
        return f"{self.Ejercicio} - {self.Instrumento}"


class Log(Document):
    fecharegistrada = DateTimeField(default=datetime.datetime.now)
    Usuarioid = ReferenceField(usuarios, required=True) #Guarda el id del usuario que realizó la acción, ReferenceField Crea un enlace directo al documento usuariosrequired=True: Es obligatorio, un log no puede existir sin un usuario
    usuario_afectado = ReferenceField(usuarios, required=False, null=True)
    correoElectronico = EmailField()
    ACCION_CHOICES = ( #accion_CHOICES: Describe la operación (Crear, Modificar, etc.) choices limita las opciones a esta lista
        'Crear Usuario',
        'Modificar Usuario',
        'Eliminar Usuario',
        'Crear Calificacion',
        'Modificar Calificacion',
        'Eliminar Calificacion',
        'Carga Masiva'
    )
    accion = StringField(max_length=50, choices=ACCION_CHOICES, required=True)
    iddocumento = ReferenceField(Calificacion, required=False, null=True)
    # Campo para guardar los cambios detallados (campos modificados, valores anteriores y nuevos)
    cambios_detallados = StringField(required=False)  # JSON string con los cambios
    meta = {
        'collection': 'log' # Nombre de la colección en MongoDB
    }
    def __str__(self):
        # Muestra el ID (ObjectId), correo y acción
        return f"[{self.id}] {self.correoElectronico} - {self.accion}"