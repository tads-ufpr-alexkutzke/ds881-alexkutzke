# Material de Aula: Introdução ao GitHub Actions

## Links interessantes

- [Documentação GitHub Actions](https://docs.github.com/en/actions/get-started/understand-github-actions);
- [GitHub Marketplace](https://github.com/marketplace?category=deployment&type=actions).

## 1. O que é CI/CD?

O desenvolvimento de software moderno exige velocidade e qualidade. A sigla CI/CD representa duas práticas fundamentais para alcançar esse objetivo:

* **Continuous Integration (Integração Contínua - CI):** É a prática de mesclar o código de todos os desenvolvedores em uma ramificação principal (como a `main`) várias vezes ao dia. A cada envio, scripts automatizados constroem a aplicação e executam testes unitários e de integração. O objetivo é detectar erros o mais rápido possível.
* **Continuous Deployment / Delivery (Entrega/Implantação Contínua - CD):** É a extensão natural da CI. Após o código ser testado e validado, ele é automaticamente empacotado e preparado para entrega (Delivery) ou implantado diretamente no ambiente de produção de forma automática (Deployment).

## 2. O papel do GitHub Actions

O GitHub Actions é a plataforma de automação nativa do GitHub. Ele permite que você crie fluxos de trabalho (workflows) de CI/CD e outras automações diretamente no seu repositório, sem a necessidade de ferramentas de terceiros (como Jenkins ou Travis CI).

Sempre que um evento ocorre no repositório (um novo commit, a abertura de um Pull Request, ou a criação de uma Release), o GitHub Actions pode disparar um script para responder a essa ação.

## 3. Vocabulário Essencial

Para utilizar o GitHub Actions, é necessário compreender a sua hierarquia estrutural:

* **Workflow (Fluxo de trabalho):** É o processo automatizado configurável em si. Um repositório pode ter múltiplos workflows, cada um em seu próprio arquivo.
* **Events (Eventos / Gatilhos):** É a regra que diz *quando* o workflow deve rodar. Exemplos comuns: `push` (quando há um novo commit), `pull_request` (quando um PR é aberto ou atualizado), `schedule` (rodar em um horário específico, como o cron do Linux), `workflow_dispatch` (rodar manualmente pelo botão na interface web).
* **Jobs (Trabalhos):** Um workflow é composto por um ou mais jobs. Por padrão, se houver mais de um job, eles são executados em paralelo. Cada job roda em uma máquina virtual limpa.
* **Runners (Executores):** É o servidor que executa o job. Pode ser fornecido pelo próprio GitHub (ex: `ubuntu-latest`, `windows-latest`) ou hospedado pela sua própria equipe (self-hosted).
* **Steps (Passos):** Um job contém uma sequência de passos. Um passo pode ser a execução de um comando no terminal (ex: `run: npm install`) ou a execução de uma *Action*.
* **Actions (Ações):** São aplicações autônomas, reutilizáveis e modulares que resolvem tarefas complexas. O GitHub possui um marketplace com milhares de Actions criadas pela comunidade (ex: `actions/checkout@v4` para baixar o código, ou `docker/build-push-action` para lidar com imagens).

## 4. Anatomia de um Workflow

Os workflows são definidos utilizando a linguagem de marcação **YAML** (`.yml` ou `.yaml`). O YAML depende estritamente da indentação (espaços) para definir a estrutura dos dados.

O GitHub só reconhecerá os seus workflows se eles estiverem salvos no diretório exato: `.github/workflows/` na raiz do seu repositório.

## 5. Exemplo: Hello World

Crie um novo repositório no GitHub, e adicione o arquivo `.github/workflows/hello.yml` com o seguinte conteúdo:

```yml
name: Meu Primeiro Workflow

on: [push]

jobs:
  imprimir-mensagem:
    runs-on: ubuntu-latest
    steps:
      - name: Executar comando no terminal
        run: echo "Hello World! O GitHub Actions está funcionando."
```

## 6. Exemplo Prático: Workflow de CI em Python

Abaixo, a anatomia de um arquivo YAML de integração contínua (ex: `.github/workflows/ci.yml`).

```yaml
# 1. Nome visível na aba "Actions" do repositório
name: Pipeline de CI - Python

# 2. Definição dos Gatilhos (Events)
on:
  push:
    branches:
      - main

# 3. Definição dos Trabalhos (Jobs)
jobs:
  build-and-test:
    # 4. Definição do Executor (Runner)
    runs-on: ubuntu-latest

    # 5. Sequência de Passos (Steps)
    steps:
      # O primeiro passo em 99% dos casos é baixar o código para o Runner
      - name: Baixar o código do repositório
        uses: actions/checkout@v4

      - name: Configurar ambiente Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Instalar dependências
        run: |
          python -m pip install --upgrade pip
          pip install flake8 pytest

      - name: Verificar formatação com Flake8
        run: flake8 .

      - name: Executar testes unitários
        run: pytest
```

## 7. Exemplo: mdbook

```yaml
# Sample workflow for building and deploying a mdBook site to GitHub Pages
#
# To get started with mdBook see: https://rust-lang.github.io/mdBook/index.html
#
name: mdBook deploy

on:
  # Runs on pushes targeting the default branch
  push:
    branches: ["main"]

  # Allows you to run this workflow manually from the Actions tab
  workflow_dispatch:

# Sets permissions of the GITHUB_TOKEN to allow deployment to GitHub Pages
permissions:
  contents: read
  pages: write
  id-token: write

# Allow only one concurrent deployment, skipping runs queued between the run in-progress and latest queued.
# However, do NOT cancel in-progress runs as we want to allow these production deployments to complete.
concurrency:
  group: "pages"
  cancel-in-progress: false

jobs:
  # Build job
  build:
    runs-on: ubuntu-latest
    env:
      MDBOOK_VERSION: 0.5.2
    steps:
      - uses: actions/checkout@v4
      - name: Install mdBook
        run: |
          curl --proto '=https' --tlsv1.2 https://sh.rustup.rs -sSf -y | sh
          rustup update
          cargo install --version ${MDBOOK_VERSION} mdbook
      - name: Setup Pages
        id: pages
        uses: actions/configure-pages@v5
      - name: Build with mdBook
        run: mdbook build
      - name: Upload artifact
        uses: actions/upload-pages-artifact@v3
        with:
          path: ./book

  # Deployment job
  deploy:
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    runs-on: ubuntu-latest
    needs: build
    steps:
      - name: Deploy to GitHub Pages
        id: deployment
        uses: actions/deploy-pages@v4
```
