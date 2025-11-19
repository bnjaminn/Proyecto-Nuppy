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
    Origen = forms.CharField(required=False)  # Campo para el origen (Corredor, CSV)
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
    contrasena = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Ingrese su contraseña'}),
        required=True,
        min_length=8,
        help_text="La contraseña debe tener al menos 8 caracteres, incluir mayúsculas, minúsculas y un símbolo especial."
    )
    confirmar_contrasena = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Confirme su contraseña'}),
        required=True,
        label="Confirmar Contraseña"
    )
    # BooleanField maneja el 'true'/'false' del checkbox para decidir que sea admin o no
    rol = forms.BooleanField(required=False) 

    def clean_contrasena(self):
        """Valida que la contraseña cumpla con los requisitos de seguridad"""
        contrasena = self.cleaned_data.get('contrasena')
        
        if not contrasena:
            return contrasena
        
        # Verificar longitud mínima
        if len(contrasena) < 8:
            raise forms.ValidationError("La contraseña debe tener al menos 8 caracteres.")
        
        # Verificar que tenga al menos una mayúscula
        if not any(c.isupper() for c in contrasena):
            raise forms.ValidationError("La contraseña debe contener al menos una letra mayúscula.")
        
        # Verificar que tenga al menos una minúscula
        if not any(c.islower() for c in contrasena):
            raise forms.ValidationError("La contraseña debe contener al menos una letra minúscula.")
        
        # Verificar que tenga al menos un símbolo especial
        import string
        simbolos_especiales = string.punctuation  # !"#$%&'()*+,-./:;<=>?@[\]^_`{|}~
        if not any(c in simbolos_especiales for c in contrasena):
            raise forms.ValidationError("La contraseña debe contener al menos un símbolo especial (!@#$%^&*()_+-=[]{}|;:,.<>?).")
        
        return contrasena
    
    def clean(self):
        """Valida que ambas contraseñas coincidan"""
        cleaned_data = super().clean()
        contrasena = cleaned_data.get('contrasena')
        confirmar_contrasena = cleaned_data.get('confirmar_contrasena')
        
        if contrasena and confirmar_contrasena:
            if contrasena != confirmar_contrasena:
                raise forms.ValidationError({
                    'confirmar_contrasena': "Las contraseñas no coinciden. Por favor, verifique que ambas sean iguales."
                })
        
        return cleaned_data

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
    contrasena = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Dejar en blanco para no cambiar'}),
        required=False,
        help_text="Si desea cambiar la contraseña, debe tener al menos 8 caracteres, incluir mayúsculas, minúsculas y un símbolo especial."
    )
    confirmar_contrasena = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Confirme la nueva contraseña'}),
        required=False,
        label="Confirmar Nueva Contraseña"
    )
    rol = forms.BooleanField(required=False)

    def clean_contrasena(self):
        """Valida que la contraseña cumpla con los requisitos de seguridad si se proporciona"""
        contrasena = self.cleaned_data.get('contrasena')
        
        # Si no se proporciona contraseña, está bien (es opcional)
        if not contrasena or contrasena.strip() == '':
            return contrasena
        
        # Si se proporciona contraseña, debe cumplir los requisitos
        # Verificar longitud mínima
        if len(contrasena) < 8:
            raise forms.ValidationError("La contraseña debe tener al menos 8 caracteres.")
        
        # Verificar que tenga al menos una mayúscula
        if not any(c.isupper() for c in contrasena):
            raise forms.ValidationError("La contraseña debe contener al menos una letra mayúscula.")
        
        # Verificar que tenga al menos una minúscula
        if not any(c.islower() for c in contrasena):
            raise forms.ValidationError("La contraseña debe contener al menos una letra minúscula.")
        
        # Verificar que tenga al menos un símbolo especial
        import string
        simbolos_especiales = string.punctuation  # !"#$%&'()*+,-./:;<=>?@[\]^_`{|}~
        if not any(c in simbolos_especiales for c in contrasena):
            raise forms.ValidationError("La contraseña debe contener al menos un símbolo especial (!@#$%^&*()_+-=[]{}|;:,.<>?).")
        
        return contrasena

    # Validación extra: Asegurar que el NUEVO correo no esté ya en uso por OTRO usuario
    def clean(self):
        cleaned_data = super().clean()
        correo = cleaned_data.get('correo')
        user_id = cleaned_data.get('user_id')
        contrasena = cleaned_data.get('contrasena')
        confirmar_contrasena = cleaned_data.get('confirmar_contrasena')

        # Busca si existe OTRO usuario con este correo
        existing_user = usuarios.objects(correo=correo, id__ne=user_id).first() #Busca si existe OTRO usuario (id__ne = id not equal) con este correo
        if existing_user:
            self.add_error('correo', "Este correo electrónico ya está registrado por otro usuario.")
        
        # Validar que si se proporciona contraseña, también se proporcione confirmación y que coincidan
        if contrasena and contrasena.strip() != '':
            if not confirmar_contrasena or confirmar_contrasena.strip() == '':
                self.add_error('confirmar_contrasena', "Debe confirmar la nueva contraseña.")
            elif contrasena != confirmar_contrasena:
                self.add_error('confirmar_contrasena', "Las contraseñas no coinciden. Por favor, verifique que ambas sean iguales.")
        elif confirmar_contrasena and confirmar_contrasena.strip() != '':
            # Si se proporciona confirmación pero no contraseña, es un error
            self.add_error('contrasena', "Debe ingresar la nueva contraseña si desea cambiarla.")
        
        return cleaned_data

#formulario para ingresar factores (segunda ventana modal)
class FactoresForm(forms.Form):
    # Campo oculto para el ID de la calificación
    calificacion_id = forms.CharField(widget=forms.HiddenInput(), required=True)
    
    # Factores del 8 al 37 (30 campos total)
    # Todos son DecimalField con 8 decimales, opcionales, inicializados en 0
    Factor08 = forms.DecimalField(initial=0.0, required=False, decimal_places=8, max_digits=17)
    Factor09 = forms.DecimalField(initial=0.0, required=False, decimal_places=8, max_digits=17)
    Factor10 = forms.DecimalField(initial=0.0, required=False, decimal_places=8, max_digits=17)
    Factor11 = forms.DecimalField(initial=0.0, required=False, decimal_places=8, max_digits=17)
    Factor12 = forms.DecimalField(initial=0.0, required=False, decimal_places=8, max_digits=17)
    Factor13 = forms.DecimalField(initial=0.0, required=False, decimal_places=8, max_digits=17)
    Factor14 = forms.DecimalField(initial=0.0, required=False, decimal_places=8, max_digits=17)
    Factor15 = forms.DecimalField(initial=0.0, required=False, decimal_places=8, max_digits=17)
    Factor16 = forms.DecimalField(initial=0.0, required=False, decimal_places=8, max_digits=17)
    Factor17 = forms.DecimalField(initial=0.0, required=False, decimal_places=8, max_digits=17)
    Factor18 = forms.DecimalField(initial=0.0, required=False, decimal_places=8, max_digits=17)
    Factor19 = forms.DecimalField(initial=0.0, required=False, decimal_places=8, max_digits=17)
    Factor20 = forms.DecimalField(initial=0.0, required=False, decimal_places=8, max_digits=17)
    Factor21 = forms.DecimalField(initial=0.0, required=False, decimal_places=8, max_digits=17)
    Factor22 = forms.DecimalField(initial=0.0, required=False, decimal_places=8, max_digits=17)
    Factor23 = forms.DecimalField(initial=0.0, required=False, decimal_places=8, max_digits=17)
    Factor24 = forms.DecimalField(initial=0.0, required=False, decimal_places=8, max_digits=17)
    Factor25 = forms.DecimalField(initial=0.0, required=False, decimal_places=8, max_digits=17)
    Factor26 = forms.DecimalField(initial=0.0, required=False, decimal_places=8, max_digits=17)
    Factor27 = forms.DecimalField(initial=0.0, required=False, decimal_places=8, max_digits=17)
    Factor28 = forms.DecimalField(initial=0.0, required=False, decimal_places=8, max_digits=17)
    Factor29 = forms.DecimalField(initial=0.0, required=False, decimal_places=8, max_digits=17)
    Factor30 = forms.DecimalField(initial=0.0, required=False, decimal_places=8, max_digits=17)
    Factor31 = forms.DecimalField(initial=0.0, required=False, decimal_places=8, max_digits=17)
    Factor32 = forms.DecimalField(initial=0.0, required=False, decimal_places=8, max_digits=17)
    Factor33 = forms.DecimalField(initial=0.0, required=False, decimal_places=8, max_digits=17)
    Factor34 = forms.DecimalField(initial=0.0, required=False, decimal_places=8, max_digits=17)
    Factor35 = forms.DecimalField(initial=0.0, required=False, decimal_places=8, max_digits=17)
    Factor36 = forms.DecimalField(initial=0.0, required=False, decimal_places=8, max_digits=17)
    Factor37 = forms.DecimalField(initial=0.0, required=False, decimal_places=8, max_digits=17)
    
    # Campos adicionales según mockup
    RentasExentas = forms.DecimalField(initial=0.0, required=False, decimal_places=8, max_digits=17)
    Factor19A = forms.DecimalField(initial=0.0, required=False, decimal_places=8, max_digits=17)

# Formulario para ingresar MONTOS (no factores)
# El usuario ingresa montos en dinero, y el sistema calcula los factores automáticamente
class MontosForm(forms.Form):
    # Campos generales
    Ejercicio = forms.IntegerField(required=True)
    Instrumento = forms.CharField(max_length=50, required=False)
    Mercado = forms.CharField(required=False)
    Origen = forms.CharField(required=False)
    
    # Montos del 8 al 37 (el usuario ingresa dinero, no factores)
    # Estos son los MONTOS que se usarán para calcular los factores
    monto_8 = forms.DecimalField(initial=0.0, required=False, decimal_places=2, max_digits=20, label="Monto 8")
    monto_9 = forms.DecimalField(initial=0.0, required=False, decimal_places=2, max_digits=20, label="Monto 9")
    monto_10 = forms.DecimalField(initial=0.0, required=False, decimal_places=2, max_digits=20, label="Monto 10")
    monto_11 = forms.DecimalField(initial=0.0, required=False, decimal_places=2, max_digits=20, label="Monto 11")
    monto_12 = forms.DecimalField(initial=0.0, required=False, decimal_places=2, max_digits=20, label="Monto 12")
    monto_13 = forms.DecimalField(initial=0.0, required=False, decimal_places=2, max_digits=20, label="Monto 13")
    monto_14 = forms.DecimalField(initial=0.0, required=False, decimal_places=2, max_digits=20, label="Monto 14")
    monto_15 = forms.DecimalField(initial=0.0, required=False, decimal_places=2, max_digits=20, label="Monto 15")
    monto_16 = forms.DecimalField(initial=0.0, required=False, decimal_places=2, max_digits=20, label="Monto 16")
    monto_17 = forms.DecimalField(initial=0.0, required=False, decimal_places=2, max_digits=20, label="Monto 17")
    monto_18 = forms.DecimalField(initial=0.0, required=False, decimal_places=2, max_digits=20, label="Monto 18")
    monto_19 = forms.DecimalField(initial=0.0, required=False, decimal_places=2, max_digits=20, label="Monto 19")
    monto_20 = forms.DecimalField(initial=0.0, required=False, decimal_places=2, max_digits=20, label="Monto 20")
    monto_21 = forms.DecimalField(initial=0.0, required=False, decimal_places=2, max_digits=20, label="Monto 21")
    monto_22 = forms.DecimalField(initial=0.0, required=False, decimal_places=2, max_digits=20, label="Monto 22")
    monto_23 = forms.DecimalField(initial=0.0, required=False, decimal_places=2, max_digits=20, label="Monto 23")
    monto_24 = forms.DecimalField(initial=0.0, required=False, decimal_places=2, max_digits=20, label="Monto 24")
    monto_25 = forms.DecimalField(initial=0.0, required=False, decimal_places=2, max_digits=20, label="Monto 25")
    monto_26 = forms.DecimalField(initial=0.0, required=False, decimal_places=2, max_digits=20, label="Monto 26")
    monto_27 = forms.DecimalField(initial=0.0, required=False, decimal_places=2, max_digits=20, label="Monto 27")
    monto_28 = forms.DecimalField(initial=0.0, required=False, decimal_places=2, max_digits=20, label="Monto 28")
    monto_29 = forms.DecimalField(initial=0.0, required=False, decimal_places=2, max_digits=20, label="Monto 29")
    monto_30 = forms.DecimalField(initial=0.0, required=False, decimal_places=2, max_digits=20, label="Monto 30")
    monto_31 = forms.DecimalField(initial=0.0, required=False, decimal_places=2, max_digits=20, label="Monto 31")
    monto_32 = forms.DecimalField(initial=0.0, required=False, decimal_places=2, max_digits=20, label="Monto 32")
    monto_33 = forms.DecimalField(initial=0.0, required=False, decimal_places=2, max_digits=20, label="Monto 33")
    monto_34 = forms.DecimalField(initial=0.0, required=False, decimal_places=2, max_digits=20, label="Monto 34")
    monto_35 = forms.DecimalField(initial=0.0, required=False, decimal_places=2, max_digits=20, label="Monto 35")
    monto_36 = forms.DecimalField(initial=0.0, required=False, decimal_places=2, max_digits=20, label="Monto 36")
    monto_37 = forms.DecimalField(initial=0.0, required=False, decimal_places=2, max_digits=20, label="Monto 37")