# gestion/forms.py
from django import forms
from django.contrib.auth.models import User, Group
from django.contrib.auth.forms import UserCreationForm

ROLE_CHOICES = (
    ("CLIENTE", "Cliente"),
    ("BIBLIOTECARIO", "Bibliotecario"),
    ("BODEGUERO", "Bodeguero"),
)

class ClienteRegistroForm(UserCreationForm):
    first_name = forms.CharField(label="Nombre", max_length=150)
    last_name = forms.CharField(label="Apellido", max_length=150)
    email = forms.EmailField(label="Email (opcional)", required=False)

    class Meta:
        model = User
        fields = ("username", "first_name", "last_name", "email", "password1", "password2")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        user.email = self.cleaned_data.get("email", "")
        if commit:
            user.save()
            grupo = Group.objects.get(name="CLIENTE")
            user.groups.add(grupo)
        return user

class AdminCrearUsuarioForm(UserCreationForm):
    first_name = forms.CharField(label="Nombre", max_length=150)
    last_name = forms.CharField(label="Apellido", max_length=150)
    email = forms.EmailField(label="Email (opcional)", required=False)
    rol = forms.ChoiceField(choices=ROLE_CHOICES)

    class Meta:
        model = User
        fields = ("username", "first_name", "last_name", "email", "rol", "password1", "password2")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        user.email = self.cleaned_data.get("email", "")
        if commit:
            user.save()
            grupo = Group.objects.get(name=self.cleaned_data["rol"])
            user.groups.add(grupo)
        return user
