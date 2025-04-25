import re
from datetime import datetime
from django.shortcuts import render, redirect
from django.contrib.auth import logout
from django.urls import reverse
from django.views import View
from django.contrib import messages
from django.contrib.auth import login, authenticate
from .models import AccountModel


class IndexView(View):
    template_name = 'index.html'

    def get(self, request):
        context = {
            "title": "Dee Source code manager"
        }
        return render(request, self.template_name, context)
    

class HomePageView(View):
    template_name = 'homepage.html'

    def get(self, request):
        context = {
            "title": "Página inicial"
        }
        return render(request, self.template_name, context)


class MyReposView(View):
    template_name = 'myrepos.html'

    def get(self, request):
        context = {
            "title": "Explore o Dee"
        }
        return render(request, self.template_name, context)


class RepoPageView(View):
    template_name = 'repopage.html'

    def get(self, request):
        context = {
            "title": "<repo_name:str>"
        }
        return render(request, self.template_name, context)
    

class LoginView(View):
    template_name = 'login_signup.html'

    def get(self, request):
        context = {
            "title": "Entre ou cadastre-se"
        }
        return render(request, self.template_name, context)

    def post(self, request):
        context = {}
        if request.method == "POST":
            try:
                email = request.POST.get("email")
                password = request.POST.get("password")
                phone = re.sub(r'[^\d]', '', request.POST.get("phone"))
                birthday = request.POST.get("birthday")
                nickname = request.POST.get("nickname")
                first_name = request.POST.get("first_name")
                last_name = request.POST.get("last_name")

                birthday_datetime = datetime.strptime(birthday, "%d/%m/%Y")
                birthday_formatted = birthday_datetime.strftime("%Y-%m-%d")

                user = AccountModel.objects.create(
                    email=email,
                    password=password,
                    phone=phone,
                    birthday=birthday_formatted,
                    nickname=nickname,
                    first_name=first_name,
                    last_name=last_name
                )
                print(user)
                user.set_password(password)
                user.save()
                login(request, user)
                
                account_id = user.pk 
                print(account_id)
                dashboard_url = reverse(
                    'dashboard', 
                    kwargs={
                        'account_id': account_id
                    }
                )
                return redirect(dashboard_url)
            except Exception as error:
                print(f'ERROR REGISTER USER::: {error}')
                messages.error(
                    request, 
                    'Erro ao criar sua conta, tente novamente ou contate o suporte!', 
                    extra_tags='error'
                )
                return redirect('register')

        
        return render(request, self.template_name, context)
    

            

def user_logout(request):
    """Desloga o usuário e redireciona para a página inicial."""
    logout(request)
    return redirect('index')  # Substitua 'home' pelo nome da sua URL desejada


