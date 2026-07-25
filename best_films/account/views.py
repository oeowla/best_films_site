from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django import forms


# ============================================================
# ФОРМА ДЛЯ ВХОДА ПО ПОЧТЕ
# Наследуемся от стандартной AuthenticationForm,
# но меняем поле username на EmailField, чтобы принимать почту
# ============================================================
class EmailAuthenticationForm(AuthenticationForm):
    username = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'placeholder': 'Почта',    # Текст-подсказка внутри поля
            'autofocus': True          # Автофокус при загрузке страницы
        }),
        label='Почта'
    )


# ============================================================
# ФОРМА ДЛЯ РЕГИСТРАЦИИ
# Создаём свою форму на основе модели User
# Поля: почта, логин, пароль, подтверждение пароля
# ============================================================
class RegistrationForm(forms.ModelForm):
    # Поле пароля — не из модели, добавляем вручную
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Пароль'}),
        label='Пароль'
    )
    # Поле подтверждения пароля
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Подтвердите пароль'}),
        label='Подтверждение пароля'
    )

    class Meta:
        model = User                                    # Используем встроенную модель пользователя
        fields = ['email', 'username']                  # Поля, которые берём из модели
        widgets = {
            'email': forms.EmailInput(attrs={'placeholder': 'Почта'}),
            'username': forms.TextInput(attrs={'placeholder': 'Логин'}),
        }
        labels = {
            'email': 'Почта',
            'username': 'Логин',
        }

    # Валидация почты — проверяем, что она не занята
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('Пользователь с такой почтой уже существует.')
        return email

    # Валидация логина — проверяем, что он не занят
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError('Пользователь с таким логином уже существует.')
        return username

    # Валидация подтверждения пароля — проверяем, что пароли совпадают
    def clean_password2(self):
        password = self.cleaned_data.get('password')
        password2 = self.cleaned_data.get('password2')
        if password and password2 and password != password2:
            raise forms.ValidationError('Пароли не совпадают.')
        return password2


# ============================================================
# ПРЕДСТАВЛЕНИЕ ВХОДА
# Принимает почту и пароль, ищет пользователя по почте,
# затем авторизует через стандартный authenticate
# ============================================================
def login_view(request):
    """Страница входа по почте"""
    # Если пользователь уже авторизован — сразу на профиль
    if request.user.is_authenticated:
        return redirect('profile')

    if request.method == 'POST':
        form = EmailAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('username')      # Здесь лежит почта
            password = form.cleaned_data.get('password')    # Пароль

            # Ищем пользователя по почте
            try:
                user_obj = User.objects.get(email=email)
                # Авторизуем через стандартный authenticate (он проверяет пароль)
                user = authenticate(
                    request,
                    username=user_obj.username,  # Передаём логин, не почту
                    password=password
                )
            except User.DoesNotExist:
                user = None
   
            if user is not None:
                login(request, user)
                messages.success(request, f'Добро пожаловать, {user.username}!')
                return redirect('profile')
        else:
            messages.error(request, 'Неверная почта или пароль.')
    else:
        form = EmailAuthenticationForm()

    return render(request, 'account/login.html', {'form': form})


# ============================================================
# ПРЕДСТАВЛЕНИЕ РЕГИСТРАЦИИ
# Создаёт нового пользователя: сохраняет почту, логин, пароль,
# затем сразу авторизует и перенаправляет на профиль
# ============================================================
def register_view(request):
    """Страница регистрации"""
    # Если уже авторизован — на профиль
    if request.user.is_authenticated:
        return redirect('profile')

    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            # Сохраняем пользователя, но пока без пароля (commit=False)
            user = form.save(commit=False)
            # Хешируем и устанавливаем пароль
            user.set_password(form.cleaned_data['password'])
            # Сохраняем в базу
            user.save()
            # Сразу авторизуем после регистрации
            login(request, user)
            messages.success(request, 'Регистрация успешна!')
            return redirect('profile')
        else:
            messages.error(request, 'Пожалуйста, исправьте ошибки.')
    else:
        form = RegistrationForm()

    return render(request, 'account/register.html', {'form': form})


# ============================================================
# ПРЕДСТАВЛЕНИЕ ПРОФИЛЯ
# Доступно только авторизованным пользователям (декоратор @login_required)
# Пока что просто пустая страница
# ============================================================
@login_required
def profile_view(request):
    """Страница профиля (пока пустая)"""
    return render(request, 'account/profile.html')
