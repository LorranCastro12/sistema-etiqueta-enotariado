# Gerador de Etiquetas E-notariado — Referência do Projeto

## Contexto

Sistema criado para gerar e imprimir etiquetas físicas de assinatura digital do e-notariado (ONR).
O problema original: o e-notariado gera um PDF com o manifesto de assinatura (pasta `modelo de referencia`),
mas ele não pode ser impresso diretamente no tamanho de etiqueta — então este sistema replica o layout
e permite preencher os dados manualmente para imprimir na etiqueta física correta.

---

## Dimensões da Etiqueta Física

| Medida              | Valor         |
|---------------------|---------------|
| Largura total       | 9,0 cm        |
| Altura total        | 5,8 cm        |
| Largura útil (texto)| 8,0 cm        |
| Altura útil (texto) | 3,5 cm        |
| Margem horizontal   | 0,5 cm (cada lado) |
| Margem vertical     | 1,15 cm (cada lado) |

A área útil de 8,0 × 3,5 cm é centralizada dentro da etiqueta de 9,0 × 5,8 cm.

---

## Layout da Etiqueta (baseado no modelo PDF)

```
┌─────────────────────────────────────────────────────────┐  ← 9,0 cm
│                                                         │
│  ┌ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┐  │  ← área útil 8,0 cm
│  │[Logo    ] │ Manifesto de assinatura      [QR Code]│  │
│  │e-notariado│ CÓDIGO DE VALIDAÇÃO                   │  │
│  │           │ HTADU-NHNAV-TQFZE-5S4SB               │  │
│  │ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ │  │
│  │MNE do documento: 067082.2026.06.26.00003504-93    │  │
│  │Documento assinado digitalmente por:               │  │
│  │✓ CPF 000.000.000-00 | NOME DA PARTE em 26/06/2026 │  │
│  │  16:15  (quebra de linha se nome for longo)       │  │
│  │Para verificar as assinaturas leia o QR code acima │  │
│  │ou acesse https://assinatura.e-notariado.org.br/   │  │
│  └ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┘  │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### Elementos Fixos (não precisam ser preenchidos)
- **Logo:** `LOGO E-NOTARIADO.png` — carregado automaticamente da pasta do programa
- **QR Code:** gerado automaticamente apontando para `https://assinatura.e-notariado.org.br/validate`
- **URL de verificação:** `https://assinatura.e-notariado.org.br/validate`
- **Texto "Manifesto de assinatura"** e demais rótulos

### Campos Preenchidos pelo Usuário
| Campo               | Exemplo                              |
|---------------------|--------------------------------------|
| Código de Validação | `HTADU-NHNAV-TQFZE-5S4SB`           |
| MNE do documento    | `067082.2026.06.26.00003504-93`      |
| CPF                 | `606.986.563-42`                     |
| Nome                | `ADEZILVA DE LIMA MENDES`            |
| Data                | `26/06/2026`                         |
| Horário             | `16:15`                              |

---

## Comportamento de Ajuste do Nome

- Se `CPF ... | NOME ... em DATA HORA` caber em uma linha → exibe em uma linha
- Se não couber → quebra em duas linhas:
  - Linha 1: `CPF 000.000.000-00 | NOME COMPLETO`
  - Linha 2: `em 26/06/2026 16:15`
- Se o nome for extremamente longo → a fonte da linha 1 encolhe progressivamente até 4,2pt

---

## Estrutura de Arquivos do Projeto

```
24 - ETIQUETA E-NOTARIADO/
├── GERADOR_ETIQUETA_E-NOTARIADO.PY       ← código-fonte principal
├── GERADOR_ETIQUETA_E-NOTARIADO.spec     ← configuração do PyInstaller
├── LOGO E-NOTARIADO.png                  ← logo fixo (deve estar junto do .exe)
├── REFERENCIA_PROJETO.md                 ← este arquivo
├── modelo de referencia/
│   └── ...EtiquetasDeAssinatura.pdf      ← PDF modelo gerado pelo e-notariado
├── build/                                ← gerado pelo PyInstaller (ignorar)
└── dist/
    └── GERADOR_ETIQUETA_E-NOTARIADO.exe  ← executável compilado
```

---

## Dependências Python

```
Pillow >= 10.0
reportlab >= 4.0
qrcode[pil] >= 7.0     ← OBRIGATÓRIO para geração automática do QR Code
pywin32 >= 305         ← necessário apenas no Windows para impressão
```

### Instalar tudo de uma vez

```bash
pip install Pillow reportlab "qrcode[pil]" pywin32
```

---

## Como Executar

```bash
cd "c:\Users\lorran.lima\Documents\1 - WORK SPACE\1 - PROGRAMACAO\24 - ETIQUETA E-NOTARIADO"
python "GERADOR_ETIQUETA_E-NOTARIADO.PY"
```

---

## Como Recompilar o Executável (.exe)

```bash
cd "c:\Users\lorran.lima\Documents\1 - WORK SPACE\1 - PROGRAMACAO\24 - ETIQUETA E-NOTARIADO"
pyinstaller "GERADOR_ETIQUETA_E-NOTARIADO.spec"
```

O `.exe` gerado ficará em `dist\GERADOR_ETIQUETA_E-NOTARIADO.exe`.

> **Importante:** ao distribuir o `.exe`, o arquivo `LOGO E-NOTARIADO.png`
> **não precisa** acompanhá-lo — ele já está embutido dentro do executável
> pelo PyInstaller (declarado em `datas` no `.spec`).

---

## Mudanças Aplicadas na Última Revisão (Claude Code — 2026-06-26)

### O que foi corrigido / reescrito

| Problema anterior                                | Solução aplicada                                      |
|--------------------------------------------------|-------------------------------------------------------|
| Campos errados (URL manual, sem MNE, sem Horário)| Campos corretos: Código, MNE, CPF, Nome, Data, Horário |
| Logo e QR Code precisavam ser selecionados       | Logo fixo (arquivo local); QR gerado automaticamente  |
| Dimensões da etiqueta erradas (5×9 cm sem margem)| Dimensões corretas: 9,0×5,8 cm, área útil 8,0×3,5 cm |
| Layout não correspondia ao modelo PDF            | Layout reescrito fiel ao modelo do e-notariado        |
| `ImageFont.truetype(..., index=1)` causava erro  | Removido; fontes bold carregadas por nome (arialbd.ttf)|
| `except: pass` silenciava erros                  | Tratamento de exceção com mensagem ao usuário         |
| Preview só atualizava com botão manual           | Preview automático com debounce de 350ms              |
| `console=True` no .spec abria terminal junto     | Alterado para `console=False`                         |
| `.spec` sem logo e sem qrcode nos hiddenimports  | `.spec` atualizado com `datas` e `hiddenimports`      |

### O que permanece igual
- Tecnologia: Python + tkinter + Pillow + ReportLab
- Saída: PDF com dimensões exatas da etiqueta (sem página A4)
- Impressão: via `win32api.ShellExecute` no Windows
- Suporte multiplataforma: Windows / Linux / macOS

---

## Tamanhos de Fonte no PDF (ReportLab)

| Elemento                          | Fonte               | Tamanho |
|-----------------------------------|---------------------|---------|
| "Manifesto de assinatura"         | Helvetica-Bold      | 8 pt    |
| "CÓDIGO DE VALIDAÇÃO"             | Helvetica-Bold      | 6,5 pt  |
| Valor do código                   | Helvetica           | 6,5 pt  |
| MNE, corpo do texto               | Helvetica           | 6,2 pt  |
| "Para verificar..." + URL         | Helvetica           | 5,5 pt  |
| Espaçamento entre linhas (body)   | —                   | 2,9 mm  |

---

## Observações para o Futuro

- O QR Code sempre aponta para `https://assinatura.e-notariado.org.br/validate`
  (URL de verificação geral do e-notariado — o usuário digita o código lá para validar).
- Se um dia a URL mudar, basta alterar a constante `VALIDATION_URL` no topo do `.PY`.
- O campo `qrcode` é opcional: se não estiver instalado, o sistema avisa e exibe um
  placeholder no preview, mas ainda gera o PDF (sem QR Code).
