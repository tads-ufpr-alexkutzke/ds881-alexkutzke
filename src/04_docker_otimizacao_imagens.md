# Material de Aula: Otimização Avançada de Imagens Docker

## 1. Multi-stage Builds

O padrão multi-stage build resolve o problema de vazar ferramentas de compilação e dependências de desenvolvimento para o ambiente de produção. Ele permite o uso de múltiplas instruções `FROM` no mesmo `Dockerfile`. Cada `FROM` inicia uma nova etapa (stage). É possível copiar artefatos específicos de uma etapa anterior, descartando todo o resto.

**Conceitos Principais:**
* **Estágio de Build (Builder):** Contém compiladores, linters, headers C/C++ e ferramentas de gerenciamento de pacotes (ex: `npm`, `cargo`, `go env`). É uma imagem pesada.
* **Estágio de Execução (Runtime):** Contém apenas o binário final ou os artefatos estáticos necessários para rodar a aplicação. É uma imagem enxuta.

**Exemplo Prático (Go):**

```dockerfile
# Estágio 1: Builder (Imagem pesada com ferramentas de compilação ~800MB)
FROM golang:1.21 AS builder
WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download
COPY . .
# Compila o binário estaticamente
RUN CGO_ENABLED=0 GOOS=linux go build -o meu_app .

# Estágio 2: Runtime (Imagem mínima baseada em Alpine ~5MB)
FROM alpine:3.18
WORKDIR /app
# Copia APENAS o binário do estágio anterior
COPY --from=builder /app/meu_app .
EXPOSE 8080
CMD ["./meu_app"]
```


## 2. Imagens Distroless

Imagens Distroless ("sem distribuição") são ambientes de execução que contêm apenas a aplicação e suas dependências de runtime. Elas não possuem gerenciadores de pacotes (`apt`, `apk`), ferramentas de rede (`curl`, `ping`) ou sequer um shell (`/bin/sh` ou `/bin/bash`).

**Vantagens:**
* **Segurança:** A superfície de ataque é drasticamente reduzida. Sem um shell, técnicas comuns de invasão (como execução remota de código via shell reverso) tornam-se ineficazes.
* **Tamanho e Ruído:** Menos vulnerabilidades (CVEs) relatadas por scanners de segurança, pois não há bibliotecas do sistema operacional para serem auditadas.

**Comparativo de Imagens Base:**

| Base | Tamanho Médio | Contém Shell/Ferramentas? | Uso Recomendado |
| :--- | :--- | :--- | :--- |
| `ubuntu` / `debian` | ~80MB - 120MB | Sim (Completo) | Ambientes de desenvolvimento ou legado acoplado ao SO. |
| `alpine` | ~5MB | Sim (Minimalista) | Scripts complexos de inicialização ou aplicações interpretadas. |
| `gcr.io/distroless/*` | ~2MB - 20MB | Não | Aplicações em produção (Java, Node, Python compilado). |
| `scratch` | 0MB | Não | Aplicações compiladas estaticamente (Go, Rust, C++). |

**Exemplo Prático com Distroless:**

```dockerfile
FROM golang:1.21 AS builder
WORKDIR /app
COPY . .
RUN CGO_ENABLED=0 go build -o meu_app .

# Estágio final usando a imagem Distroless oficial do Google
FROM gcr.io/distroless/static-debian12
COPY --from=builder /app/meu_app /meu_app
CMD ["/meu_app"]
```

## 3. Técnicas Adicionais de Otimização

* **Otimização do Cache de Camadas:** O Docker invalida o cache de uma camada se a instrução correspondente (ou os arquivos copiados) for alterada. Instruções que mudam com pouca frequência (como instalação de dependências) devem vir antes de instruções voláteis (como cópia do código-fonte).
* **Arquivo `.dockerignore`:** Fundamental para impedir que o contexto de build envie arquivos desnecessários (como `.git`, `node_modules/` locais, logs ou arquivos temporários) para o daemon do Docker, o que aumenta o tempo de construção e pode sobrescrever dependências do contêiner.
* **Execução como Usuário Não-Root:** Por padrão, os contêineres rodam como usuário `root`. É uma prática de segurança criar e utilizar um usuário com privilégios restritos usando a instrução `USER`.

## 4. Leituras Recomendadas

1. **Documentação Oficial: Multi-stage builds**
   * Link: [https://docs.docker.com/build/building/multi-stage/](https://docs.docker.com/build/building/multi-stage/)
   * Descrição: Guia definitivo sobre a sintaxe e casos de uso avançados, como parar em estágios específicos e usar imagens externas como estágio.
2. **Boas Práticas para escrever Dockerfiles (Docker Docs)**
   * Link: [https://docs.docker.com/develop/develop-images/dockerfile_best-practices/](https://docs.docker.com/develop/develop-images/dockerfile_best-practices/)
   * Descrição: Cobre conceitos de cache, ordenação de instruções e formatação.
3. **Google Distroless GitHub Repository**
   * Link: [https://github.com/GoogleContainerTools/distroless](https://github.com/GoogleContainerTools/distroless)
   * Descrição: O repositório oficial das imagens distroless, contendo explicações sobre o conceito e como utilizar com diferentes linguagens (Java, Node, Python, Rust).
