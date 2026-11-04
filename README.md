# Cash4You 💸

Sistema de gestão desenvolvido para auxiliar no gerenciamento de estabelecimentos comerciais, reunindo funcionalidades de controle de clientes, produtos, vendas, estoque e financeiro em uma única plataforma.

O Cash4You é uma evolução do projeto Cashly, desenvolvido utilizando Django e Python.

---

## 🚀 Funcionalidades

O sistema conta atualmente com os seguintes módulos:

- **Dashboard:** painel com indicadores gerais do estabelecimento, incluindo clientes, produtos, estoque e informações financeiras.
- **Clientes:** cadastro e gerenciamento de clientes.
- **Catálogo de produtos:** gerenciamento de produtos e informações de estoque.
- **Vendas:** registro e gerenciamento de vendas e respectivos itens.
- **Controle de estoque:** acompanhamento dos produtos e identificação de itens com estoque baixo.
- **Financeiro:** gerenciamento de contas a pagar e acompanhamento de pagamentos.
- **Agendamentos:** gerenciamento de horários e disponibilidade de funcionários.
- **Usuários e permissões:** gerenciamento de usuários e controle de acesso às funcionalidades do sistema.
- **Configurações:** gerenciamento de informações do estabelecimento.

## 🛠️ Tecnologias e bibliotecas

| Tecnologia | Finalidade |
|---|---|
| Python | Linguagem de programação principal |
| Django 5.2.17 | Framework backend |
| SQLite | Banco de dados para desenvolvimento (configuração padrão, caso mantida no projeto) |
| HTML5 | Estrutura das páginas |
| CSS3 | Estilização e interface |
| JavaScript | Interatividade no frontend |
| python-decouple | Gerenciamento de variáveis de ambiente |

Outras dependências podem ser consultadas no arquivo `requirements.txt`.

## 📋 Pré-requisitos

Antes de executar o projeto, é necessário possuir:

- Python 3.10 ou superior.
- Git.
- Pip (gerenciador de pacotes do Python).

## ⚙️ Instalação e configuração

### 1. Clonar o repositório

```bash
git clone https://github.com/Joao0liver/cash4you.git
```

Entre na pasta do projeto:

```bash
cd cash4you
```

### 2. Criar um ambiente virtual

Recomenda-se utilizar um ambiente virtual para isolar as dependências do projeto.

**Windows:**

```bash
python -m venv venv
venv\Scripts\activate
```

**Linux/macOS:**

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Instalar as dependências

Com o ambiente virtual ativado, execute:

```bash
pip install -r requirements.txt
```

### 4. Configurar as variáveis de ambiente

Caso necessário, configure as variáveis de ambiente utilizadas pelo projeto em um arquivo `.env`, respeitando as configurações definidas em `core/settings.py`.

Não compartilhe chaves secretas ou credenciais no repositório.

### 5. Executar as migrações

Crie as tabelas do banco de dados:

```bash
python manage.py migrate
```

### 6. Criar grupos e permissões

O projeto possui uma estrutura de grupos e permissões para controlar o acesso dos usuários às funcionalidades do sistema.

Para configurar os grupos e suas respectivas permissões, execute o comando de gerenciamento disponibilizado pelo projeto:

```bash
python manage.py criar_grupos
```

### 7. Criar um superusuário

Para acessar o painel administrativo do Django, crie um superusuário:

```bash
python manage.py createsuperuser
```

Siga as instruções exibidas no terminal.

### 8. Executar o servidor

Por fim, inicie o servidor de desenvolvimento:

```bash
python manage.py runserver
```

O sistema estará disponível em:

http://127.0.0.1:8000/

---

## 📁 Estrutura do projeto

O projeto está organizado em aplicações Django, cada uma responsável por um conjunto de funcionalidades.

```text
cash4you/
│
├── agenda/         # Controle de agenda (geral)
├── autenticacao/   # Login e logout
├── catalogo/       # Gerenciamento do catálogo de produtos e serviços
├── cliente/        # Cadastro e gerenciamento de clientes
├── configuracao/   # Configurações do estabelecimento
├── contapagar/     # Controle de gastos
├── core/           # Configurações principais do projeto
├── dashboard/      # Painel de indicadores
├── templates/      # Templates HTML reutilizáveis
├── usuario/        # Usuários, grupos e permissões
├── venda/          # Vendas e caixa
├── vendaitem/      # Itens relacionados às vendas
│
├── manage.py
├── requirements.txt
└── README.md
```

*Outras aplicações e diretórios podem ser adicionados conforme a evolução do projeto.*

## 🔐 Controle de acesso

O Cash4You utiliza o sistema de autenticação e autorização do Django para gerenciar os usuários e suas permissões.

O controle de acesso é organizado por grupos, permitindo definir quais funcionalidades cada categoria de usuário pode utilizar.

A criação e configuração dos grupos e permissões é realizada pelo comando de gerenciamento apresentado anteriormente.

Os grupos existentes no sistema são:

- Administrador
- Gerente
- Funcionário

## 👨‍💻 Desenvolvimento

Este projeto está em desenvolvimento e pode receber novas funcionalidades, melhorias e correções continuamente.

## 📄 Licença

Este projeto está temporariamente disponível publicamente no GitHub.