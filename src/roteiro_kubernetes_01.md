Roteiro de apresentação e comandos para a introdução ao Kubernetes.

### Fase 1: Inicialização Básica
Criação de um cluster padrão, sem mapeamento de portas ou configurações avançadas.

```bash
# Cria um cluster simples com 1 nó (Control Plane)
kind create cluster

# Verifica os nós disponíveis no cluster
kubectl get nodes

# Exibe as informações do contexto atual e onde o Control Plane está rodando
kubectl cluster-info
```

### Fase 2: Implantação Imperativa
Criação de um recurso utilizando a linha de comando para demonstrar a criação de Pods.

```bash
# Cria um Deployment solicitando 1 réplica do Nginx
kubectl create deployment nginx --image=nginx:latest

# Verifica o status de criação do Pod
kubectl get pods

# Exibe detalhes extras, como o IP interno do Pod e em qual nó ele está alocado
kubectl get pods -o wide
```

### Fase 3: Exposição de Rede e Acesso Local
Demonstração de como expor um serviço na rede do cluster e como acessá-lo externamente contornando o isolamento do Kind.

```bash
# Cria um Service do tipo NodePort vinculado à porta 80 do Nginx
kubectl expose deployment nginx --port=80 --target-port=80 --type=NodePort

# Lista os serviços para observar a porta aleatória (30000-32767) gerada pelo K8s
kubectl get svc nginx

# Cria um túnel direto entre a porta 8080 do host (máquina física) e a porta 80 do Service
kubectl port-forward svc/nginx 8080:80
```
*Instrução:* Acesse `http://localhost:8080` no navegador para provar que a aplicação está acessível. Interrompa o túnel (`Ctrl+C`) antes de prosseguir.

### Fase 4: Limpeza do Ambiente
Remoção dos recursos criados imperativamente para preparar a transição para os arquivos declarativos (YAML).

```bash
# Deleta o Deployment e o Service criados
kubectl delete deployment nginx
kubectl delete svc nginx
```
