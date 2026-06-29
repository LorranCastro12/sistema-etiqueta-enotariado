# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## O que é este projeto

Gerador de etiquetas físicas de assinatura digital para o sistema e-notariado (ONR). O e-notariado gera um PDF de manifesto de assinatura que não pode ser impresso diretamente no tamanho da etiqueta física — este sistema replica o layout e permite imprimir na etiqueta correta (9,0 × 5,8 cm).

## Executar e recompilar

```bash
# Rodar direto pelo Python
python "GERADOR_ETIQUETA_E-NOTARIADO.PY"

# Recompilar o .exe (gera em dist\GERADOR_ETIQUETA_E-NOTARIADO.exe)
pyinstaller "GERADOR_ETIQUETA_E-NOTARIADO.spec"

# Instalar dependências
pip install Pillow reportlab "qrcode[pil]" pywin32
```

## Arquitetura

O projeto é um único arquivo Python (`GERADOR_ETIQUETA_E-NOTARIADO.PY`) com três camadas:

**1. Utilitários (funções de módulo)**
- `resource_path()` — resolve caminhos de arquivos tanto em modo fonte quanto em .exe (PyInstaller usa `sys._MEIPASS`)
- `make_qr_pil(size_px, url)` / `make_qr_buffer(url)` — geram o QR Code respectivamente para o preview (PIL) e para o PDF (ReportLab via buffer de bytes); recebem a URL completa como parâmetro (incluindo o código de validação)
- `get_printers()` / `print_file()` — multiplataforma: `win32print`/`win32api` no Windows, `lp` no Linux/macOS
- `text_width_pil()` — wrapper de largura de texto compatível com versões antigas do Pillow

**2. `EtiquetaApp` — classe principal (tkinter)**
- `_apply_style()` — configura `ttk.Style` com tema `"clam"` e paleta de cores institucional; chamado em `__init__` antes de `_build_ui()`
- `_build_ui()` — monta header azul, cards brancos (Dados / Preview / Impressão) e botões de ação
- `_clear_fields()` — limpa Código, MNE, CPF e Nome; redefine Data/Hora para o momento atual
- `_schedule_preview()` — debounce de 350ms: qualquer alteração nos campos agenda `update_preview`
- `update_preview()` — renderiza a etiqueta em tempo real usando **Pillow** num `tk.Canvas`
- `generate_pdf()` — gera o PDF final usando **ReportLab** com dimensões exatas da etiqueta física

**3. Constantes de dimensão e UI (topo do arquivo)**
```python
LABEL_W = 9.0 * cm   # etiqueta total
LABEL_H = 5.8 * cm
TEXT_W  = 8.0 * cm   # área útil centralizada
TEXT_H  = 3.5 * cm
MARGIN_X = (LABEL_W - TEXT_W) / 2   # 0,5 cm
MARGIN_Y = (LABEL_H - TEXT_H) / 2   # 1,15 cm
VALIDATION_URL = "https://assinatura.e-notariado.org.br/validate"

# UI Design Tokens (após as constantes de dimensão)
CLR_BG, CLR_SURFACE, CLR_BORDER   # fundo, superfície de card, borda
CLR_PRIMARY, CLR_PRIMARY_HOV      # azul institucional #1B4F9E e hover
CLR_SECONDARY, CLR_LABEL          # fundo do botão secundário e cor de label
CLR_WARN, CLR_ERROR               # laranja e vermelho para avisos
FONT_FAMILY = "Segoe UI"
FONT_NORMAL, FONT_BOLD, FONT_SMALL
```

`VALIDATION_URL` é a base da URL — usada tanto no texto impresso no rodapé quanto para montar a URL do QR code. O QR code codifica `f"{VALIDATION_URL}/{codigo}"`, abrindo direto no resultado validado sem necessidade de inserção manual.

## Dualidade Preview × PDF

O preview (`update_preview`) usa **Pillow + Arial** (fontes do sistema) e o PDF (`generate_pdf`) usa **ReportLab + Helvetica**. Ambos devem implementar o mesmo comportamento de layout — qualquer mudança visual precisa ser replicada nas duas funções.

Comportamento crítico de ajuste de nome: se `CPF | NOME em DATA HORA` não couber em uma linha, quebra em duas; se a linha 1 (`CPF | NOME`) ainda for longa demais, a fonte encolhe progressivamente de 6,2pt até 4,2pt em passos de 0,15pt.

## QR Code

- **Tamanho:** 1,5 cm (PDF: `QR_SZ = 1.5 * cm`; preview: `QR_SZ = round(1.5 * CPX)`)
- **URL:** dinâmica — `f"{VALIDATION_URL}/{codigo}"` — abre direto no resultado validado; no preview, quando o campo código está vazio usa `VALIDATION_URL` como fallback
- **Linha divisória:** posicionada em `max(LOGO_SZ, QR_SZ)` abaixo do topo, pois o QR (1,5 cm) é maior que o logo (1,15 cm)
- `avail_w` / `avail_px` (espaço horizontal para o texto do assinante) já subtraem `QR_SZ` dinamicamente — ajustam automaticamente se o tamanho mudar

## Interface gráfica (UI)

- **Tema:** `ttk.Style` com `"clam"` (único tema built-in no Windows com controle total de cores via `bordercolor`, `fieldbackground`, etc.)
- **Layout:** header fixo azul (#1B4F9E, 56 px) + cards brancos (`tk.Frame` com `highlightbackground`/`highlightthickness=1`) para cada seção
- **Tamanho inicial da janela:** 760×860 px; mínimo 660×760 px — garante visibilidade de todos os elementos ao abrir
- **Botões:** `Primary.TButton` (Imprimir, azul sólido) e `Secondary.TButton` (Salvar PDF / Limpar, azul claro). Ordem na barra: `[Salvar PDF]` à esquerda, `[Imprimir Etiqueta] [Limpar]` à direita
- **Importante:** labels dentro dos cards usam `tk.Label` (não `ttk.Label`) para que `bg=CLR_SURFACE` seja aplicado diretamente sem precisar de estilo ttk separado por contexto
- **Ícone da janela:** `root.iconbitmap(resource_path("ICONE.ico"))` em `main()`, envolto em `try/except` para não quebrar em ambientes sem o arquivo. O `.ico` contém 7 tamanhos embutidos (16 → 256 px, 32-bit RGBA)

## PyInstaller (.spec)

O `LOGO E-NOTARIADO.png` e o `ICONE.ico` são embutidos no .exe via `datas` no `.spec` — **não precisam** ser distribuídos junto com o executável. O ícone também é declarado em `icon='ICONE.ico'` no bloco `EXE(...)`, o que faz o Windows exibir o ícone correto no `.exe` e na barra de tarefas. O `qrcode` é declarado em `hiddenimports` porque o PyInstaller não o detecta automaticamente. `console=False` é obrigatório para evitar janela de terminal.

## Tamanhos de fonte no PDF

| Elemento | Fonte | Tamanho |
|---|---|---|
| "Manifesto de assinatura" | Helvetica-Bold | 8 pt |
| "CÓDIGO DE VALIDAÇÃO" | Helvetica-Bold | 6,5 pt |
| Valor do código | Helvetica | 9,5 pt |
| MNE e corpo | Helvetica | 9,0 pt |
| "Para verificar..." + URL | Helvetica | 6,5 pt |
| Espaçamento entre linhas | — | 3,1 mm |

O check mark (✓) é desenhado manualmente com dois segmentos de linha — não use caracteres Unicode pois ReportLab com Helvetica não os suporta.

## Impressão no Windows

`print_file()` usa três tentativas em cascata:

1. `ShellExecute("printto", abs_path, printer_name)` — passa a impressora diretamente; não usar aspas extras em `printer_name`
2. `win32print.SetDefaultPrinter` + `ShellExecute("print")` — fallback para leitores que não suportam "printto"
3. `os.startfile(abs_path)` + dialog de instrução manual — fallback final

**Por que a cascata existe:** no Windows 11 com Microsoft Edge como leitor PDF padrão, o verbo `"print"` do ShellExecute retorna erro 31 (`ERROR_GEN_FAILURE`). Isso não é bug do código nem do .exe — é limitação do Edge. Criar o executável `.exe` não resolve; o comportamento é idêntico rodando pelo Python.
