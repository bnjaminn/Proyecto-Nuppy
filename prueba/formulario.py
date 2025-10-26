from django import forms
from .models import usuarios #importamos usuario para la validacion completa 


#formulario para el login
class LoginForm(forms.Form): #especificamos que es de tipo forms esto se hace con todos los forms
    correo = forms.EmailField(
        label="", 
        widget=forms.EmailInput(
            attrs={
                'placeholder': 'correo', 
                'class': 'form-input'     
            }
        )
    )
    contrasena = forms.CharField(
        label="",
        widget=forms.PasswordInput(
            attrs={
                'placeholder': '**********',
                'class': 'form-input'     
            }
        )
    )

#formulario para el ingresar calificacion (SUJETO A CAMBIOS)
class CalificacionModalForm(forms.Form):
    #Aca definimos los campos para el primer formulario de ingresar osea la primera ventana
    Mercado = forms.CharField(required=False)
    Ejercicio = forms.IntegerField()
    Instrumento = forms.CharField(max_length=50, required=False)
    FechaPago = forms.DateField(required=False, input_formats=['%Y-%m-%d']) 
    SecuenciaEvento = forms.IntegerField(required=False)
    Dividendo = forms.DecimalField(initial=0.0, required=False, decimal_places=8)
    ISFUT = forms.BooleanField(required=False) # 'required=False' permite que no esté chequeado
    
    #Ignorar aun no se utiliza
    ValorHistorico = forms.DecimalField(initial=0.0, required=False, decimal_places=8)
    FactorActualizacion = forms.DecimalField(initial=0.0, required=False, decimal_places=8)
    Anho = forms.IntegerField(required=False)

    
    Descripcion = forms.CharField(required=False)

#formulario para crear usuario
class UsuarioForm(forms.Form):
    #Aca Define los campos del modal Crear Usuario
    nombre = forms.CharField(max_length=200, required=True)
    correo = forms.EmailField(required=True)
    contrasena = forms.CharField(widget=forms.PasswordInput, required=True)
    # BooleanField maneja el 'true'/'false' del checkbox para decidir que sea admin o no
    rol = forms.BooleanField(required=False) 

    #Aseguraramos que el correo no exista ya
    def clean_correo(self):
        correo = self.cleaned_data.get('correo')
        if usuarios.objects(correo=correo).first(): # Busca si ya existe en MongoDB
            raise forms.ValidationError("Este correo electrónico ya está registrado.")
        return correo
    
#formulario para actualizar usuario
class UsuarioUpdateForm(forms.Form):
    #Aca definimos los datos que hay que pasar para actualizar al usuario
    user_id = forms.CharField(widget=forms.HiddenInput(), required=True) #en esta linea se ejectuta el hidden para ocultar el ID del usuario
    nombre = forms.CharField(max_length=200, required=True)
    correo = forms.EmailField(required=True)
    contrasena = forms.CharField(widget=forms.PasswordInput, required=False) #Contraseña opcional con el false: si se envía, se actualiza
    rol = forms.BooleanField(required=False)

    # Validación extra: Asegurar que el NUEVO correo no esté ya en uso por OTRO usuario
    def clean(self):
        cleaned_data = super().clean()
        correo = cleaned_data.get('correo')
        user_id = cleaned_data.get('user_id')

        # Busca si existe OTRO usuario con este correo
        existing_user = usuarios.objects(correo=correo, id__ne=user_id).first() #Busca si existe OTRO usuario (id__ne = id not equal) con este correo
        if existing_user:
            self.add_error('correo', "Este correo electrónico ya está registrado por otro usuario.")  
        return cleaned_data