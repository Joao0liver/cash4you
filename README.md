# Cash4You

Sistema web de gestão para pequenos negócios, desenvolvido com Django. O Cash4You reúne cadastros, controle de estoque, vendas, agenda, relatórios e indicadores em um único painel.

## Sumário

- [Funcionalidades](#funcionalidades)
- [Regras de negócio](#regras-de-negócio)
- [Tecnologias](#tecnologias)
- [Configuração e execução](#configuração-e-execução)
- [Testes](#testes)

## Funcionalidades

### Dashboard

- Indicadores do dia: valor total vendido, número de vendas, quantidade de clientes cadastrados e produtos com estoque baixo.
- Os cartões de vendas levam ao Registro de Vendas; o cartão de clientes abre a Carteira de Clientes; o cartão de estoque baixo abre Produtos no Estoque. Dicas explicam os destinos.
- Resumo diário dos três produtos mais vendidos e das três formas de pagamento com maior valor no dia.
- Lista de produtos que precisam de reposição.
- Análises gerais com gráficos de produtos mais vendidos, serviços mais prestados, formas de pagamento e situação do estoque.
- Comparativo de vendas dos últimos três dias, semanas ou meses.

### Cadastros

- CRUD (criar, listar, editar e excluir) de Produtos no Estoque, Serviços Prestados e Carteira de Clientes.
- Busca e ordenação em produtos e serviços, e busca de clientes.
- Produtos e serviços incluem custo direto, despesas variáveis, lucro desejado, sugestão de preço de venda e cálculo de lucro líquido quando os dados necessários estão cadastrados.
- A página **Cadastrar** apresenta atalhos para os cadastros e para a ferramenta de precificação.

### Frente de Caixa e Registro de Vendas

- Inclusão de produtos e serviços no carrinho, alteração de quantidades e remoção de itens.
- Validação de estoque no carrinho e novamente ao finalizar a venda.
- Pagamento em dinheiro, cartão de crédito, cartão de débito ou Pix. Para dinheiro, o valor recebido deve cobrir o total; o troco é calculado.
- Nome e telefone do cliente são opcionais. O telefone habilita a preparação de um comprovante para WhatsApp.
- A mensagem do comprovante pode incluir nome do estabelecimento, horário de funcionamento e endereço, configurados pela engrenagem na Frente de Caixa.
- Os dados do estabelecimento ficam salvos para vendas futuras e são copiados para cada venda, preservando as informações usadas em comprovantes anteriores.
- A Frente de Caixa mostra as três vendas mais recentes, com atalhos para seus detalhes e para o registro completo.
- O Registro de Vendas permite filtrar por várias formas de pagamento e por intervalo de datas inclusivo, em conjunto. O seletor de pagamento tem altura compacta, igual aos campos de data; use Ctrl (Windows) ou Command (Mac) para selecionar mais de uma forma. É possível limpar os filtros.
- Vendas podem ser consultadas, editadas e excluídas. A edição recalcula itens e estoque; excluir uma venda repõe as unidades vendidas.

### Agenda

- Cadastro, consulta, edição e exclusão de agendamentos.
- Horários de atendimento em blocos de 30 minutos, das 07:00 às 23:00.
- Horários já reservados para a data não podem ser selecionados novamente.
- Nome e telefone são obrigatórios; e-mail e serviços relacionados são opcionais.
- Link para iniciar conversa pelo WhatsApp a partir do telefone do agendamento.

### Relatórios

- **Relatório de caixa:** consulta as vendas de uma data, com horário, itens, quantidades, pagamento e totais.
- **Relatório de estoque:** lista produtos, quantidades, preços e estado do estoque.
- Ambos oferecem impressão com tipografia e espaçamento compactos, tabelas preparadas para múltiplas páginas e ocultação de navegação e controles.
- O relatório de caixa detalha cada item no impresso com tipo, quantidade, preço unitário e subtotal.

## Regras de negócio

### Navegação

- As áreas principais são Dashboard, Cadastrar, Vendas, Agenda e Relatórios.
- Os grupos de navegação permanecem abertos durante a navegação interna e se ajustam à seção atual; selecionar outro grupo fecha o anterior.
- Clicar em **Cadastrar** abre a página com atalhos de cadastro. A seta ao lado expande os links diretos para Produtos no Estoque, Serviços Prestados, Carteira de Clientes e Precificar.
- Clicar em **Vendas** abre diretamente a Frente de Caixa. Na navegação, somente **Frente de Caixa** fica selecionada; a seta abre os atalhos para a Frente de Caixa e o Registro de Vendas.
- Títulos e opções visíveis usam os nomes **Produtos no Estoque**, **Serviços Prestados**, **Carteira de Clientes**, **Frente de Caixa** e **Registro de Vendas**. Nomes internos de rotas e modelos permanecem técnicos.

### Clientes

- Nome, CPF e telefone são obrigatórios.
- CPF deve ter 11 dígitos e passar pela validação dos dígitos verificadores.
- Telefone deve conter números e DDD, com pelo menos 10 dígitos.
- A busca da carteira de clientes permite localizar por nome, CPF ou telefone.

### Produtos, serviços e precificação

- Produtos usam custo direto, preço de venda, quantidade, percentual de despesas variáveis e lucro desejado.
- Serviços usam custo direto por realização, preço de venda, despesas variáveis e lucro desejado.
- Fórmula para sugestão de preço:

  `Preço sugerido = Custo direto / (1 - (Despesas variáveis % + Lucro desejado %) / 100)`

- A soma de despesas variáveis e lucro desejado precisa ser menor que 100%; caso contrário, a fórmula não tem denominador positivo válido.
- O preço sugerido pode ser alterado pelo usuário.
- Lucro líquido:

  `Lucro líquido = Preço de venda - Custo direto - (Preço de venda × Despesas variáveis % / 100)`

- Registros antigos sem os dados necessários permanecem sem lucro calculado; não são usados valores presumidos.
- A listagem de Produtos no Estoque destaca a linha e apresenta o selo **Estoque baixo** quando a quantidade é menor que 5 unidades (0 a 4). Exatamente 5 unidades não recebe esse alerta na listagem.

### Agenda

- Existem 32 blocos de meia hora por dia, do período 07:00–07:30 até 22:30–23:00.
- Cada combinação de data e horário inicial só pode ser reservada uma vez, com validação no servidor e proteção contra duplicidade no banco.
- Excluir um agendamento libera seus horários.

### Vendas e estoque

- Os itens vendidos registram tipo, descrição, preço unitário, quantidade e subtotal, preservando os dados históricos da venda.
- O estoque de produtos é decrementado ao concluir uma venda; serviços não alteram estoque.
- Validações e mudanças de venda/estoque ocorrem no servidor e as operações relevantes são atômicas.
- Na edição da venda, os itens são recalculados usando os preços atuais dos cadastros. O estoque consumido pela venda original é considerado ao validar a nova quantidade.
- Em pagamentos que não sejam em dinheiro, valor recebido e troco não se aplicam.

### Dashboard e limites de estoque

- Os indicadores diários usam a data local da aplicação (`America/Sao_Paulo`).
- Os gráficos gerais mostram até três itens/formas conforme os maiores agregados.
- O dashboard considera baixo estoque estritamente abaixo de 5 unidades (0 a 4).
- O relatório de estoque considera “Baixo” de 1 a 5 unidades, inclusive; quantidade zero é “Em falta”; acima de 5 é “Adequado”.

### Apresentação e comprovantes

- A interface e as mensagens usam português brasileiro e moeda em reais.
- O comprovante para WhatsApp é preparado somente quando há telefone informado; o envio precisa ser confirmado pelo usuário no WhatsApp.
- A mensagem inclui saudação, data completa, itens e subtotais, valor total, forma de pagamento e, quando for em dinheiro, troco. Nome, horário e endereço do estabelecimento são acrescentados quando configurados.
- Dados ausentes não devem ser inventados. Validações importantes também devem existir no servidor.

## Tecnologias

- Python e Django (versões definidas em [`requirements.txt`](./requirements.txt)).
- SQLite como banco de dados padrão.
- Bootstrap para interface e Chart.js para gráficos do dashboard.
- As bibliotecas Bootstrap e Chart.js são carregadas por CDN; é necessária conexão com a internet para esses recursos visuais.

## Configuração e execução

Requisitos: Python compatível com as dependências do projeto e PowerShell (os comandos abaixo são para Windows).

1. Na pasta do projeto, crie e ative um ambiente virtual:

   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

2. Instale as dependências:

   ```powershell
   python -m pip install -r requirements.txt
   ```

3. Crie um arquivo `.env` na raiz do projeto com os valores locais:

   ```dotenv
   SECRET_KEY=coloque-uma-chave-secreta-local
   DEBUG=True
   ALLOWED_HOSTS=localhost,127.0.0.1
   ```

   Gere uma chave secreta própria para cada ambiente e não a publique nem a versione.

4. Aplique as migrações e inicie o servidor:

   ```powershell
   python manage.py migrate
   python manage.py runserver
   ```

5. Acesse `http://127.0.0.1:8000/`.

Para acessar a interface administrativa do Django, crie um usuário administrador:

```powershell
python manage.py createsuperuser
```

## Testes

Execute a suíte automatizada na raiz do projeto:

```powershell
python manage.py test
```

Verifique se há migrações de modelos ainda não geradas:

```powershell
python manage.py makemigrations --check --dry-run
```
