# Cash4You — Regras de negócio e funcionalidades

Este documento reúne em um só lugar os requisitos, regras de negócio e comportamentos funcionais definidos durante a construção do Cash4You. Serve como referência para manter ou ampliar o sistema sem perder as decisões já tomadas.

## 1. Navegação e comportamento geral

- O menu lateral organiza as áreas principais: **Dashboards**, **Cadastrar**, **Vendas**, **Agenda** e **Relatórios**.
- **Cadastrar**, **Vendas**, **Agenda** e **Relatórios** são grupos recolhíveis. Clicar no grupo abre ou recolhe suas opções; abrir outro grupo recolhe o que estava aberto; escolher uma opção interna também recolhe os grupos.
- O grupo **Cadastrar** contém a visão geral, Produtos, Serviços, Clientes e Precificar.
- O grupo **Vendas** contém Caixa e Histórico de vendas.
- O grupo **Agenda** contém Agendamentos e Novo agendamento.
- O grupo **Relatórios** contém Relatório de caixa e Relatório de estoque.
- O layout comum mantém o menu lateral, cabeçalho e rodapé estáticos. A área de conteúdo é rolável, e o título inicial da página permanece visível durante a rolagem.
- Valores monetários são apresentados em reais (R$), no formato brasileiro, com duas casas decimais.
- Operações destrutivas devem ser confirmadas e feitas por envio POST, e não apenas por abertura de um link.

## 2. Cadastros

Os cadastros de Clientes, Produtos e Serviços têm operações de criar, listar, editar e excluir, além de formulários com validação e mensagens apropriadas.

### 2.1 Clientes

- Nome, CPF e telefone são obrigatórios.
- O nome não pode ficar vazio após remover espaços nas extremidades.
- O CPF deve conter exatamente 11 dígitos numéricos e passar pela validação dos dígitos verificadores. Sequências repetidas, como `11111111111`, não são válidas.
- O CPF é validado no navegador durante a digitação e novamente no servidor. A validação do navegador é apenas uma conveniência; não substitui a validação do servidor.
- O telefone deve conter apenas dígitos e pelo menos 10 caracteres.
- A listagem permite localizar o cliente por nome, CPF ou telefone. Pontuação digitada na busca não impede a busca pelos números correspondentes.
- O número de telefone na listagem é um link para iniciar uma conversa no WhatsApp, com o código de país do Brasil (`55`).

### 2.2 Produtos

- Cada produto possui descrição, custo/preço de custo, preço de venda, quantidade em estoque, despesas variáveis percentuais e percentual de lucro desejado.
- A listagem permite filtrar por descrição, custo, preço de venda ou quantidade.
- A ordenação da listagem é aplicada imediatamente ao selecionar:
  - Descrição crescente (A–Z) ou decrescente (Z–A).
  - Quantidade crescente (menor–maior) ou decrescente (maior–menor).
- O campo de busca deve continuar aplicado quando a ordenação é alterada.
- Custos e preços são mostrados como moeda brasileira.
- Os valores numéricos da tabela ficam centralizados; descrição permanece à esquerda e ações à direita.
- Os cabeçalhos de tabela apresentam explicações curtas ao passar o cursor.
- A listagem apresenta, por produto:
  - Lucro líquido unitário.
  - Quantidade em estoque.
  - Valor do estoque pelo preço de venda.
  - Lucro líquido potencial do estoque.
- Também apresenta os totais gerais da listagem atual (respeitando os filtros):
  - Unidades em estoque.
  - Valor do estoque a preço de venda.
  - Lucro líquido potencial do estoque.
- Produtos antigos sem percentual de despesas variáveis não recebem um valor presumido: o lucro correspondente é exibido como não calculado e há um aviso. Esses produtos não entram no total de lucro potencial.

### 2.3 Serviços

- Cada serviço possui descrição, custo direto por realização, preço de venda, despesas variáveis percentuais e percentual de lucro desejado.
- A listagem permite filtrar por descrição ou preço de venda.
- A ordenação por descrição é aplicada imediatamente, em ordem A–Z ou Z–A, preservando a busca.
- Custo e preço são mostrados como moeda brasileira.
- Os valores numéricos da tabela ficam centralizados; descrição permanece à esquerda e ações à direita.
- Cada cabeçalho da tabela tem uma explicação curta ao passar o cursor.
- A listagem apresenta o lucro líquido por realização do serviço.
- Se faltar custo direto ou percentual de despesas variáveis, o lucro é exibido como não calculado. Um aviso informa quantos serviços não puderam ser calculados e orienta o usuário a completar os dados.

### 2.4 Precificação por markup

- A página **Precificar** explica o método de precificação por markup/margem de contribuição e seus três componentes:
  1. Custo variável direto (`CV`): custo para adquirir ou produzir um produto, ou custo para realizar um serviço.
  2. Despesas variáveis (`DV%`): impostos, taxas de cartão, comissões, frete por venda e despesas variáveis semelhantes.
  3. Lucro desejado (`Lucro%`): percentual desejado sobre o preço final.
- A fórmula usada para sugerir o preço é:

  `Preço sugerido = Custo direto / (1 - (DV% + Lucro%) / 100)`

- `DV% + Lucro%` deve ser menor que 100%. Se a soma for igual a 100%, o denominador zera; se superar 100%, fica negativo. Nos dois casos a fórmula não pode produzir um preço válido.
- Despesas e lucro desejado são cadastrados por item, e não como parâmetros globais.
- Produtos usam seu preço/custo direto como custo da fórmula. Serviços têm custo direto próprio por realização.
- O preço calculado é uma sugestão preenchida pelo cálculo; o usuário decide e pode editar o preço de venda final.
- Dicas explicativas devem estar disponíveis nos campos de precificação.
- Registros anteriores sem os novos dados percentuais permanecem sem valores inventados; o lucro não é calculado até que os dados necessários sejam informados.
- O lucro líquido exibido em Produtos e Serviços é:

  `Lucro líquido = Preço de venda - Custo direto - (Preço de venda × DV% / 100)`

- O lucro desejado não é subtraído como despesa: ele é uma meta usada para calcular/sugerir o preço.

## 3. Agenda

- O horário de atendimento é todos os dias, das **07:00 às 23:00**.
- O período é dividido em 32 blocos de 30 minutos:
  - Primeiro bloco: 07:00–07:30.
  - Último bloco: 22:30–23:00.
- O usuário escolhe a data em um calendário e um ou mais blocos de horário.
- Selecionar pelo menos um bloco é obrigatório. Os blocos podem ser selecionados individualmente.
- Blocos já reservados para aquela data ficam visualmente riscados e não podem ser selecionados.
- Cada combinação de data e horário de início só pode ser reservada uma vez; a validação do servidor e a restrição de banco de dados evitam duplicidade, inclusive em tentativas concorrentes.
- Serviços associados ao agendamento são opcionais e podem ser um ou mais dos serviços cadastrados.
- Nome e telefone/WhatsApp são obrigatórios. E-mail é opcional.
- A Agenda oferece CRUD: listar, criar, editar e excluir agendamentos. Excluir uma reserva libera seus blocos.
- Na listagem, telefone/WhatsApp abre uma conversa no WhatsApp.

## 4. Caixa e vendas

### 4.1 Carrinho

- O Caixa permite adicionar produtos e serviços cadastrados, um a um, em uma lista de compras.
- É possível ajustar a quantidade ou remover um item antes de finalizar.
- O preço unitário usado no carrinho é o preço de venda atualmente cadastrado para aquele produto ou serviço.
- Produtos respeitam o estoque disponível. O Caixa impede adicionar/definir quantidade acima do estoque e revalida o estoque no momento de finalizar a venda.
- Se o estoque tiver sido alterado por outra operação enquanto o item estava no carrinho, a venda não é concluída, o estoque não fica negativo e o carrinho é preservado para correção.
- A tela mantém os campos de seleção de pagamento, telefone e os controles do Caixa visíveis mesmo sem itens.
- Finalizar pagamento fica desabilitado enquanto não houver itens válidos no carrinho.

### 4.2 Pagamento

- Formas aceitas:
  - Dinheiro.
  - Cartão de crédito.
  - Cartão de débito.
  - Pix.
- Para pagamento em dinheiro, informar o valor recebido é obrigatório. O valor não pode ser inferior ao total.
- O troco é calculado e registrado como `valor recebido - total`.
- Para cartão e Pix, valor recebido e troco não se aplicam.
- O telefone do cliente não é obrigatório para concluir a venda.
- Quando informado, o telefone deve conter DDD e 10 ou 11 dígitos; o usuário pode escolher abrir o WhatsApp com o resumo da venda já preenchido. O envio é opcional e precisa ser confirmado no próprio WhatsApp.
- O resumo para WhatsApp inclui os itens e quantidades, subtotais, total e forma de pagamento; para dinheiro, inclui também valor recebido e troco.

### 4.3 Registro, estoque e manutenção de vendas

- Uma venda finalizada registra data/hora, forma de pagamento, total, telefone opcional, valor recebido/troco quando aplicáveis e seus itens.
- Cada item registra tipo (produto ou serviço), descrição, preço unitário, quantidade e subtotal. Esses dados preservam um retrato da venda, mesmo que o cadastro posteriormente seja alterado ou removido.
- Ao finalizar uma venda, o estoque dos produtos é reduzido pelas quantidades vendidas. Serviços não alteram estoque.
- O Histórico de vendas permite abrir os detalhes, editar ou excluir uma venda.
- Na edição:
  - O usuário define as quantidades finais de produtos e serviços, forma de pagamento e telefone.
  - O sistema considera as unidades consumidas pela venda original como disponíveis para a edição, valida o estoque resultante e não salva se faltar estoque.
  - O total e os itens são recalculados com os preços atuais dos cadastros.
  - O estoque é ajustado atomicamente para refletir as quantidades finais.
  - Em dinheiro, valor recebido deve cobrir o novo total e o troco é recalculado.
- Ao excluir uma venda, o sistema repõe ao estoque as quantidades de produtos daquela venda. A exclusão é confirmada e feita por POST.

## 5. Dashboards

- A página inicial é **Dashboards**, acessível pelo menu lateral.
- Gráfico de produtos mais vendidos: mostra até três descrições de produtos, classificadas pela soma das unidades registradas em vendas.
- Gráfico de serviços mais prestados: mostra até três serviços, classificados pela quantidade registrada em vendas.
- Gráfico de formas de pagamento: mostra até três formas, classificadas pelo valor total de vendas agregado por forma.
- Gráfico de status do estoque: compara a quantidade de produtos com estoque **abaixo de 5 unidades** com os demais. Se houver produtos abaixo do limite, a tela também lista os nomes e quantidades para reposição.
- Gráfico de valores do caixa: compara os totais vendidos em três períodos. O usuário escolhe:
  - Últimos 3 dias corridos, incluindo hoje.
  - Semana atual e duas semanas anteriores (semanas iniciadas na segunda-feira).
  - Mês atual e dois meses anteriores.
- Períodos sem venda são mostrados com total zero.

## 6. Relatórios

### 6.1 Relatório diário de caixa

- A tela abre por padrão com a data atual.
- O usuário pode selecionar outra data para consultar as vendas concluídas naquele dia.
- O relatório apresenta vendas e horários, itens/quantidades, formas de pagamento, total por forma e total do dia.
- Deve haver um comando de impressão. A versão impressa oculta menu, cabeçalho, rodapé e controles de navegação.

### 6.2 Relatório de estoque

- Apresenta todos os produtos cadastrados, com código, descrição, quantidade, preço de custo, preço de venda e status.
- Status:
  - **Em falta:** quantidade igual a zero.
  - **Baixo:** de 1 a 5 unidades, inclusive.
  - **Adequado:** mais de 5 unidades.
- Apresenta totais/contagens para produtos cadastrados, produtos em baixa e produtos em falta.
- Deve haver um comando de impressão; na impressão, elementos de navegação e controles são ocultados.

## 7. Observação sobre limites de estoque

Há dois limites com propósitos diferentes e ambos devem ser preservados:

- O **Dashboard** destaca estoque estritamente abaixo de 5 unidades (`0–4`), conforme solicitado para o painel.
- O **Relatório de estoque** classifica como baixo estoque de 5 unidades ou menos (`1–5`) e separa estoque zerado como “Em falta”.

## 8. Regras de consistência

- Validações importantes devem existir no servidor, mesmo quando também há validações ou interações no navegador.
- Operações que alterem vendas e estoque devem ser atômicas: uma falha não pode deixar venda parcialmente alterada ou estoque parcialmente ajustado.
- Produtos vendidos e serviços prestados usam os preços de venda cadastrados no Caixa. Na edição de uma venda, os itens são recalculados com os preços atuais, conforme descrito acima.
- Quando um dado necessário a um cálculo está ausente em registros antigos, não se deve inventar um valor: indicar que o cálculo não está disponível e explicar qual dado falta.
- A apresentação deve manter português brasileiro, valores em R$ e explicações acessíveis nos campos ou cabeçalhos quando pertinente.
