# Docker Volumes e Networks

## 1. Docker Volumes (Persistência de Dados)

Por padrão, todos os arquivos criados dentro de um contêiner são armazenados em uma camada gravável temporária. Quando o contêiner é removido, os dados são perdidos. Para persistir dados (como bancos de dados ou uploads), o Docker utiliza **Volumes**.

Existem dois tipos principais de armazenamento persistente no Docker:
1.  **Named Volumes (Volumes Nomeados):** Gerenciados inteiramente pelo Docker. São a melhor escolha para persistência de dados em produção.
2.  **Bind Mounts:** Mapeiam um diretório ou arquivo específico da máquina host para dentro do contêiner. São ideais para ambientes de desenvolvimento.

### Comandos Principais de Volumes

* `docker volume create <nome>`: Cria um novo volume nomeado.
* `docker volume ls`: Lista todos os volumes existentes.
* `docker volume inspect <nome>`: Exibe detalhes do volume, incluindo o caminho físico onde os dados estão armazenados no host (Mountpoint).
* `docker volume rm <nome>`: Remove um volume (o volume não pode estar em uso por nenhum contêiner).

### Argumentos de Execução (`-v` vs `--mount`)

Para acoplar um volume a um contêiner, utiliza-se a flag `-v` ou `--mount` no comando `docker run`.

* **Sintaxe `-v`:** `-v <origem>:<destino>`
* **Sintaxe `--mount`:** `--mount type=volume,source=<origem>,target=<destino>`

### Exemplo: Banco de Dados MySQL
O MySQL armazena seus dados em `/var/lib/mysql`. Se rodarmos um contêiner sem volume, perdemos o banco ao destruir o contêiner.

```bash
# 1. Cria o volume
docker volume create mysql_dados

# 2. Executa o MySQL montando o volume
docker run -d \
  --name meu-banco \
  --rm \
  -p 3306:3306 \
  -e MYSQL_ROOT_PASSWORD=senha_secreta \
  -v mysql_dados:/var/lib/mysql \
  mysql:8.0
```

---

## 2. Docker Networks (Comunicação entre Contêineres)

As redes (Networks) permitem que contêineres isolados conversem entre si de forma segura. O Docker possui um servidor DNS embutido que permite a resolução de nomes de contêineres em redes definidas pelo usuário (User-defined bridges).



### Tipos de Rede (Drivers)
* **Bridge (Padrão):** Usada quando os contêineres precisam se comunicar em um mesmo host. A rede `bridge` padrão não possui resolução de DNS por nome do contêiner, por isso cria-se redes *user-defined*.
* **Host:** O contêiner compartilha o stack de rede da máquina host (não há isolamento de IP).
* **None:** Desabilita completamente a interface de rede do contêiner.

### Comandos Principais de Networks

* `docker network create <nome>`: Cria uma nova rede do tipo bridge.
* `docker network ls`: Lista as redes disponíveis.
* `docker network inspect <nome>`: Mostra detalhes da rede e quais contêineres estão conectados a ela.
* `docker network connect <rede> <container>`: Conecta um contêiner em execução a uma rede.

### Exemplo Prático Clássico: WordPress + MySQL
Este exemplo integra Volumes e Networks. O WordPress precisa conversar com o MySQL. Eles devem estar na mesma rede para que o WordPress acesse o banco usando apenas o nome do contêiner (`db-site`).

```bash
# 1. Cria a rede
docker network create rede_wordpress

# 2. Sobe o banco de dados conectado à rede e com volume
docker run -d \
  --name db-site \
  --network rede_wordpress \
  -e MYSQL_ROOT_PASSWORD=senha_root \
  -e MYSQL_DATABASE=wordpress \
  --mount type=volume,source=wp_db_data,target=/var/lib/mysql \
  mysql:8.0

# 3. Sobe o WordPress na mesma rede, apontando para o host 'db-site'
docker run -d \
  --name meu-wordpress \
  --network rede_wordpress \
  -p 8080:80 \
  -e WORDPRESS_DB_HOST=db-site \
  -e WORDPRESS_DB_USER=root \
  -e WORDPRESS_DB_PASSWORD=senha_root \
  -e WORDPRESS_DB_NAME=wordpress \
  wordpress:latest
```
Acessando `localhost:8080`, a instalação do WordPress estará pronta e conectada ao banco.

---

## 3. Desenvolvimento com Volumes Compartilhados (Bind Mounts)

No ambiente de desenvolvimento, queremos escrever o código na nossa IDE (no host) e ver a mudança refletida imediatamente dentro do contêiner, sem precisar realizar o `docker build` a cada salvamento. Isso é feito com um **Bind Mount**.

### Exemplo: Ambiente Node.js (Express)

**Arquivo: `Dockerfile.dev`**
```dockerfile
FROM node:24-alpine

WORKDIR /app

# Copia e instala apenas dependências primeiro (otimização de cache)
COPY package.json package-lock.json ./
RUN npm install

# O código fonte (COPY . .) é intencionalmente omitido ou substituído pelo bind mount em tempo de execução
# O comando padrão deve rodar com uma ferramenta de live-reload (como nodemon ou node --watch)
CMD ["npm", "run", "start:dev"]
```

**Comando de Execução no Host:**
Para rodar este ambiente, o diretório atual da máquina host (`$(pwd)` no Linux/Mac ou `%cd%` no Windows) é mapeado para `/app` no contêiner.

```bash
docker run -d \
  --name api-dev \
  -p 3000:3000 \
  --mount type=bind,source="$(pwd)",target=/app \
  minha-imagem-node
```

*Observação técnica:* Como o diretório local sobrescreve a pasta `/app` do contêiner, a pasta `node_modules` gerada no build pode ser ofuscada. Em projetos Node, utiliza-se frequentemente um volume anônimo adicional (`-v /app/node_modules`) para proteger as dependências instaladas.

---

## 4. Leituras Recomendadas (Documentação Oficial)

* **Docker Volumes:** [https://docs.docker.com/storage/volumes/](https://docs.docker.com/storage/volumes/)
* **Docker Bind Mounts:** [https://docs.docker.com/storage/bind-mounts/](https://docs.docker.com/storage/bind-mounts/)
* **Docker Network Drivers:** [https://docs.docker.com/network/](https://docs.docker.com/network/)
* **Networking Tutorial:** [https://docs.docker.com/network/network-tutorial-standalone/](https://docs.docker.com/network/network-tutorial-standalone/)
