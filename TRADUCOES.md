# Traduções / Translations

A interface está em **português (Brasil)** (idioma-fonte) e traduzida para **English, Deutsch, Italiano, Español e Français**.
O idioma é escolhido em *Configurações → Idioma / Language* (padrão: o idioma do Windows; se não houver tradução, inglês)
e muda na hora, sem reiniciar.

## Adicionar um idioma novo (ex.: japonês)
1. `python tools/i18n_check.py --init ja "日本語"` cria `gui/i18n/ja.json` com todos os textos para traduzir.
2. Preencha os valores (a chave é o texto em português; **mantenha** `{0}`, `{1}`, `{n}` e as quebras de linha `\n`).
   Formas de plural: `{n} página` (singular) e `{n} páginas` (plural) — traduza as duas.
3. `python tools/i18n_check.py` lista o que ainda falta. Textos vazios/ausentes caem de volta para o português.
4. Pronto: o idioma aparece sozinho na lista de Configurações. Se precisar de regra de plural diferente, ajuste `_is_singular()` em `gui/utils/i18n.py`.
5. Para gerar o `.exe` com o idioma, nada a fazer: `gui/i18n/*.json` já é empacotado.

## Ao mudar a interface
Todo texto visível deve passar por `tr("texto em português")` (ou `trn(n, "{n} item", "{n} itens")` para plurais, ou `tr_noop(...)`
quando o texto só é traduzido na hora de exibir). Depois rode `python tools/i18n_check.py` — os testes (`pytest`) também
falham se algum idioma estiver incompleto.

## O que ainda NÃO é traduzido
O **relatório de qualidade (HTML)**, os registros técnicos (logs) e as mensagens da linha de comando (`python main.py`) continuam em
português. Os textos mostrados na interface (inclusive as etapas do processamento e os avisos do resultado) são traduzidos.

> As traduções foram escritas por IA e merecem revisão por falantes nativos antes de uma distribuição pública.
