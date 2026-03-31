# Docker Compose

## O que é o Docker Compose?

O Docker Compose é uma ferramenta para definir e executar múltiplos contêineres de forma orquestrada. Em vez de executar longos comandos, como `docker run`, no terminal um por um, o Compose permite utilizar um arquivo YAML declarativo (`docker-compose.yml`) para configurar todos os serviços, redes e volumes da aplicação.

Com um único comando, é possível criar e iniciar todos os componentes da infraestrutura, caracterizando a prática de **Infraestrutura como Código (IaC)**.

## `docker-compose` vs `docker compose`

Historicamente, o Compose era uma ferramenta separada do Docker Engine. Essa arquitetura mudou recentemente:

* **`docker-compose` (com hífen - Versão 1):** É a versão original, escrita em Python. Era instalada como um binário separado do Docker. Atualmente, a versão 1 está **descontinuada (deprecated)** e não recebe mais atualizações.
* **`docker compose` (com espaço - Versão 2):** É a versão moderna, reescrita em Go. Ela foi integrada diretamente na CLI oficial do Docker como um plugin (Docker CLI plugin). É mais rápida, suporta novos recursos corporativos e é o padrão atual da indústria.

## Estrutura Básica do `docker-compose.yml`

Um arquivo do Compose é dividido em seções principais. Abaixo estão as diretivas mais comuns utilizadas no dia a dia:

* **`services:`** A base do arquivo. Define quais contêineres (serviços) serão criados.
* **`image:`** Especifica a imagem pré-construída que será baixada do Docker Hub (ex: `postgres:15`).
* **`build:`** Indica o diretório contendo um `Dockerfile` para que o Compose construa a imagem localmente antes de rodar.
* **`ports:`** Mapeia as portas da máquina host para as portas do contêiner (Sintaxe: `"HOST:CONTAINER"`).
* **`environment:`** Define variáveis de ambiente dentro do contêiner.
* **`volumes:`** Mapeia volumes nomeados ou diretórios locais (bind mounts) para persistência de dados ou desenvolvimento.
* **`networks:`** Especifica em quais redes customizadas o contêiner deve ser conectado.
* **`depends_on:`** Define a ordem de inicialização. Garante que um serviço "A" só inicie após o serviço "B" ter sido iniciado (ex: a API só sobe depois do Banco de Dados).

## Exemplos Práticos

### Exemplo 1: Stack Clássica (WordPress + MySQL)
Este exemplo substitui a necessidade de criar redes e volumes manualmente no terminal. O Compose resolve a comunicação via DNS interno automaticamente usando os nomes dos serviços (`db` e `wordpress`).

```yaml
# docker-compose.yml
services:
  db:
    image: mysql:8.0
    environment:
      MYSQL_ROOT_PASSWORD: senha_root
      MYSQL_DATABASE: wordpress
    volumes:
      - db_data:/var/lib/mysql

  wordpress:
    image: wordpress:latest
    ports:
      - "8080:80"
    environment:
      WORDPRESS_DB_HOST: db
      WORDPRESS_DB_USER: root
      WORDPRESS_DB_PASSWORD: senha_root
      WORDPRESS_DB_NAME: wordpress
    depends_on:
      - db

# Declaração explícita dos volumes nomeados utilizados nos serviços
volumes:
  db_data:
```

### Exemplo 2: Ambiente de Desenvolvimento (API Node.js + Redis)
Este cenário é comum quando o aluno está desenvolvendo a própria aplicação e precisa que ela se conecte a um serviço de cache externo.

```yaml
# docker-compose.yml
services:
  api:
    build: . # Constrói a imagem usando o Dockerfile na mesma pasta
    ports:
      - "3000:3000"
    volumes:
      - .:/app # Bind mount para Live Reload do código fonte
      - /app/node_modules # Volume anônimo para proteger as dependências instaladas
    environment:
      - REDIS_URL=redis://cache:6379
    depends_on:
      - cache

  cache:
    image: redis:alpine # Imagem leve pré-construída
    ports:
      - "6379:6379" # Exposto apenas se precisar acessar do host para debug
```

## Principais comandos

A execução desses comandos deve ser feita no mesmo diretório onde o arquivo `docker-compose.yml` está salvo.

* **`docker compose up -d`**: Constrói as imagens (se necessário), cria as redes/volumes e sobe todos os contêineres em background (*detached*).
* **`docker compose down`**: Para e remove todos os contêineres e a rede padrão criados pelo arquivo. (Use `-v` no final se quiser apagar também os volumes nomeados).
* **`docker compose logs -f`**: Exibe e acompanha em tempo real os logs de todos os serviços unificados. Para ver apenas de um, adicione o nome (ex: `docker compose logs -f api`).
* **`docker compose ps`**: Lista o status atual dos serviços gerenciados por este arquivo.
* **`docker compose build`**: Força a reconstrução das imagens especificadas com a diretiva `build`, útil quando o `Dockerfile` ou as dependências do projeto foram alteradas.
