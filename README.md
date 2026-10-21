# PDF Document Reconstructor

Reconstrói PDFs recuperados em arquivos `.docx` **editáveis**, o mais próximos possível do original perdido.
Tudo roda **localmente e offline**: nenhum PDF sai do seu computador.

> **Reconstrução ≠ recuperação.** O *conteúdo* (texto, fontes, imagens, posições) é recuperado do PDF.
> A *estrutura interna* do DOCX original (estilos, campos, quebras, numeração automática) não existe mais no PDF e é
> **inferida**. O programa mede o quanto o resultado se parece com o original e diz onde falhou.

Status: **MVP (Fases 1–5 + validação da Fase 9)** — PDFs com texto real. Veja [Limitações](#limitações-conhecidas-desta-versão).

---

## Instalação (Windows)

Requisitos: **Python 3.10 ou superior** (https://www.python.org/downloads/ — marque *Add python.exe to PATH*).

```bat
cd pdf_document_reconstructor
py -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Para a **validação visual** (renderizar o DOCX de volta em PDF e comparar) é preciso um renderizador:

| Opção | Como instalar | Observação |
|---|---|---|
| **LibreOffice** (padrão) | `winget install TheDocumentFoundation.LibreOffice` ou https://www.libreoffice.org | Gratuito, offline. Pode diferir levemente do Word. |
| **Microsoft Word** | `pip install docx2pdf` (Word precisa estar instalado) | O mais fiel ao que você verá ao abrir o DOCX. Use `--renderer word`. |

Sem nenhum dos dois, o DOCX é gerado normalmente; só a comparação visual é pulada (e o relatório avisa).

## Uso

```bat
:: um arquivo
python main.py documento.pdf

:: pasta inteira (processa tudo em input\ e grava em output\)
python main.py --input .\input --output .\output

:: escolher o modo
python main.py documento.pdf --mode editable      :: prioriza edição
python main.py documento.pdf --mode visual        :: prioriza aparência
python main.py documento.pdf --mode balanced      :: padrão

:: outras opções
python main.py documento.pdf --renderer word --no-validate --keep-temp -v
```

### O que é gerado

```text
output/documento.docx                         ← o arquivo reconstruído
reports/documento/relatorio.html              ← abra no navegador (qualidade, fontes, problemas, comparação)
reports/documento/relatorio.json              ← mesmos dados, para automação
reports/documento/documento_reconstruido.pdf  ← o DOCX renderizado de volta
reports/documento/comparacao/                 ← original_page_01.png, reconstructed_page_01.png, difference_page_01.png
reports/documento/modelo.json                 ← modelo intermediário (para depurar sem reprocessar)
reports/documento/processamento.log           ← log detalhado
```

No mapa `difference_page_XX.png`: **cinza** = igual · **vermelho** = existe no original e falta na reconstrução ·
**azul** = a mais ou deslocado.

Se um PDF falhar (corrompido, protegido por senha, não-PDF), o erro é registrado e o lote **continua**.
Na tabela final, `!` marca arquivos com problemas graves: **leia o relatório antes de confiar no resultado**.

### Os três modos

| Modo | Espaçamento entre linhas | Quebras de linha | Para quê |
|---|---|---|---|
| `balanced` (padrão) | "no mínimo" X pt | o Word refaz | melhor compromisso |
| `editable` | **múltiplo** (1,0 / 1,15 / 1,5…) | o Word refaz | editar à vontade; acompanha o tamanho da fonte |
| `visual` | **exato** X pt | **travadas** nas posições originais | aparência máxima; o texto não reflui |

---

## Interface gráfica (PDF Reconstruction Studio)

```bat
pip install -r requirements.txt
python run_gui.py            :: ou dê dois cliques em iniciar_gui.bat
```

### Idiomas

A interface fala português (BR), English, Deutsch, Italiano, Español e Français e muda na hora em
*Configurações → Idioma / Language* (padrão: o idioma do Windows). Como adicionar outro idioma: veja `TRADUCOES.md`.

### Programa de verdade (.exe), sem .bat

Dê dois cliques em **`criar_executavel.bat`** (uma vez; precisa de internet e leva alguns minutos). Ele cria o ambiente, instala as
bibliotecas, empacota o programa com PyInstaller e coloca um atalho **"PDF Reconstruction Studio"** na Área de Trabalho.
O programa fica em `dist\PDF Reconstruction Studio\PDF Reconstruction Studio.exe` (uma pasta de ~400 MB; pode movê-la inteira para
onde quiser). Logs e histórico passam a ficar em `%LOCALAPPDATA%\PDFReconstructionStudio`. Para conferir uma build:
`"PDF Reconstruction Studio.exe" --selftest` (grava `selftest.log` com OK/FALHA). A conferência com o original (modo Equilibrada)
continua usando o LibreOffice ou o Word instalados no computador; sem eles o documento é gerado normalmente, só sem a conferência.

---

`iniciar_gui.bat` procura o Python (`.venv`, `venv`, `py`, `python`), confere as dependências e abre o programa com uma
janela de console, que mostra qualquer erro. **Extraia o ZIP antes de usar** (não rode de dentro dele).
Se a janela não abrir, veja `logs\startup_error.log` (erro ao iniciar) e `logs\crash.log` (falha fatal do Qt);
o programa também mostra uma caixa de mensagem com o motivo.

Arraste o PDF (ou clique em *Selecionar PDF*) → **Reconstruir PDF** → acompanhe o progresso por página → **Abrir documento**.
A interface é só a camada de apresentação: ela chama `app.pipeline.reconstruct_pdf` por meio de `gui/services/engine_adapter.py`
(o motor não foi duplicado). A linha de comando (`python main.py ...`) continua funcionando igual.

| Na interface | No motor |
|---|---|
| Qualidade **Mais rápida** | modo `balanced`, **sem** comparar o resultado com o original |
| Qualidade **Equilibrada** (padrão) | modo `balanced`, comparando com o original (precisa de LibreOffice ou Word) |
| Qualidade **Máxima fidelidade** | modo `visual` (linhas travadas; mais fiel, menos editável) |
| Progresso | página a página, de verdade; etapas sem progresso medível usam barra indeterminada |
| Cancelar | cooperativo: o motor confere entre etapas/páginas; nenhum DOCX parcial é deixado |
| PDF com senha | a GUI pede a senha; o motor recebe uma cópia desprotegida temporária (apagada ao final) |
| Páginas digitalizadas | a GUI avisa que, sem OCR (Fase 7), elas entram como **imagem** (texto não editável) |

* Relatório de qualidade (HTML) aparece como **Ver relatório de qualidade** na tela de sucesso (fica em `reports/<nome>/`).
* Logs da GUI e do motor: `logs/application.log` e `logs/reconstruction.log` (botão *Abrir logs* nas Configurações).
* Preferências: `QSettings` · Histórico: `data/history.json`.
* Para testar só a interface, sem processar de verdade: `set PDFRS_DEMO=1` antes de `python run_gui.py`.

**Mudanças feitas no motor (retrocompatíveis):** `app/utils/hooks.py` (novo: ganchos opcionais de progresso/cancelamento),
`app/pipeline.py` (parâmetro opcional `hooks`; sem ele nada muda) e `app/validation/docx_renderer.py`
(o LibreOffice é chamado com `stdin=DEVNULL` e sem janela, necessário para rodar com `pythonw`).

**Imagens recortadas:** quando o PDF mostra só um pedaço de uma foto (clip, "cortar imagem" do Word/Canva/InDesign), o DOCX usa a
área visível e o recorte nativo do Word (`a:srcRect`: a foto inteira continua no arquivo e dá para ajustar o corte). Recortes em forma de
círculo/cantos arredondados viram PNG com transparência. Imagem recortada **e** espelhada/rotacionada em ângulo livre não reproduz o recorte.

**Camadas (imagem × texto):** imagem pintada *depois* de texto que ela cobre fica na frente (como no PDF); imagem pintada *antes* do
texto, ou a menos de `image_text_safe_margin_pt` (16 pt) de qualquer texto, fica **atrás** do texto. Assim, se o Word usar outra fonte
ou quebrar uma linha diferente, nenhuma palavra fica escondida por uma imagem. Imagens isoladas continuam na frente (mais fáceis de editar).
Para selecionar uma imagem que ficou atrás do texto no Word: Página Inicial → Selecionar → Painel de Seleção.

**Colunas (2 a 3):** páginas em que nenhuma linha atravessa a calha entre as colunas viram colunas nativas do Word
(`w:cols`, com quebra de coluna e, se o PDF tiver a linha vertical entre elas, o separador). Cada coluna forma seus próprios
parágrafos, então linhas da esquerda e da direita nunca se misturam. Se um título cruza as colunas, a página usa o comportamento
anterior (tabulações). Desligue com `Config(native_columns=False)`.

**Largura do texto:** PDFs do Word costumam ter o texto ~1-3% mais estreito que a fonte nominal (ajuste `Tc`). O motor mede isso em
Times/Arial/Courier e reproduz como espaçamento entre caracteres (só condensa), para o Word quebrar as linhas onde o PDF quebrou
(`Config(match_text_width=False)` desliga).

---

## Como funciona

```text
PDF → diagnóstico → classificação → extração → parágrafos → DocumentModel → DOCX
    → renderização → comparação PDF × DOCX → relatório
```

* **Diagnóstico**: por página (texto, imagens, vetores, tabelas, colunas, fontes, camada OCR invisível) →
  `TEXT_PDF`, `SCANNED_PDF`, `HYBRID_PDF` ou `COMPLEX_LAYOUT_PDF`. **OCR nunca é usado se há texto real.**
* **Parágrafos**: o PDF só tem linhas soltas com coordenadas. O agrupamento usa espaçamento vertical, estilo, recuos,
  alinhamento e o **teste de quebra natural** (se a primeira palavra da próxima linha *caberia* no fim da anterior,
  a quebra foi deliberada, então não é continuação; assim endereços e versos não viram um bloco só).
* **Posição**: cada página do PDF vira uma *seção* do Word (tamanho e margens próprios). Um "cursor" simula onde o Word
  colocará cada linha e calcula o espaçamento anterior de cada parágrafo, de modo que as linhas de base caiam onde
  estavam (medido: **< 0,1 pt** de desvio no LibreOffice).
* **Imagens**: a imagem original é extraída (sem rasterizar a página), com transparência e rotação de 90° tratadas, e
  inserida como objeto ancorado na posição exata, na frente ou atrás do texto conforme a ordem de pintura do PDF.
* **Fontes**: nome normalizado (`ABCDEF+Arial-BoldMT` → Arial); se não estiver instalada, é substituída **e registrada**.
  Nenhuma substituição é silenciosa.

## Estrutura do projeto

```text
main.py                       ponto de entrada (CLI)
run_gui.py / iniciar_gui.bat  ponto de entrada da interface gráfica
gui/                          interface (PySide6): ui/ telas, services/ (inclui engine_adapter.py), workers/, utils/
app/
  main.py                     argumentos da linha de comando e tabela-resumo
  pipeline.py                 orquestra o fluxo; isola erros por página e por arquivo
  config.py                   TODOS os limiares e o efeito de cada modo
  analyzer/
    pdf_analyzer.py           Fase 1: analisa o documento (abre, repara, agrega páginas)
    page_analyzer.py          métricas de uma página (texto, imagens, vetores, tabelas, colunas, margens…)
    layout_analyzer.py        heurísticas: nº de colunas, cabeçalhos/rodapés recorrentes
    font_analyzer.py          resumo de fontes do documento
    document_classifier.py    classifica páginas/documento e escolhe a estratégia (A/B/C)
  extractors/
    text_extractor.py         Fase 2: spans com fonte, tamanho, cor e coordenadas; ignora texto invisível
    image_extractor.py        imagens originais (+máscara de alfa, CMYK, rotação, ordem de pintura)
  models/                     Fase 3: modelo intermediário (document / page / text / image), serializável em JSON
  reconstruction/
    paragraph_builder.py      linhas → parágrafos, alinhamento, recuos, listas, tabulações
    docx_builder.py           Fases 4/5: DOCX (seções por página, espaçamento calculado, imagens ancoradas)
  validation/
    docx_renderer.py          DOCX → PDF (LibreOffice ou Word)
    pdf_renderer.py           rasterização de páginas
    image_comparator.py       SSIM por página + similaridade do texto + mapa de diferenças
    quality_report.py         relatório HTML/JSON
  utils/                      geometria, fontes, registro de problemas (IssueLog), logging, acesso ao PDF
tests/                        44 testes; tests/samples/ tem os PDFs de exemplo (gerados por make_samples.py)
input/  output/  reports/  temp/
```

## Métrica de similaridade

* **Visual**: SSIM calculado **só nas regiões com conteúdo** (senão o branco do papel inflaria a nota).
* **Texto**: compara as palavras em ordem de leitura visual (independe da ordem em que o PDF desenhou).

É um **indicador para achar páginas problemáticas, não uma medida absoluta de fidelidade**. Um deslocamento de 1 px
já derruba o SSIM; sempre olhe as imagens de comparação.

Resultados nas amostras deste repositório (LibreOffice, modo `balanced`):

| Amostra | Visual | Texto | Observação |
|---|---|---|---|
| texto simples (justificado, lista, título) | 95% | 100% | quebras de linha idênticas |
| texto + imagem | 96% | 100% | imagem pixel a pixel igual |
| paisagem | 90% | 100% | |
| PDF "tipo Word" (título, bullets, imagem) | 87% | 99% | falta o filete sob o título (vetor); 99% porque o bullet de fonte Symbol vira "•" |
| cabeçalho/rodapé em 3 páginas | 93% | 100% | páginas preservadas 1:1 |
| duas colunas | 97% | 100% | colunas mantidas por tabulação |
| tabela | 63% | 100% | **bordas e sombreado ainda não reconstruídos** (Fase 6) |
| escaneado (sem texto) | 96% | — | página inserida como imagem de fundo: **não editável** (OCR na Fase 7) |
| página rotacionada (`/Rotate`) | 90% | 0% | inserida como imagem: **não editável** |

## Limitações conhecidas desta versão

Todas aparecem no relatório de cada documento quando ocorrem.

| Limitação | O que acontece hoje | Fase |
|---|---|---|
| **Tabelas** | texto alinhado por tabulação; **sem bordas, células ou sombreado** | 6 |
| **PDF escaneado** | página inserida como imagem de fundo; **sem texto editável** (`OCR_PENDENTE`) | 7 |
| **Vetores** (linhas, formas, fundos coloridos, sublinhado) | não reconstruídos (`VETORES_NAO_RECONSTRUIDOS`) | 6/8 |
| **Colunas** | mantidas por tabulação; não são colunas nativas do Word | 8 |
| **Cabeçalho/rodapé** | detectados, mas ficam no corpo da página; não viram cabeçalho/rodapé do Word | 8 |
| **Listas** | bullet e recuo corretos, mas é texto literal (não é lista automática do Word); numeração `1.` é texto | 8 |
| **Estilos do Word** | sem `Heading 1`, `Normal` etc.; tudo é formatação direta (a classe do parágrafo é detectada e fica no modelo) | 8 |
| **Página com `/Rotate`** | inserida como imagem | 8 |
| **Texto rotacionado** (marca d'água diagonal, texto vertical) | **não reconstruído** (`TEXTO_ROTACIONADO`) | 8 |
| **Imagens** rotacionadas em ângulo não múltiplo de 90° ou espelhadas | inseridas sem rotação (registrado) | — |
| **Formulários** (campos/caixas) | só o que a tabulação consegue; sem campos editáveis | 8 |

Outras observações honestas:

* O texto nunca é "consertado": se o PDF tem uma hifenização no fim da linha, ela permanece.
* O sistema só reproduz o que o PDF contém. Se o PDF recuperado já estava danificado, o relatório marca `PDF_REPARADO`.
* Se o número de páginas do DOCX renderizado difere do original (texto transbordou), a comparação por índice pode
  ficar desalinhada e o relatório avisa (`NUMERO_DE_PAGINAS_DIFERENTE`).

## O que foi (e o que não foi) verificado

* ✅ **Testado**: Linux, Python 3.12, PyMuPDF 1.28, LibreOffice. 44 testes automatizados passando; todos os DOCX gerados
  passam na validação do esquema OOXML.
* ⚠️ **Não testado**: execução **no Windows**, o **Microsoft Word** como renderizador (`--renderer word`), e a abertura
  dos DOCX no próprio Word. A detecção de fontes instaladas no Windows (via registro) está implementada, mas só foi
  exercitada em Linux (`fc-list`).
* ⚠️ O posicionamento vertical foi **calibrado contra o LibreOffice**. O Word pode diferir em frações de ponto na
  posição da linha de base; se você notar um desvio sistemático ao abrir no Word, o ajuste fica em `app/config.py`
  (`exact_ascent_ratio`, `descent_ratio`) e `app/utils/fonts.py` (tabelas de métricas por fonte).

## Testes

```bat
pip install -r requirements-dev.txt
python -m pytest
```

Gera os PDFs de exemplo em `tests/samples/` (o de "tipo Word" exige LibreOffice; sem ele esse caso é pulado).
Os testes de validação visual também são pulados se não houver renderizador.

## Licenças

* **PyMuPDF é AGPL-3.0.** Para uso pessoal e local não há restrição. Se você distribuir este programa (ou oferecê-lo
  como serviço), precisa cumprir a AGPL ou adquirir a licença comercial da Artifex.
* python-docx (MIT), Pillow (HPND), NumPy (BSD), scikit-image (BSD). LibreOffice (MPL 2.0) é usado como programa externo.

## Roteiro

| Fase | Conteúdo | Status |
|---|---|---|
| 1 | Analisador de PDF | ✅ |
| 2 | Extração estrutural | ✅ |
| 3 | Modelo intermediário | ✅ |
| 4 | Reconstrução básica de DOCX | ✅ |
| 5 | Imagens e fontes | ✅ |
| 6 | **Tabelas** (`add_table`, células mescladas, bordas) | próxima |
| 7 | OCR / PaddleOCR (dependência opcional) | |
| 8 | Layouts complexos (colunas, cabeçalho/rodapé nativos, listas, estilos, formulários) | |
| 9 | Renderização e comparação | ✅ (núcleo) |
| 10 | Relatórios completos | básico pronto |
| 11 | Lote | básico pronto (`--input`) |
| 12 | Interface gráfica | |
