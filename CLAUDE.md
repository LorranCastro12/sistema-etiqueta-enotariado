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
- `make_qr_pil()` / `make_qr_buffer()` — geram o QR Code respectivamente para o preview (PIL) e para o PDF (ReportLab via buffer de bytes)
- `get_printers()` / `print_file()` — multiplataforma: `win32print`/`win32api` no Windows, `lp` no Linux/macOS
- `text_width_pil()` — wrapper de largura de texto compatível com versões antigas do Pillow

**2. `EtiquetaApp` — classe principal (tkinter)**
- `_build_ui()` — monta o formulário (3 linhas × 2 campos), canvas de preview e seção de impressão
- `_schedule_preview()` — debounce de 350ms: qualquer alteração nos campos agenda `update_preview`
- `update_preview()` — renderiza a etiqueta em tempo real usando **Pillow** num `tk.Canvas`
- `generate_pdf()` — gera o PDF final usando **ReportLab** com dimensões exatas da etiqueta física

**3. Constantes de dimensão (topo do arquivo)**
```python
LABEL_W = 9.0 * cm   # etiqueta total
LABEL_H = 5.8 * cm
TEXT_W  = 8.0 * cm   # área útil centralizada
TEXT_H  = 3.5 * cm
MARGIN_X = (LABEL_W - TEXT_W) / 2   # 0,5 cm
MARGIN_Y = (LABEL_H - TEXT_H) / 2   # 1,15 cm
VALIDATION_URL = "https://assinatura.e-notariado.org.br/validate"
```

## Dualidade Preview × PDF

O preview (`update_preview`) usa **Pillow + Arial** (fontes do sistema) e o PDF (`generate_pdf`) usa **ReportLab + Helvetica**. Ambos devem implementar o mesmo comportamento de layout — qualquer mudança visual precisa ser replicada nas duas funções.

Comportamento crítico de ajuste de nome: se `CPF | NOME em DATA HORA` não couber em uma linha, quebra em duas; se a linha 1 (`CPF | NOME`) ainda for longa demais, a fonte encolhe progressivamente de 6,2pt até 4,2pt em passos de 0,15pt.

## PyInstaller (.spec)

O `LOGO E-NOTARIADO.png` é embutido no .exe via `datas` no `.spec` — **não precisa** ser distribuído junto com o executável. O `qrcode` é declarado em `hiddenimports` porque o PyInstaller não o detecta automaticamente. `console=False` é obrigatório para evitar janela de terminal.

## Tamanhos de fonte no PDF

| Elemento | Fonte | Tamanho |
|---|---|---|
| "Manifesto de assinatura" | Helvetica-Bold | 8 pt |
| "CÓDIGO DE VALIDAÇÃO" | Helvetica-Bold | 6,5 pt |
| Valor do código | Helvetica | 7,5 pt |
| MNE e corpo | Helvetica | 7,0 pt |
| "Para verificar..." + URL | Helvetica | 6,5 pt |
| Espaçamento entre linhas | — | 3,1 mm |

O check mark (✓) é desenhado manualmente com dois segmentos de linha — não use caracteres Unicode pois ReportLab com Helvetica não os suporsa.

## Impressão no Windows

`print_file()` usa três tentativas em cascata:

1. `ShellExecute("printto", abs_path, printer_name)` — passa a impressora diretamente; não usar aspas extras em `printer_name`
2. `win32print.SetDefaultPrinter` + `ShellExecute("print")` — fallback para leitores que não suportam "printto"
3. `os.startfile(abs_path)` + dialog de instrução manual — fallback final

**Por que a cascata existe:** no Windows 11 com Microsoft Edge como leitor PDF padrão, o verbo `"print"` do ShellExecute retorna erro 31 (`ERROR_GEN_FAILURE`). Isso não é bug do código nem do .exe — é limitação do Edge. Criar o executável `.exe` não resolve; o comportamento é idêntico rodando pelo Python.
