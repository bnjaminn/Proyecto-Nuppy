from mongoengine import Document, StringField, FloatField, IntField, ListField, EmbeddedDocument #estas importaciones son OBLIGATORIAS PARA CREAR EL DOCUMENTO

# En lugar de heredar de 'models.Model', heredas de 'Document'
class Producto(Document): #ignorar esta creacion de documento fue un test para probar la conexion para la base de datos de todas formas sirve como base para entender como crear los documentos
    """
    Este es un Documento de MongoEngine.
    Es el equivalente a un Modelo de Django.
    """
    # Define los campos que quieres. Se ven muy parecidos a los de Django.
    nombre = StringField(max_length=200, required=True)
    precio = FloatField(default=0.0)
    stock = IntField(default=0)
    
    # ¡Aquí puedes hacer cosas que en SQL son difíciles!
    tags = ListField(StringField(max_length=50))
    
    # Esto le dice a MongoEngine en qué "colección" (tabla) guardar esto.
    meta = {
        'collection': 'productos'
    }

    def __str__(self):
        return self.nombre
    



class usuarios(Document):
    nombre = StringField(max_length=200, required=True)
    correo = StringField(max_length=200, required=True)
    contrasena = StringField(max_length=8, required=True)
    meta = {
        'collection': 'usuarios'
    }

    def __str__(self):
        return self.nombre