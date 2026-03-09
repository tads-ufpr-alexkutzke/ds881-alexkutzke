# Leitura Introdutória para Docker

### 1. Origem e Fundamentos

A transição do uso de Máquinas Virtuais para Containers é o conceito central para o entendimento do Docker.

* [Docker Overview (Documentação Oficial)](https://docs.docker.com/get-started/overview/);
* [O que são Contêineres? (Red Hat)](https://www.redhat.com/pt-br/topics/containers/whats-a-linux-container);
* [Containers vs. Máquinas Virtuais (Google Cloud)](https://cloud.google.com/learn/what-are-containers).

### 2. Comandos Iniciais da CLI

A interação primária com o Docker ocorre via linha de comando (CLI). Os links abaixo detalham o uso e as principais *flags* dos comandos de operação.

* [`docker run`](https://docs.docker.com/engine/reference/commandline/run/);
* [`docker ps`](https://docs.docker.com/engine/reference/commandline/ps/);
* [`docker build`](https://docs.docker.com/engine/reference/commandline/build/);

### 3. Construção de Imagens e Dockerfile

A infraestrutura como código no ecossistema Docker é padronizada pelo arquivo `Dockerfile`.

* [Referência do Dockerfile](https://docs.docker.com/engine/reference/builder/);
* [Boas Práticas para Escrever Dockerfiles](https://docs.docker.com/develop/develop-images/dockerfile_best-practices/);
