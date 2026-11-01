# Linguagem ubíqua

Este vocabulário deve ser usado de forma consistente no código, documentação, vídeo
e conversas do time.

| Termo | Definição no domínio |
|---|---|
| Cliente | Pessoa física ou jurídica identificada por CPF/CNPJ que solicita o reparo. |
| Veículo | Bem do cliente identificado por placa e associado a uma OS. |
| Ordem de Serviço (OS) | Agregado que registra itens, orçamento, decisão do cliente e andamento do atendimento. |
| Serviço de catálogo | Trabalho oferecido pela oficina, com preço e duração estimada. |
| Peça/insumo | Item físico com SKU, preço e quantidade em estoque. |
| Diagnóstico | Etapa em que a oficina investiga o veículo e pode revisar os itens. |
| Orçamento | Soma dos snapshots de serviços e peças multiplicados pelas quantidades. |
| Snapshot | Cópia de descrição e preço feita na inclusão do item, preservando o histórico. |
| Aprovação | Decisão positiva do cliente que inicia a execução e autoriza a baixa de estoque. |
| Rejeição | Decisão negativa que mantém a OS aguardando revisão sem baixar estoque. |
| Código de acompanhamento | Identificador imprevisível usado pelo cliente para consultar a OS. |
| Movimento de estoque | Registro imutável de entrada ou saída, com motivo e possível OS de origem. |
| Tempo de execução | Intervalo entre aprovação/início da execução e finalização. |

## Status da Ordem de Serviço

| Status | Significado |
|---|---|
| RECEBIDA | OS aberta; veículo recebido pela oficina. |
| EM_DIAGNOSTICO | Equipe avaliando o veículo e compondo o orçamento. |
| AGUARDANDO_APROVACAO | Orçamento enviado e aguardando decisão do cliente. |
| EM_EXECUCAO | Orçamento aprovado e trabalho autorizado. |
| FINALIZADA | Trabalho concluído, aguardando entrega. |
| ENTREGUE | Veículo devolvido ao cliente; ciclo encerrado. |

## Invariantes

- Toda OS possui ao menos um serviço.
- Uma OS não repete o mesmo serviço ou peça.
- Valores e quantidades não podem ser negativos; quantidade de item é maior que zero.
- Uma placa pertence a apenas um cliente.
- Um orçamento só pode ser decidido quando estiver pendente.
- Aprovação só ocorre se todas as peças tiverem estoque suficiente.
- Uma OS só é finalizada após entrar em execução e só é entregue após finalizada.

