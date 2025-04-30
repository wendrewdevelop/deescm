import re
import os
import tarfile
from datetime import datetime
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import logout
from django.urls import reverse
from django.views import View
from django.contrib import messages
from django.contrib.auth import login, authenticate
from django.utils.html import mark_safe
from pygments import highlight
from pygments.lexers import get_lexer_for_filename, guess_lexer
from pygments.formatters import HtmlFormatter
from .models import (
    AccountModel, 
    RepoModel, 
    RepoObjectModel,
    RepoIssueModel,
    RepoStarsModel,
    RepoForksModel
)


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
        user = AccountModel.objects.filter(
            id=request.user.id
        ).first()
        context["user_name"] = f'{user.first_name} {user.last_name}'
        return render(request, self.template_name, context)


class MyReposView(View):
    template_name = 'myrepos.html'

    def get(self, request, user_id, *args, **kwargs):
        context = {
            "title": "Meus repos"
        }
        repos = RepoModel.objects.filter(
            repo_owner=user_id
        )
        context["repos"] = repos
        context["user_name"] = f'{request.user.first_name} {request.user.last_name}'
        return render(request, self.template_name, context)

    def post(self, request, user_id, *args, **kwargs):
        owner = get_object_or_404(AccountModel, pk=user_id)

        # Captura campos do formulário
        name = request.POST.get('repo_name', '').strip()
        description = request.POST.get('repo_description', '').strip()

        # Validações básicas
        if not name:
            messages.error(request, "O nome do repositório não pode ficar vazio.")
            return redirect('myrepos', user_id=user_id)

        try:
            # Cria o repositório
            repo = RepoModel.objects.create(
                repo_name=name,
                repo_description=description,
                repo_owner=owner,
                # zip_file=zip_file,  # se existir
            )

            messages.success(
                request, 
                f"Repositório “{repo.repo_name}” criado com sucesso!"
            )
            return redirect('repo', repo_id=repo.id)
        except Exception as error:
            print(f"Erro::: {error}")
            return redirect('myrepos', user_id=user_id)


class RepoPageView(View):
    template_name = 'repopage.html'

    def get(self, request, repo_id, *args, **kwargs):
        repo = RepoModel.objects.filter(
            repo_id=repo_id,
        ).first()
        print(repo.repo_id)
        repo_object = RepoObjectModel.objects.filter(
            repo_link=repo.repo_id,
        ).first()
        print(repo_object)
        issues = RepoIssueModel.objects.filter(
            repo_link=repo.repo_id
        )
        context = {
            "title": f'{repo.repo_owner.first_name} {repo.repo_owner.last_name} – {repo.repo_name}',
            "repo": repo,
            "user_name": f'{repo.repo_owner.first_name} {repo.repo_owner.last_name}',
            "issues": issues
        }
        if repo_object:
            archive_path = os.path.join(
                settings.BASE_DIR, 
                'test_repos', 
                
                f'{repo_object.upload}'
            )
            with tarfile.open(archive_path, 'r:gz') as tar:
                members = [m for m in tar.getmembers() if m.isreg()]
                files = []
                for m in members:
                    files.append({
                        'name': m.name,
                        'size': m.size,
                        'modified': datetime.fromtimestamp(m.mtime).strftime('%Y-%m-%d %H:%M:%S')
                    })
            context = {
                "title": f'{repo.repo_owner.first_name} {repo.repo_owner.last_name} – {repo.repo_name}',
                "repo": repo,
                "user_name": f'{repo.repo_owner.first_name} {repo.repo_owner.last_name}',
                "files": files,
            }
        return render(request, self.template_name, context)
    
    def post(self, request, repo_id, *args, **kwargs):
        repo = RepoModel.objects.filter(
            repo_id=repo_id,
        ).first()

        if request.method == "POST":
            form_type = request.POST.get('form_type')
            print(form_type)
            if form_type == "issue":
                issue_title = request.POST.get('issue_title')
                print(issue_title)
                issue_description = request.POST.get('issue_description')
                print(issue_description)
                issue_status = request.POST.get('issue_status')
                print(issue_status)
                issue_repo_link = request.POST.get('issue_repo_link')
                print(issue_repo_link)
                issue_created_by = request.POST.get('issue_created_by')
                print(issue_created_by)
                try:
                    repo_instance = RepoModel.objects.get(
                        repo_id=issue_repo_link
                    )
                    account_instance = AccountModel.objects.get(
                        id=issue_created_by
                    )
                    issue = RepoIssueModel(
                        issue_title=issue_title, 
                        issue_description=issue_description,
                        issue_status=issue_status,
                        repo_link=repo_instance,
                        created_by=account_instance
                    )
                    issue.save()
                    print(issue)
                    return redirect('repo', repo_id=issue_repo_link)
                except Exception as error:
                    print(f'ERROR REGISTER USER::: {error}')
                    messages.error(
                        request, 
                        'Erro ao criar sua conta, tente novamente ou contate o suporte!', 
                        extra_tags='error'
                    )
                    return redirect('repo', repo_id=repo.repo_id)


class FileDetailView(View):
    template_name = 'file_detail.html'

    def get(self, request, repo_id, *args, **kwargs):
        repo_obj = RepoObjectModel.objects.filter(
            repo_link=repo_id
        ).first()

        file_path = request.GET.get('path')
        if not file_path:
            return render(request, self.template_name, {'error': 'Caminho do arquivo não informado.'})

        archive_path = os.path.join(settings.BASE_DIR, 'test_repos', f'{repo_obj.upload}')
        with tarfile.open(archive_path, 'r:gz') as tar:
            try:
                member = tar.getmember(file_path)
            except KeyError:
                return render(request, self.template_name, {'error': 'Arquivo não encontrado no repositório.'})
            f = tar.extractfile(member)  # :contentReference[oaicite:10]{index=10}
            raw = f.read().decode('utf-8', errors='replace')
            f.close()

        try:
            lexer = get_lexer_for_filename(file_path, stripall=True)
        except Exception:
            lexer = guess_lexer(raw)
        formatter = HtmlFormatter(linenos=True, cssclass="highlight")
        highlighted = highlight(raw, lexer, formatter)
        css_style = formatter.get_style_defs('.highlight')

        context = {
            'repo_owner': repo_obj.repo_link.repo_owner,
            'repo_id': repo_obj.repo_link.repo_id,
            'repo_name': repo_obj.repo_link.repo_name,
            'file_name': file_path,
            'highlighted_code': mark_safe(highlighted),
            'css_style': css_style,
        }
        return render(request, self.template_name, context)


class ProfileView(View):
    template_name = 'profile.html'

    def get(self, request, user_id, *args, **kwargs):
        context = {
            "title": "Perfil"
        }
        user_data = AccountModel.objects.filter(
            id=user_id
        ).first()
        print(user_data)
        context["first_name"] = user_data.first_name
        context["last_name"] = user_data.last_name
        context["email"] = user_data.email
        context["user_name"] = f'{user_data.first_name} {user_data.last_name}'
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
            form_type = request.POST.get('form_type')
            print(form_type)
            try:
                if form_type == "login":
                    email = request.POST.get('email')
                    print(email)
                    password = request.POST.get('password')
                    print(password)
                    user = authenticate(
                        request, 
                        username=email, 
                        password=password
                    )
                    print(user)
                    if user:
                        login(request, user)
                        return redirect('home')
                else:
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
                    return redirect('home')
            except Exception as error:
                print(f'ERROR REGISTER USER::: {error}')
                messages.error(
                    request, 
                    'Erro ao criar sua conta, tente novamente ou contate o suporte!', 
                    extra_tags='error'
                )
                return redirect('login')
    
        return render(request, self.template_name, context)
    

class IssueView(View):
    template_name = 'repopage.html'

    def post(self, request):
        context = {}
        
    
        return render(request, self.template_name, context)
           

def user_logout(request):
    """Desloga o usuário e redireciona para a página inicial."""
    logout(request)
    return redirect('index')


