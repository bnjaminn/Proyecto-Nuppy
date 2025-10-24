from django import forms
from .models import usuarios

class LoginForm(forms.Form):
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


class CalificacionModalForm(forms.Form):
    """
    Este formulario coincide con TODOS los campos
    (visibles y ocultos) que se enviarán AL FINAL del flujo modal.
    ¡Actualizado con ISFUT como BooleanField!
    """
    # Campos ocultos (pasados desde Modal 1)
    Mercado = forms.CharField(required=False)
    Ejercicio = forms.IntegerField()
    Instrumento = forms.CharField(max_length=50, required=False)
    FechaPago = forms.DateField(required=False, input_formats=['%Y-%m-%d']) 
    SecuenciaEvento = forms.IntegerField(required=False)
    Dividendo = forms.DecimalField(initial=0.0, required=False, decimal_places=8)
    
    # ¡CAMBIO AQUÍ! ISFUT ahora es BooleanField
    ISFUT = forms.BooleanField(required=False) # 'required=False' permite que no esté chequeado
    
    # Campos visibles del (futuro) Modal 2
    ValorHistorico = forms.DecimalField(initial=0.0, required=False, decimal_places=8)
    FactorActualizacion = forms.DecimalField(initial=0.0, required=False, decimal_places=8)
    Anho = forms.IntegerField(required=False)

    # Campo extra (del mockup principal)
    Descripcion = forms.CharField(required=False)


class UsuarioForm(forms.Form):
    """
    Formulario para validar los datos al crear un nuevo usuario.
    """
    nombre = forms.CharField(max_length=200, required=True)
    correo = forms.EmailField(required=True)
    contrasena = forms.CharField(widget=forms.PasswordInput, required=True)
    # BooleanField maneja el 'true'/'false' del checkbox
    rol = forms.BooleanField(required=False) 

    # Validación extra: Asegurar que el correo no exista ya
    def clean_correo(self):
        correo = self.cleaned_data.get('correo')
        if usuarios.objects(correo=correo).first(): # Busca si ya existe en MongoDB
            raise forms.ValidationError("Este correo electrónico ya está registrado.")
        return correo
    

class UsuarioUpdateForm(forms.Form):
    """
    Formulario para validar los datos al modificar un usuario.
    """
    # Campo oculto para identificar al usuario
    user_id = forms.CharField(widget=forms.HiddenInput(), required=True) 
    
    nombre = forms.CharField(max_length=200, required=True)
    correo = forms.EmailField(required=True)
    
    # Contraseña opcional: si se envía, se actualiza.
    contrasena = forms.CharField(widget=forms.PasswordInput, required=False) 
    rol = forms.BooleanField(required=False)

    # Validación extra: Asegurar que el NUEVO correo no esté ya en uso por OTRO usuario
    def clean(self):
        cleaned_data = super().clean()
        correo = cleaned_data.get('correo')
        user_id = cleaned_data.get('user_id')

        # Busca si existe OTRO usuario con este correo
        existing_user = usuarios.objects(correo=correo, id__ne=user_id).first() # id__ne = "id not equal"
        if existing_user:
            self.add_error('correo', "Este correo electrónico ya está registrado por otro usuario.")
            # raise forms.ValidationError({"correo": "Este correo electrónico ya está registrado por otro usuario."})

        return cleaned_data