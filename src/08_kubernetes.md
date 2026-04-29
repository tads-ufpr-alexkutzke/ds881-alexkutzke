# Kubernetes: Arquitetura e Fundamentos

- [Apresentação de slides](./08_kubernetes.pdf)
- [Exemplos](https://github.com/alexkutzke/ds881-introducao-kubernetes/tree/main)

## Ambiente
Existem várias soluções para simularmos um cluster Kubernetes. Nos exemplos de aula, utilizaremos o [Kind](https://kind.sigs.k8s.io/) (Kubernetes in Docker).


## 1. Visão Geral do Sistema
O Kubernetes é uma plataforma de código aberto voltada para a orquestração de contêineres em ambientes de produção. Suas três principais premissas são:
* **Distribuição e Agendamento:** Automatiza a alocação e a execução dos contêineres no cluster.
* **Desacoplamento:** Separa as aplicações da infraestrutura física subjacente.
* **Autocorreção:** Utiliza mecanismos contínuos para manter o estado desejado da aplicação, lidando automaticamente com falhas nas máquinas.

---

## 2. O Cluster Kubernetes

Um cluster Kubernetes é dividido em dois recursos fundamentais:

### Camada de Gerenciamento (Control Plane)
* Coordena todas as atividades do cluster.
* Aloca cargas de trabalho, gerencia atualizações e mantém o estado desejado das aplicações.

### Nós de Processamento (Worker Nodes)
* Máquinas (físicas ou virtuais) responsáveis por hospedar e executar as aplicações em contêineres.
* **Componentes internos de cada Nó:**
    * **Kubelet:** Agente que se comunica com o Control Plane para garantir que os contêineres descritos na API estejam em execução e saudáveis.
    * **Container Runtime:** O software base (ex: Docker Engine ou containerd) que baixa as imagens e executa a aplicação isolada.

---

## 3. Componentes e Abstrações

### Pods
O Kubernetes não gerencia contêineres diretamente, mas sim Pods.
* **Contexto Compartilhado:** Um Pod encapsula um ou mais contêineres que compartilham o mesmo IP, espaço de rede e intervalo de portas.
* **Armazenamento:** Contêineres no mesmo Pod têm acesso aos mesmos volumes (físicos ou lógicos).
* **Efemeridade:** Pods são mortais; se um Nó falha, o Pod é destruído e o Kubernetes recria um substituto em outro Nó.

### Deployments
* É um controlador do Control Plane focado em manter o estado desejado da aplicação (ex: manter sempre 3 réplicas).
* **Funções:** Especifica a imagem do contêiner, provê autocorreção ao substituir Pods perdidos e permite atualizações graduais (*Rolling Updates*) com zero *downtime*.

### Services
Como os IPs dos Pods são voláteis, o Service cria uma abstração lógica para garantir estabilidade.
* Atribui um IP e porta fixos a um grupo de Pods e atua como balanceador de carga entre eles.
* Roteia o tráfego exclusivamente para Pods operacionais e saudáveis.

**Tipos de Service:**
* **ClusterIP (Padrão):** IP virtual restrito ao interior do cluster (comunicação entre microsserviços).
* **NodePort:** Abre uma porta estática nos Nós (ex: 30080), permitindo acesso externo usando o IP da máquina.
* **Load Balancer:** Provisiona um balanceador de carga externo no provedor de nuvem para tráfego da internet (produção).

### Rótulos e Seletores (Labels & Selectors)
* **Rótulos (Labels):** Pares estáticos de chave/valor (ex: `app: backend`) anexados aos objetos (como Pods) para classificação.
* **Seletores (Selectors):** Mecanismo de busca usado por Services e Deployments para encontrar dinamicamente os Pods que pertencem ao seu escopo lógico.

---

## 4. Interação via CLI: kubectl
O `kubectl` é a ferramenta principal para o desenvolvedor enviar requisições à API do Control Plane. A sintaxe padrão é: `kubectl <ação> <recurso> <nome> [flags]`.

**Criação e Configuração:**
* Criar um Deployment: `kubectl create deployment meu-app --image=nginx:latest`
* Escalonar réplicas: `kubectl scale deployment/meu-app --replicas=4`
* Expor com um Service: `kubectl expose deployment nginx --type=NodePort --port=80 --target-port=80`
* Criar túnel temporário local: `kubectl port-forward services/nginx 8080:80`

**Diagnóstico e Depuração:**
* Listar Pods e IPs: `kubectl get pods -o wide`
* Ver eventos e propriedades: `kubectl describe pod <nome-do-pod>`
* Acessar logs do contêiner: `kubectl logs <nome-do-pod>`
* Acessar shell interativo no contêiner: `kubectl exec -it <nome-do-pod> -- bash`

---

## 5. Síntese: O Fluxo de Execução
1. **Instrução:** O desenvolvedor declara o estado desejado utilizando o `kubectl`.
2. **Gerenciamento:** O controlador de Deployment processa a requisição e cria as réplicas lógicas necessárias.
3. **Alocação:** O agente Kubelet nos Worker Nodes recebe a ordem e aciona o Container Runtime para baixar a imagem e subir os Pods.
