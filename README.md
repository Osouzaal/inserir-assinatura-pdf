# 🖊️ Inserir Assinatura em PDFs (Python)

Script em Python que aplica, em lote, a **imagem PNG da assinatura da fonoaudióloga** em PDFs de laudos, junto com **data e hora (horário de Brasília)**, gerando **cópias** e **preservando sempre os arquivos originais**.

Foi pensado para o fluxo de laudos de audiometria de uma clínica, onde muitos PDFs precisam receber a assinatura da fonoaudióloga responsável de forma padronizada e sem trabalho manual.

---

## ✨ O que ele faz

- Lê todos os PDFs de uma pasta (opcionalmente, também das subpastas).
- Insere a imagem PNG da assinatura da fonoaudióloga (de preferência com fundo transparente) na página escolhida.
- Escreve, ao lado da imagem, um carimbo discreto com **data e hora** no formato `dd/mm/aaaa HH:MMH`, sempre em horário de Brasília.
- Salva as cópias em uma **pasta de saída separada**, mantendo a mesma estrutura de subpastas.
- **Nunca sobrescreve** nada: se o arquivo de destino já existe, ele é preservado.
- Protege contra situações problemáticas (PDF com senha, PDF com assinatura digital, página inexistente, imagem fora da página).
- Imprime no terminal o resultado de cada arquivo (criado, ignorado ou com erro).

---

## ⚙️ Como funciona (passo a passo)

1. **Leitura da configuração** – o script carrega o `config.json` (por padrão, o que estiver na mesma pasta do script, ou outro indicado com `--config`).
2. **Validação** – confere se a pasta de PDFs existe e se a imagem PNG existe. Cria a pasta de saída, se necessário.
3. **Busca dos PDFs** – usa `*.pdf` (somente a pasta) ou `**/*.pdf` (com subpastas), conforme `varrer_subpastas`.
4. **Data/hora única por execução** – o horário de Brasília (`America/Sao_Paulo`) é calculado uma vez e aplicado em todos os PDFs do lote. Se o fuso não estiver disponível no sistema, usa UTC-3 como alternativa.
5. **Para cada PDF:**
   - Se o destino já existe → ignora e preserva.
   - Se o PDF é protegido por senha → ignora.
   - Se detecta **assinatura digital** (campo `/Sig` ou `/ByteRange`) → ignora, pois editar invalidaria a assinatura (a menos que `processar_pdfs_assinados` seja `true`).
   - Se a página configurada não existe → ignora.
   - Calcula a posição da imagem (veja abaixo), cria uma camada (overlay) com a imagem e outra com a data/hora usando **ReportLab**, e mescla as duas na página com **pypdf**.
   - Grava a cópia com o metadado `Subject` = "Copia com imagem da fono adicionada".
6. **Relatório** – mostra uma linha por arquivo com o status.

### 📐 Posicionamento inteligente

- As coordenadas do `config.json` são baseadas em uma página **A4 (594,96 × 841,92 pt)** e são **escaladas automaticamente** caso o PDF tenha outro tamanho.
- A altura (eixo Y) da imagem é **ancorada no nome do paciente**: o script varre o texto da página procurando um texto grande (fonte ≥ 12 pt), no lado direito (> 55% da largura) e próximo ao rodapé (entre 40 e 160 pt de altura). Ao achar, posiciona a imagem a `distancia_nome_imagem_pt` acima dele.
- Se não encontrar o nome, usa o valor fixo `y_pt` do `config.json`.
- Se a imagem ficar fora dos limites da página, o arquivo é sinalizado com erro em vez de gerar um PDF quebrado.

---

## 📦 Requisitos

- Python 3.9+
- Bibliotecas: `pypdf`, `reportlab`, `pillow`

```bash
py -m pip install pypdf reportlab pillow
```

> No Windows, se o fuso `America/Sao_Paulo` não for encontrado, instale também `tzdata` (`py -m pip install tzdata`). Sem ele, o script usa UTC-3 automaticamente.

---

## 🚀 Como usar

1. Copie o arquivo de exemplo e ajuste os caminhos:

   ```bash
   copy config.example.json config.json
   ```

2. Edite o `config.json` (veja a tabela abaixo).

3. Execute:

   ```bash
   py inserir_assinatura.py
   ```

   Ou com um arquivo de configuração em outro local:

   ```bash
   py inserir_assinatura.py --config "C:\caminho\config.json"
   ```

### Exemplo de saída

```
Data/hora aplicada (Brasilia): 28/09/2026 14:32H
criado: laudo_001.pdf
ja existe - preservado: laudo_002.pdf
ignorado - assinatura digital detectada (a edicao a invalida): laudo_003.pdf
ERRO - Imagem fora da pagina: x=74.0, y=96.0, largura=150.0, altura=900.0 pt: laudo_004.pdf
```

---

## 🔧 Configuração (`config.json`)

| Chave | Tipo | Descrição |
|---|---|---|
| `pasta_pdfs` | texto | Pasta com os PDFs originais. |
| `pasta_saida` | texto | Pasta onde as cópias assinadas serão salvas. |
| `imagem_png` | texto | Caminho da imagem PNG da assinatura da fonoaudióloga (de preferência com fundo transparente). |
| `varrer_subpastas` | true/false | Se `true`, processa também as subpastas mantendo a estrutura. |
| `largura_pt` | número | Largura da imagem em pontos (a altura é proporcional). |
| `x_pt` | número | Posição horizontal da imagem (a partir da esquerda). |
| `y_pt` | número | Posição vertical de reserva, usada se o nome do paciente não for encontrado. |
| `pagina` | número | Página onde a imagem será aplicada (começa em 1). |
| `processar_pdfs_assinados` | true/false | Se `true`, processa mesmo PDFs com assinatura digital (invalida essa assinatura). |
| `data_x_pt` | número | Posição horizontal do texto de data/hora. |
| `data_y_pt` | número | Reservado para posição do texto de data/hora (atualmente a data usa a mesma altura da imagem). |
| `data_tamanho_pt` | número | Tamanho da fonte da data/hora. |
| `distancia_nome_imagem_pt` | número | Distância vertical entre o nome do paciente e a imagem. |

> 1 ponto (pt) = 1/72 de polegada. Uma página A4 tem cerca de 595 × 842 pt.

---

## 🧯 Códigos de retorno

- `0` – execução concluída (mesmo que alguns arquivos tenham sido ignorados).
- `2` – erro de configuração (JSON inválido, chave ausente, pasta ou imagem não encontrada).

---

## 🔒 Segurança e privacidade

- Os PDFs originais **nunca são alterados**; o resultado sempre vai para outra pasta.
- **Não versione dados reais.** PDFs de laudos contêm dados sensíveis de pacientes (LGPD) e a imagem da assinatura é de uso pessoal da fonoaudióloga. Adicione-os ao `.gitignore`.
- Use a assinatura apenas com **autorização da fonoaudióloga titular**.
- A imagem inserida é uma **representação visual**, não uma assinatura digital com validade jurídica (ICP-Brasil).

---

## 🗂️ Estrutura sugerida do repositório

```
.
├── inserir_assinatura.py
├── config.example.json
├── requirements.txt
├── .gitignore
└── README.md
```

---

## 🛠️ Tecnologias

- [Python](https://www.python.org/)
- [pypdf](https://pypdf.readthedocs.io/) – leitura e mesclagem de PDFs
- [ReportLab](https://www.reportlab.com/) – criação das camadas de imagem e texto
- [Pillow](https://python-pillow.org/) – suporte a imagens

---

## 👤 Autor

**Iverson Souza Gomes**
Técnico em Radiologia • Professor de inglês • Estudante de ADS

- GitHub: [@Osouzaal](https://github.com/Osouzaal)
- LinkedIn: [Iverson Souza](https://www.linkedin.com/in/iverson-souza-b9a40b157)
