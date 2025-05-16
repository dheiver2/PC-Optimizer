# PC Optimizer

Um script Python avançado para otimização e manutenção do Windows, com análise inteligente do sistema e recursos automatizados de limpeza, integrado com múltiplos agentes de IA especializados para otimização inteligente.

## 🚀 Funcionalidades

- **Análise Inteligente do Sistema**
  - Monitoramento de CPU, memória e disco
  - Análise de processos e serviços
  - Detecção de problemas de performance
  - Recomendações personalizadas
  - Análise preditiva de problemas usando IA
  - Classificação inteligente de processos críticos
  - Detecção de anomalias usando IsolationForest
  - Análise semântica com BERT
  - Previsões de tendências do sistema

- **Otimizações Automáticas**
  - Limpeza de arquivos temporários
  - Otimização de memória virtual
  - Desfragmentação de disco
  - Limpeza de cache do sistema
  - Otimização de serviços do Windows
  - Gerenciamento de programas de inicialização
  - Otimização baseada em padrões de uso
  - Ajuste automático de configurações do sistema
  - Limpeza inteligente de arquivos em uso
  - Otimização de rede e DNS

- **Gerenciamento de Software**
  - Identificação de programas não utilizados
  - Desinstalação automática de softwares antigos
  - Análise de uso de programas
  - Recomendações inteligentes de software
  - Detecção de software malicioso
  - Análise de compatibilidade
  - Análise de data de instalação e último uso
  - Proteção de software crítico do sistema

- **Recursos de Segurança**
  - Verificação de privilégios de administrador
  - Backup automático antes de alterações críticas
  - Logs detalhados de operações
  - Detecção de vulnerabilidades
  - Análise de segurança do sistema
  - Verificação de antivírus
  - Monitoramento de firewall
  - Análise de serviços críticos

- **Agentes de IA Especializados**
  - PerformanceAgent: Análise de performance
  - SecurityAgent: Verificação de segurança
  - OptimizationAgent: Recomendações de otimização
  - AnalysisAgent: Análise geral do sistema
  - PredictionAgent: Previsões de tendências
  - Suporte a GPU para aceleração
  - Análise adaptativa baseada em histórico
  - Detecção de padrões de uso

## 📋 Pré-requisitos

- Windows 10 ou superior
- Python 3.8 ou superior
- Privilégios de administrador
- GPU NVIDIA (opcional, para melhor performance da IA)
- 8GB RAM mínimo (16GB recomendado para IA)
- Espaço em disco: 2GB mínimo para modelos de IA

## 📦 Instalação

1. Clone o repositório:
```bash
git clone https://github.com/seu-usuario/pc-optimizer.git
cd pc-optimizer
```

2. Instale as dependências:
```bash
pip install -r requirements.txt
```

3. (Opcional) Configure a GPU para aceleração da IA:
```bash
pip install torch --index-url https://download.pytorch.org/whl/cu118
```

## 🛠️ Dependências

```
psutil>=5.9.0
wmi>=1.5.1
GPUtil>=1.4.0
pywin32>=305
humanize>=4.6.0
colorama>=0.4.6
tqdm>=4.65.0
transformers>=4.30.0
torch>=2.0.0
numpy>=1.24.0
requests>=2.31.0
scikit-learn>=1.0.0
sentence-transformers>=2.2.0
pandas>=1.5.0
```

## 💻 Uso

Execute o script com privilégios de administrador:

```bash
python pc_optimizer.py
```

O script irá:
1. Inicializar os agentes de IA especializados
2. Analisar o sistema em múltiplas camadas
3. Executar otimizações inteligentes
4. Gerar um relatório detalhado
5. Reiniciar automaticamente o Windows para aplicar as alterações

## 🤖 Recursos de IA

### Agentes Especializados
- **PerformanceAgent**: Análise de performance do sistema
- **SecurityAgent**: Verificação de segurança e vulnerabilidades
- **OptimizationAgent**: Geração de recomendações de otimização
- **AnalysisAgent**: Análise geral do sistema
- **PredictionAgent**: Previsões de tendências

### Análise Inteligente
- Detecção de anomalias usando IsolationForest
- Análise semântica com BERT
- Previsões de tendências
- Recomendações personalizadas
- Análise de segurança proativa

### Otimizações Inteligentes
- Ajuste automático de configurações
- Otimização baseada em padrões de uso
- Detecção de problemas recorrentes
- Previsão de problemas futuros
- Análise de histórico de uso

## ⚠️ Avisos Importantes

- Faça backup dos seus dados importantes antes de executar o script
- O script requer privilégios de administrador
- Algumas otimizações podem levar tempo para serem concluídas
- O sistema será reiniciado automaticamente após a otimização
- O uso da GPU é opcional, mas recomendado para melhor performance
- Mantenha pelo menos 20% de espaço livre no disco C:

## 📊 Relatório de Otimização

O script gera um relatório detalhado incluindo:
- Estado do sistema antes e depois das otimizações
- Métricas de performance
- Problemas identificados
- Recomendações personalizadas
- Informações sobre hardware e software
- Análise de IA do estado do sistema
- Previsões de performance
- Análise de segurança
- Recomendações de software
- Tendências do sistema

## 🔧 Personalização

O script pode ser personalizado editando as seguintes seções:
- `_optimize_services()`: Lista de serviços para otimização
- `_is_critical_software()`: Critérios para software crítico
- `_get_disk_recommendations()`: Limites e recomendações de disco
- `AIAgents`: Configurações dos agentes de IA
- `SystemAnalyzer`: Parâmetros de análise do sistema
- `PerformanceAgent`: Configurações de análise de performance
- `SecurityAgent`: Configurações de segurança
- `OptimizationAgent`: Configurações de otimização

## 📝 Logs

Os logs são salvos em `optimization.log` e incluem:
- Detalhes de todas as operações
- Erros e avisos
- Métricas de performance
- Resultados das otimizações
- Análises dos agentes de IA
- Recomendações geradas
- Histórico de otimizações
- Detecção de anomalias

## 🤝 Contribuindo

Contribuições são bem-vindas! Por favor, leia as diretrizes de contribuição antes de enviar um pull request.

## 📄 Licença

Este projeto está licenciado sob a licença MIT - veja o arquivo [LICENSE](LICENSE) para detalhes.

## ⚠️ Disclaimer

Este script é fornecido "como está", sem garantias de qualquer tipo. Use por sua conta e risco. Sempre faça backup dos seus dados importantes antes de executar qualquer otimização do sistema. 
