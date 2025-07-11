import re
import os
import paramiko
import io
import zipfile
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

LANGUAGES = {
    '.py': 'Python',
    '.js': 'JavaScript',
    '.jsx': 'React',
    '.ts': 'TypeScript',
    '.java': 'Java',
    '.kt': 'Kotlin',
    '.cpp': 'C++',
    '.h': 'C/C++',
    '.c': 'C',
    '.cs': 'C#',
    '.php': 'PHP',
    '.rb': 'Ruby',
    '.go': 'Go',
    '.rs': 'Rust',
    '.swift': 'Swift',
    '.m': 'Objective-C',
    '.html': 'HTML',
    '.css': 'CSS',
    '.scss': 'Sass',
    '.sass': 'Sass',
    '.less': 'Less',
    '.md': 'Markdown',
    '.json': 'JSON',
    '.yml': 'YAML',
    '.yaml': 'YAML',
    '.xml': 'XML',
    '.sql': 'SQL',
    '.sh': 'Shell',
    '.bat': 'Batch',
    '.ps1': 'PowerShell',
    '.lua': 'Lua',
    '.pl': 'Perl',
    '.r': 'R',
    '.dart': 'Dart',
    '.hs': 'Haskell',
    '.exs': 'Elixir',
    '.vue': 'Vue',
    '.svelte': 'Svelte',
    '.tf': 'Terraform',
    '.dockerfile': 'Docker',
    '.dockerignore': 'Docker',
    '.gitignore': 'Git'
}
LANGUAGE_CSS_CLASSES = {
    'Python': 'python',
    'JavaScript': 'javascript',
    'TypeScript': 'typescript',
    'Java': 'java',
    'C++': 'cpp',
    'C#': 'csharp',
    'PHP': 'php',
    'Ruby': 'ruby',
    'Go': 'go',
    'Rust': 'rust',
    'HTML': 'html',
    'CSS': 'css',
    'Shell': 'shell',
    'Swift': 'swift',
    'Dart': 'dart',
    'Kotlin': 'kotlin',
    'Sass': 'sass',
    'Less': 'less',
    'Vue': 'vue',
    'React': 'react'
}


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

    def get_remote_zip(self, repo_id, branch, upload_hash):
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(
            hostname='192.168.3.60',
            username='servidor',
            password='0110'
        )
        sftp = ssh.open_sftp()

        zip_filename = f"{branch}-{upload_hash}.zip"
        remote_dir   = f"/home/servidor/repos/{repo_id}/{branch}"
        remote_path  = f"{remote_dir}/{zip_filename}"

        buf = io.BytesIO()
        sftp.getfo(remote_path, buf)
        buf.seek(0)

        sftp.close()
        ssh.close()
        return buf

    def get(self, request, repo_id, *args, **kwargs):
        repo = RepoModel.objects.filter(repo_id=repo_id).first()
        if not repo:
            return render(request, self.template_name, {"error": "Repositório não encontrado"})

        # repo_object = RepoObjectModel.objects.filter(repo_link=repo.repo_id).first()
        issues = RepoIssueModel.objects.filter(repo_link=repo.repo_id)

        branches = (
            RepoObjectModel.objects
            .filter(repo_link=repo.repo_id)
            .values_list('branch', flat=True)
            .distinct()
        )
        print(f'BRANCHS::: {branches}')
        selected_branch = request.GET.get('branch', 'main')
        print(f'SELECTED BRANCH::: {selected_branch}')
        # /home/servidor/repos/00ad54c4-c043-4aeb-9631-2da242722d0a/main
        print(f'/home/servidor/repos/{repo_id}/{selected_branch}')
        if selected_branch not in branches:
            selected_branch = branches.first() or 'main'

        try:
            repo_object = (
                RepoObjectModel.objects
                .filter(
                    repo_link=repo.repo_id, 
                    branch=selected_branch
                ).order_by('-created_at').first()
            )
            print(f"{selected_branch}-{repo_object.upload_hash}.zip")
        except Exception as error:
            print(f'Erro ao mudar de branch: {error}.')
            repo_object = None

        context = {
            "title": f'{repo.repo_owner.first_name} {repo.repo_owner.last_name} – {repo.repo_name}',
            "repo": repo,
            "user_name": f'{repo.repo_owner.first_name} {repo.repo_owner.last_name}',
            "issues": issues,
            "issues_count": issues.count(),
            "repo_obj": repo_object,
            'selected_branch': selected_branch,
            'branches': branches,
            "readme_content": None,
            "languages": set() 
        }

        if repo_object and repo_object.upload_hash:
            print(repo_object.upload_hash)
            try:
                print(f'REPO ID::: {repo_id}')
                print(f'SELECTED BRANCH::: {selected_branch}')
                print(f'UPLOAD HASH::: {repo_object.upload_hash}')
                zip_buffer = self.get_remote_zip(
                    repo_id, 
                    selected_branch, 
                    repo_object.upload_hash
                )
                print(f'ZIP BUFFER::: {zip_buffer}')
                
                if zip_buffer:
                    with zipfile.ZipFile(zip_buffer, 'r') as zipf:
                        languages = set()
                        # Busca por qualquer variação do nome README
                        readme_info = None
                        for file_info in zipf.infolist():
                            print(file_info.is_dir())
                            if file_info.filename.lower() == 'readme.md':
                                readme_info = file_info
                            if not file_info.is_dir():
                                filename = file_info.filename
                                _, ext = os.path.splitext(filename)
                                ext = ext.lower()

                                language = LANGUAGES.get(ext)
                                if language:
                                    languages.add(language)
                        
                        languages_with_classes = []
                        for lang in sorted(languages):
                            css_class = LANGUAGE_CSS_CLASSES.get(lang, 'default')
                            languages_with_classes.append({
                                'name': lang,
                                'css_class': css_class.lower()  # Usar lowercase para compatibilidade com CSS
                            })
                            
                        context["languages"] = languages_with_classes 

                        # Se encontrou o README
                        if readme_info and not readme_info.is_dir():
                            raw_readme = zipf.read(readme_info).decode('utf-8', errors='replace')
                            
                            # Realçar sintaxe do Markdown
                            try:
                                lexer = get_lexer_for_filename('README.md')
                            except Exception:
                                lexer = get_lexer_by_name('markdown')
                                
                            formatter = HtmlFormatter(style="friendly", linenos=False)
                            highlighted_readme = highlight(raw_readme, lexer, formatter)
                            
                            context["readme_content"] = mark_safe(highlighted_readme)
                            
                        # Listagem de arquivos mantida
                        files = []
                        for file_info in zipf.infolist():
                            if not file_info.is_dir():
                                files.append({
                                    'name': file_info.filename,
                                    'size': file_info.file_size,
                                    'modified': datetime(*file_info.date_time).strftime('%Y-%m-%d %H:%M:%S')
                                })
                        
                        context["files"] = files

            except Exception as e:
                print(f"Erro ao processar arquivo: {e}")
                context["error"] = "Erro ao carregar arquivos do repositório"

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

    def get_remote_zip(self, repo_id, branch, upload_hash):
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname='192.168.3.60', username='servidor', password='0110')
        sftp = ssh.open_sftp()

        zip_filename = f"{branch}-{upload_hash}.zip"
        remote_dir   = f"/home/servidor/repos/{repo_id}/{branch}"
        remote_path  = f"{remote_dir}/{zip_filename}"
        print(f"full remote path::: {remote_path}")

        buf = io.BytesIO()
        sftp.getfo(remote_path, buf)
        buf.seek(0)

        sftp.close()
        ssh.close()
        return buf

    def get(self, request, repo_id, *args, **kwargs):
        repo = RepoModel.objects.filter(repo_id=repo_id).first()
        if not repo:
            return render(request, self.template_name, {'error': 'Repositório não encontrado'})

        branches = RepoObjectModel.objects.filter(repo_link=repo.repo_id) \
                                          .values_list('branch', flat=True) \
                                          .distinct()
        selected_branch = request.GET.get('branch', 'main')
        if selected_branch not in branches:
            selected_branch = branches.first() or 'main'

        repo_obj = RepoObjectModel.objects.filter(
            repo_link=repo,
            branch=selected_branch
        ).order_by('-created_at').first()
        print(repo_id, 
                selected_branch, 
                repo_obj.upload_hash)
        if not repo_obj or not repo_obj.upload_hash:
            print("cai no not repo_obj or not repo_obj.upload_hash")
            return render(request, self.template_name, {
                'error': 'Nenhum upload para essa branch',
                'branches': branches,
                'selected_branch': selected_branch,
                'repo': repo,
            })

        file_path = request.GET.get('path')
        if not file_path:
            print("cai no not file_path")
            return render(request, self.template_name, {
                'error': 'Caminho do arquivo não informado',
                'branches': branches,
                'selected_branch': selected_branch,
                'repo': repo,
                'repo_owner': repo.repo_owner,
                'repo_id': repo.repo_id,
                'repo_name': repo.repo_name,
                'selected_branch': selected_branch,
                'file_name': file_path,
                'user_id': repo.repo_owner.pk,
                'user_name': f"{repo.repo_owner.first_name} {repo.repo_owner.last_name}",
            })

        try:
            zip_buf = self.get_remote_zip(
                repo_id, 
                selected_branch, 
                repo_obj.upload_hash
            )
            with zipfile.ZipFile(zip_buf, 'r') as zipf:
                info = zipf.getinfo(file_path)
                if info.is_dir():
                    raise KeyError(f"{file_path} é um diretório")
                raw = zipf.read(file_path).decode('utf-8', errors='replace')
        except KeyError:
            return render(request, self.template_name, {
                'error': 'Arquivo não encontrado',
                'branches': branches,
                'selected_branch': selected_branch,
                'repo': repo,
            })
        except Exception as e:
            return render(request, self.template_name, {
                'error': f"Falha ao carregar arquivo: {e}",
                'branches': branches,
                'selected_branch': selected_branch,
                'repo': repo,
            })

        try:
            lexer = get_lexer_for_filename(file_path)
        except Exception:
            lexer = guess_lexer(raw)
        formatter = HtmlFormatter(linenos=False, cssclass="highlight", style="friendly")
        highlighted = highlight(raw, lexer, formatter)
        css_style = formatter.get_style_defs('.highlight')

        context = {
            'repo_owner': repo.repo_owner,
            'repo_id': repo.repo_id,
            'repo_name': repo.repo_name,
            'branches': branches,
            'selected_branch': selected_branch,
            'file_name': file_path,
            'highlighted_code': mark_safe(highlighted),
            'css_style': css_style,
            'user_id': repo.repo_owner.pk,
            'user_name': f"{repo.repo_owner.first_name} {repo.repo_owner.last_name}",
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
        context["user_id"] = user_id
        context["user_name"] = f'{user_data.first_name} {user_data.last_name}'
        return render(request, self.template_name, context)
    
    def post(self, request, user_id, *args, **kwargs):
        if request.method == "POST":
            first_name = request.POST.get('first_name')
            print(first_name)
            last_name = request.POST.get('last_name')
            print(last_name)
            email = request.POST.get('email')
            print(email)
            try:
                user_instance = AccountModel.objects.get(
                    id=user_id
                )
                user_instance.first_name = first_name
                user_instance.last_name = last_name
                user_instance.email = email
                user_instance.save()
                print(user_instance)
                return redirect('profile', user_id=user_id)
            except Exception as error:
                messages.error(
                    request, 
                    'Erro ao atualizar os dados, tente novamente ou contate o suporte!', 
                    extra_tags='error'
                )
                return redirect('profile', user_id=user_id)
    

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


