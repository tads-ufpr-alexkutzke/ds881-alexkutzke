---
marp: true
theme: default
paginate: true
---

# Aula 01 - Introdução e Cultura DevOps
## O que é DevOps?
**Data:** 25/02

---

## O Contexto da Disciplina

- **Objetivo Geral:** Conhecer e compreender o funcionamento dos processos modernos de entrega de software seguros, rápidos e confiáveis, desde o versionamento do código até a implantação em containers.
- **Procedimento Didático:** Aulas práticas.
- **Ambiente de Desenvolvimento:** 
  - Instalação local;
  - GirusLab: Ambiente de testes local para ferramentas de DevOps
  - GitHub Codespaces: Ambiente padronizado em Linux, com VS Code e Docker embutidos.
  - Killercoda / Play with Kubernetes: Clusters efêmeros para orquestração.

---

## Avaliação Contínua e Portfólio

- **Portfólio de Lab (50%):** - Repositório individual no GitHub.
  - Documentação contínua das atividades (commits semânticos, capturas de tela, arquivos de configuração).
- **Projeto Final: Pipeline DevOps (50%):**
  - Aplicação simples + Dockerfile.
  - Workflow de CI/CD (GitHub Actions) configurado e funcional.
- **Defesa Rápida:**
  - Commit ao vivo no projeto final.
  - Validação se o pipeline executa corretamente os testes e o build.

---

## O Paradigma Tradicional de TI

Historicamente, o desenvolvimento de software seguia modelos em cascata (Waterfall) e estruturas organizacionais em silos:

1. **Silo de Negócios:** Define os requisitos.
2. **Silo de Desenvolvimento (Dev):** Escreve o código. Seu indicador de sucesso é a **velocidade** de entrega de novas features.
3. **Silo de Operações (Ops):** Mantém os servidores. Seu indicador de sucesso é a **estabilidade** e o *uptime*.
4. **Silo de Segurança (Sec):** Atua no final do processo, muitas vezes bloqueando entregas.

---

## O "Muro da Confusão"

O código é "jogado" do Desenvolvimento para as Operações:
- **Dev:** "Meu código compila e passou nos testes locais. O problema é na infraestrutura."
- **Ops:** "Esse código consome muita memória, não tem documentação de deploy e quebrou a produção. O problema é no código."

**Consequências:** Deploys noturnos, finais de semana trabalhando, alta taxa de falhas, *burnout* das equipes e atraso no retorno financeiro (Time to Market).

---

## O que (NÃO) é DevOps?

- **Não é um cargo:** Contratar um "Engenheiro DevOps" e colocá-lo em um novo silo isolado não resolve o problema.
- **Não é apenas automação:** CI/CD sem mudança cultural apenas entrega código ruim mais rápido.
- **Não é usar ferramentas específicas:** Usar Docker, Kubernetes ou Terraform não significa fazer DevOps se os silos e a falta de comunicação continuarem.

---

## O que É DevOps?

DevOps é a união de **Cultura**, **Práticas** e **Ferramentas** para aumentar a capacidade de uma organização de entregar aplicativos e serviços em alta velocidade.

- **Responsabilidade Compartilhada:** "Você construiu, você roda" (You build it, you run it - Werner Vogels, CTO da Amazon).
- **Alinhamento de Incentivos:** Devs e Ops trabalham juntos com o mesmo objetivo: entregar valor seguro e rápido ao cliente.

---

## O Projeto Fênix: A Referência Cultural

**Livro:** *O Projeto Fênix: Um romance sobre TI, DevOps e sobre ajudar o seu negócio a vencer (Gene Kim, Kevin Behr, George Spafford).*

- **Enredo:** Bill é promovido a vice-presidente de TI da Parts Unlimited em um momento de crise. O "Projeto Fênix" está atrasado, estourou o orçamento e ameaça a falência da empresa.
- **Lição:** TI não é um departamento de suporte; TI é o próprio negócio. Gargalos de TI são gargalos de negócio.

---

## Os Três Caminhos do DevOps (Caminho 1: Fluxo)

**Otimização do fluxo de trabalho da esquerda (Desenvolvimento) para a direita (Operações).**

- **Visão Sistêmica:** Otimizar o todo, não o gargalo local.
- **Tamanhos de Lote Reduzidos:** Entregar pequenas alterações com frequência (ex: múltiplos deploys por dia) em vez de um grande deploy a cada 6 meses.
- **Tornar o Trabalho Visível:** Uso de quadros Kanban.
- **Eliminar Desperdícios:** Reduzir o trabalho não concluído e o excesso de burocracia para aprovações.

---

## Os Três Caminhos do DevOps (Caminho 2: Feedback)

**Criar loops de feedback rápidos e constantes da direita para a esquerda.**

- **Amplificar o Feedback:** Identificar problemas o mais cedo possível (*Shift-Left*).
- **Qualidade na Origem:** Não empurrar defeitos para as próximas etapas. Se a build quebrar, o time para o que está fazendo para consertar.
- **Telemetria:** Monitoramento de aplicações, logs centralizados e alertas métricos para saber antes do cliente que algo falhou.

---

## Os Três Caminhos do DevOps (Caminho 3: Aprendizado Contínuo)

**Criar uma cultura que promova duas coisas: experimentação e aprendizado a partir das falhas.**

- **Segurança Psicológica:** A equipe deve se sentir segura para assumir riscos calculados.
- **Post-mortems *Blameless* (Sem Culpa):** Quando ocorre um incidente em produção, a investigação busca entender *onde o sistema permitiu a falha*, e não *quem errou*.
- **Injeção de Falhas:** Práticas como *Chaos Engineering* para testar a resiliência da arquitetura proativamente.

---

## O Framework CALMS

Acrônimo criado por Jez Humble para avaliar a maturidade DevOps:

- **C - Culture (Cultura):** Comunicação, empatia e quebra de silos.
- **A - Automation (Automação):** Tudo como código (Infraestrutura, Pipeline, Configurações).
- **L - Lean (Enxuto):** Foco no valor para o cliente e eliminação de gargalos.
- **M - Measurement (Medição):** Decisões baseadas em dados (Taxa de falha de deploy, Tempo de recuperação, ...).
- **S - Sharing (Compartilhamento):** Transparência no conhecimento e nas ferramentas entre Devs e Ops.

---

## Por que começaremos com Git?

O controle de versão (Git) é a base da Automação (Caminho 1) e do Compartilhamento (Caminho 3).

- Todo o código da aplicação, os Dockerfiles e os manifestos do Kubernetes viverão no Git.
- O GitHub não é apenas um repositório, mas a plataforma central onde o trabalho se torna visível (Issues, Pull Requests) e onde o Pipeline será executado (GitHub Actions).
- Podemos utilizar o Codespaces como ambiente *Lean*, eliminando o desperdício de tempo com setups de máquinas locais incompatíveis.
