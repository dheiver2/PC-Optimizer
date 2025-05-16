import os
import subprocess
import ctypes
import winreg
import shutil
import tempfile
from datetime import datetime, timedelta
import psutil
import win32com.client
import humanize
import sys
import json
import wmi
import GPUtil
import platform
from typing import Dict, List, Tuple, Optional
import logging
from concurrent.futures import ThreadPoolExecutor
import time
from tqdm import tqdm
import colorama
from colorama import Fore, Style
import requests
import threading
from queue import Queue
import re
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification, AutoModelForCausalLM
import torch
import numpy as np
from sklearn.ensemble import IsolationForest
from sentence_transformers import SentenceTransformer
import pandas as pd
from collections import defaultdict

# Inicializa colorama para cores no Windows
colorama.init()

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('optimization.log'),
        logging.StreamHandler()
    ]
)

class LLMAgent:
    """Classe para gerenciar o modelo de análise."""
    
    def __init__(self):
        self.model = None
        self.tokenizer = None
        self.classifier = None
        self.available = False
        
    def start_llm(self):
        """Inicia o modelo de análise."""
        print(f"{Fore.YELLOW}Iniciando modelo de análise...{Style.RESET_ALL}")
        try:
            print(f"{Fore.CYAN}Carregando modelo BERT (isso pode levar alguns segundos na primeira execução)...{Style.RESET_ALL}")
            
            # Carrega o modelo e tokenizer
            model_name = "bert-base-uncased"
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModelForSequenceClassification.from_pretrained(
                model_name,
                num_labels=3,
                problem_type="multi_label_classification"
            )
            
            # Configura o modelo para avaliação
            self.model.eval()
            
            # Cria o pipeline de análise
            self.classifier = pipeline(
                "text-classification",
                model=self.model,
                tokenizer=self.tokenizer,
                device=0 if torch.cuda.is_available() else -1,
                top_k=3
            )
            
            self.available = True
            print(f"{Fore.GREEN}Modelo iniciado com sucesso!{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.YELLOW}Erro ao iniciar modelo: {str(e)}{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}Usando modo padrão de otimização.{Style.RESET_ALL}")
            self.available = False
    
    def analyze_system_state(self, system_info: Dict) -> Dict:
        """Analisa o estado do sistema usando o modelo."""
        if not self.available:
            return self._get_default_analysis(system_info)
            
        try:
            # Prepara o texto para análise
            text = f"""
            Sistema: {system_info.get('os')}
            CPU: {system_info.get('cpu_usage')}%
            Memória: {system_info.get('memory_usage')}%
            Disco: {system_info.get('disk_usage')}%
            Processos: {system_info.get('running_processes')}
            """
            
            # Analisa o texto
            results = self.classifier(text)
            
            # Mapeia os resultados para nosso formato
            estado = "bom"
            confianca = 0.0
            problemas = []
            recomendacoes = []
            prioridade = 3
            
            # Analisa cada resultado
            for result in results:
                label = result['label']
                score = result['score']
                
                if label == 'LABEL_0':  # Bom
                    if score > confianca:
                        estado = "bom"
                        confianca = score
                elif label == 'LABEL_1':  # Crítico
                    if score > confianca:
                        estado = "crítico"
                        confianca = score
                elif label == 'LABEL_2':  # Atenção
                    if score > confianca:
                        estado = "atenção"
                        confianca = score
            
            # Adiciona problemas e recomendações baseados nas métricas
            if system_info.get('cpu_usage', 0) > 80:
                problemas.append("Uso de CPU muito alto")
                recomendacoes.append("Feche programas não utilizados")
                prioridade = max(prioridade, 4)
                
            if system_info.get('memory_usage', 0) > 90:
                problemas.append("Uso de memória muito alto")
                recomendacoes.append("Considere aumentar a memória RAM")
                prioridade = max(prioridade, 4)
                
            if system_info.get('disk_usage', 0) > 95:
                problemas.append("Espaço em disco muito baixo")
                recomendacoes.append("Libere espaço no disco C:")
                prioridade = 5
            
            return {
                "estado": estado,
                "confianca": confianca,
                "problemas": problemas,
                "recomendacoes": recomendacoes,
                "prioridade": prioridade
            }
            
        except Exception as e:
            logging.error(f"Erro na análise do sistema: {str(e)}")
            return self._get_default_analysis(system_info)
    
    def _get_default_analysis(self, system_info: Dict) -> Dict:
        """Fornece análise padrão quando o modelo não está disponível."""
        estado = "bom"
        problemas = []
        recomendacoes = []
        prioridade = 3
        
        # Análise de CPU
        if system_info.get('cpu_usage', 0) > 80:
            estado = "crítico"
            problemas.append("Uso de CPU muito alto")
            recomendacoes.append("Feche programas não utilizados")
            prioridade = max(prioridade, 4)
            
        # Análise de Memória
        if system_info.get('memory_usage', 0) > 90:
            estado = "crítico"
            problemas.append("Uso de memória muito alto")
            recomendacoes.append("Considere aumentar a memória RAM")
            prioridade = max(prioridade, 4)
            
        # Análise de Disco
        if system_info.get('disk_usage', 0) > 95:
            estado = "crítico"
            problemas.append("Espaço em disco muito baixo")
            recomendacoes.append("Libere espaço no disco C:")
            prioridade = 5
            
        return {
            "estado": estado,
            "confianca": 1.0,
            "problemas": problemas,
            "recomendacoes": recomendacoes,
            "prioridade": prioridade
        }
    
    def optimize_task(self, task_name: str, task_data: Dict) -> Dict:
        """Otimiza uma tarefa específica."""
        # Como o BERT é um modelo de classificação, usamos regras predefinidas
        if "memória" in task_name.lower():
            return {
                "acoes": ["limpar_temp", "limpar_cache", "otimizar_virtual"],
                "ordem": 1,
                "riscos": ["Nenhum risco significativo"],
                "metricas": ["Redução do uso de memória"]
            }
        elif "disco" in task_name.lower():
            return {
                "acoes": ["limpar_temp", "defrag", "limpar_lixeira"],
                "ordem": 1,
                "riscos": ["Nenhum risco significativo"],
                "metricas": ["Aumento do espaço livre"]
            }
        elif "rede" in task_name.lower():
            return {
                "acoes": ["limpar_cache", "reset_rede"],
                "ordem": 1,
                "riscos": ["Reconexão temporária necessária"],
                "metricas": ["Melhoria na conectividade"]
            }
        else:
            return {
                "acoes": ["Executar tarefa padrão"],
                "ordem": 1,
                "riscos": ["Desconhecido"],
                "metricas": ["Conclusão da tarefa"]
            }

class SystemAnalyzer:
    """Classe para análise do sistema."""
    
    def __init__(self, llm_agent: LLMAgent):
        self.wmi = wmi.WMI()
        self.system_info = {}
        self.llm_agent = llm_agent
        
    def get_system_info(self) -> Dict:
        """Obtém informações detalhadas do sistema."""
        print(f"\n{Fore.CYAN}Analisando sistema...{Style.RESET_ALL}")
        try:
            self.system_info = {
                'os': platform.system() + ' ' + platform.release(),
                'processor': platform.processor(),
                'ram': f"{round(psutil.virtual_memory().total / (1024**3), 2)} GB",
                'disk': self._get_disk_info(),
                'gpu': self._get_gpu_info(),
                'network': self._get_network_info(),
                'startup_programs': self._get_startup_programs(),
                'running_processes': len(psutil.pids()),
                'cpu_usage': round(psutil.cpu_percent(interval=1), 1),
                'memory_usage': round(psutil.virtual_memory().percent, 1),
                'disk_usage': round(psutil.disk_usage('/').percent, 1)
            }
            
            # Análise inteligente usando LLM
            analysis = self.llm_agent.analyze_system_state(self.system_info)
            self.system_info['llm_analysis'] = analysis
            
            return self.system_info
        except Exception as e:
            logging.error(f"Erro ao obter informações do sistema: {str(e)}")
            return {}

    def _get_disk_info(self) -> List[Dict]:
        """Obtém informações dos discos."""
        disks = []
        for disk in self.wmi.Win32_LogicalDisk():
            if disk.DriveType == 3:  # Disco fixo
                try:
                    free_space = float(disk.FreeSpace) / (1024**3)
                    total_space = float(disk.Size) / (1024**3)
                    disks.append({
                        'drive': disk.DeviceID,
                        'total': f"{total_space:.2f} GB",
                        'free': f"{free_space:.2f} GB",
                        'usage': f"{((total_space - free_space) / total_space * 100):.1f}%"
                    })
                except:
                    continue
        return disks

    def _get_gpu_info(self) -> List[Dict]:
        """Obtém informações das GPUs."""
        try:
            gpus = GPUtil.getGPUs()
            return [{
                'name': gpu.name,
                'memory_total': f"{gpu.memoryTotal} MB",
                'memory_used': f"{gpu.memoryUsed} MB",
                'temperature': f"{gpu.temperature}°C"
            } for gpu in gpus]
        except:
            return []

    def _get_network_info(self) -> Dict:
        """Obtém informações da rede."""
        try:
            net_io = psutil.net_io_counters()
            return {
                'bytes_sent': humanize.naturalsize(net_io.bytes_sent),
                'bytes_recv': humanize.naturalsize(net_io.bytes_recv),
                'connections': len(psutil.net_connections())
            }
        except:
            return {}

    def _get_startup_programs(self) -> List[Dict]:
        """Obtém lista de programas que iniciam com o Windows."""
        startup_programs = []
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run")
            i = 0
            while True:
                try:
                    name, value, _ = winreg.EnumValue(key, i)
                    startup_programs.append({'name': name, 'path': value})
                    i += 1
                except WindowsError:
                    break
        except Exception as e:
            logging.error(f"Erro ao obter programas de inicialização: {str(e)}")
        return startup_programs

class AIAgents:
    """Classe para gerenciar diferentes agentes de IA especializados."""
    
    def __init__(self):
        self.performance_agent = None
        self.security_agent = None
        self.optimization_agent = None
        self.analysis_agent = None
        self.prediction_agent = None
        self.available = False
        self.models_loaded = False
        
    def initialize_agents(self):
        """Inicializa todos os agentes de IA."""
        print(f"{Fore.YELLOW}Iniciando agentes de IA...{Style.RESET_ALL}")
        try:
            # Carrega modelos base
            self._load_base_models()
            
            # Inicializa agentes especializados
            self.performance_agent = PerformanceAgent(self.models)
            self.security_agent = SecurityAgent(self.models)
            self.optimization_agent = OptimizationAgent(self.models)
            self.analysis_agent = AnalysisAgent(self.models)
            self.prediction_agent = PredictionAgent(self.models)
            
            self.available = True
            self.models_loaded = True
            print(f"{Fore.GREEN}Agentes de IA iniciados com sucesso!{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}Erro ao iniciar agentes de IA: {str(e)}{Style.RESET_ALL}")
            self.available = False
    
    def _load_base_models(self):
        """Carrega os modelos base necessários para os agentes."""
        self.models = {
            'bert': AutoModelForSequenceClassification.from_pretrained("bert-base-uncased"),
            'tokenizer': AutoTokenizer.from_pretrained("bert-base-uncased"),
            'sentence_transformer': SentenceTransformer('all-MiniLM-L6-v2'),
            'causal_lm': AutoModelForCausalLM.from_pretrained("gpt2")
        }
        
        # Move modelos para GPU se disponível
        if torch.cuda.is_available():
            for model in self.models.values():
                if isinstance(model, torch.nn.Module):
                    model.to('cuda')
    
    def analyze_system(self, system_info: Dict) -> Dict:
        """Realiza análise completa do sistema usando todos os agentes."""
        if not self.available:
            return self._get_default_analysis(system_info)
        
        try:
            # Análise de performance
            perf_analysis = self.performance_agent.analyze(system_info)
            
            # Análise de segurança
            security_analysis = self.security_agent.analyze(system_info)
            
            # Análise geral
            general_analysis = self.analysis_agent.analyze(system_info)
            
            # Previsões
            predictions = self.prediction_agent.predict(system_info)
            
            # Otimizações recomendadas
            optimizations = self.optimization_agent.get_recommendations(system_info)
            
            return {
                'performance': perf_analysis,
                'security': security_analysis,
                'general': general_analysis,
                'predictions': predictions,
                'optimizations': optimizations
            }
        except Exception as e:
            logging.error(f"Erro na análise do sistema: {str(e)}")
            return self._get_default_analysis(system_info)
    
    def _get_default_analysis(self, system_info: Dict) -> Dict:
        """Fornece análise padrão quando os agentes não estão disponíveis."""
        return {
            'performance': {'status': 'unknown', 'issues': [], 'recommendations': []},
            'security': {'status': 'unknown', 'issues': [], 'recommendations': []},
            'general': {'status': 'unknown', 'issues': [], 'recommendations': []},
            'predictions': {'short_term': [], 'long_term': []},
            'optimizations': []
        }

class PerformanceAgent:
    """Agente especializado em análise de performance."""
    
    def __init__(self, models):
        self.models = models
        self.anomaly_detector = IsolationForest(contamination=0.1)
    
    def analyze(self, system_info: Dict) -> Dict:
        """Analisa a performance do sistema."""
        metrics = self._extract_metrics(system_info)
        anomalies = self._detect_anomalies(metrics)
        recommendations = self._generate_recommendations(metrics, anomalies)
        
        return {
            'status': self._determine_status(metrics),
            'metrics': metrics,
            'anomalies': anomalies,
            'recommendations': recommendations
        }
    
    def _extract_metrics(self, system_info: Dict) -> Dict:
        """Extrai métricas relevantes do sistema."""
        return {
            'cpu_usage': system_info.get('cpu_usage', 0),
            'memory_usage': system_info.get('memory_usage', 0),
            'disk_usage': system_info.get('disk_usage', 0),
            'process_count': system_info.get('running_processes', 0)
        }
    
    def _detect_anomalies(self, metrics: Dict) -> List[str]:
        """Detecta anomalias nas métricas do sistema."""
        anomalies = []
        if metrics['cpu_usage'] > 90:
            anomalies.append("Uso de CPU extremamente alto")
        if metrics['memory_usage'] > 90:
            anomalies.append("Uso de memória extremamente alto")
        if metrics['disk_usage'] > 95:
            anomalies.append("Espaço em disco crítico")
        return anomalies
    
    def _generate_recommendations(self, metrics: Dict, anomalies: List[str]) -> List[str]:
        """Gera recomendações baseadas nas métricas e anomalias."""
        recommendations = []
        if "Uso de CPU extremamente alto" in anomalies:
            recommendations.append("Feche programas não utilizados")
            recommendations.append("Verifique processos em segundo plano")
        if "Uso de memória extremamente alto" in anomalies:
            recommendations.append("Aumente a memória virtual")
            recommendations.append("Feche aplicativos pesados")
        return recommendations
    
    def _determine_status(self, metrics: Dict) -> str:
        """Determina o status geral da performance."""
        if any(v > 90 for v in metrics.values()):
            return "crítico"
        elif any(v > 80 for v in metrics.values()):
            return "atenção"
        return "bom"

class SecurityAgent:
    """Agente especializado em análise de segurança."""
    
    def __init__(self, models):
        self.models = models
    
    def analyze(self, system_info: Dict) -> Dict:
        """Analisa a segurança do sistema."""
        vulnerabilities = self._check_vulnerabilities(system_info)
        recommendations = self._generate_recommendations(vulnerabilities)
        
        return {
            'status': self._determine_status(vulnerabilities),
            'vulnerabilities': vulnerabilities,
            'recommendations': recommendations
        }
    
    def _check_vulnerabilities(self, system_info: Dict) -> List[str]:
        """Verifica vulnerabilidades no sistema."""
        vulnerabilities = []
        # Verifica serviços críticos
        if not self._check_antivirus():
            vulnerabilities.append("Antivírus não detectado")
        if not self._check_firewall():
            vulnerabilities.append("Firewall pode estar desativado")
        return vulnerabilities
    
    def _check_antivirus(self) -> bool:
        """Verifica se há antivírus ativo."""
        try:
            wmi = wmi.WMI()
            antivirus = wmi.SecurityCenter2_AntivirusProduct()
            return len(antivirus) > 0
        except:
            return False
    
    def _check_firewall(self) -> bool:
        """Verifica se o firewall está ativo."""
        try:
            wmi = wmi.WMI()
            firewall = wmi.MSFT_NetFirewallProfile()
            return any(f.Enabled for f in firewall)
        except:
            return False
    
    def _generate_recommendations(self, vulnerabilities: List[str]) -> List[str]:
        """Gera recomendações de segurança."""
        recommendations = []
        if "Antivírus não detectado" in vulnerabilities:
            recommendations.append("Instale um antivírus confiável")
        if "Firewall pode estar desativado" in vulnerabilities:
            recommendations.append("Ative o firewall do Windows")
        return recommendations
    
    def _determine_status(self, vulnerabilities: List[str]) -> str:
        """Determina o status de segurança."""
        if len(vulnerabilities) > 2:
            return "crítico"
        elif vulnerabilities:
            return "atenção"
        return "bom"

class OptimizationAgent:
    """Agente especializado em otimizações do sistema."""
    
    def __init__(self, models):
        self.models = models
        self.optimization_history = []
    
    def get_recommendations(self, system_info: Dict) -> List[Dict]:
        """Gera recomendações de otimização."""
        recommendations = []
        
        # Análise de disco
        disk_recs = self._analyze_disk(system_info)
        recommendations.extend(disk_recs)
        
        # Análise de memória
        memory_recs = self._analyze_memory(system_info)
        recommendations.extend(memory_recs)
        
        # Análise de processos
        process_recs = self._analyze_processes(system_info)
        recommendations.extend(process_recs)
        
        return recommendations
    
    def _analyze_disk(self, system_info: Dict) -> List[Dict]:
        """Analisa e recomenda otimizações de disco."""
        recommendations = []
        for disk in system_info.get('disk', []):
            usage = float(disk['usage'].strip('%'))
            if usage > 90:
                recommendations.append({
                    'type': 'disk',
                    'priority': 'high',
                    'action': 'cleanup',
                    'description': f'Libere espaço no disco {disk["drive"]}'
                })
            elif usage > 80:
                recommendations.append({
                    'type': 'disk',
                    'priority': 'medium',
                    'action': 'defrag',
                    'description': f'Desfragmente o disco {disk["drive"]}'
                })
        return recommendations
    
    def _analyze_memory(self, system_info: Dict) -> List[Dict]:
        """Analisa e recomenda otimizações de memória."""
        recommendations = []
        memory_usage = system_info.get('memory_usage', 0)
        if memory_usage > 90:
            recommendations.append({
                'type': 'memory',
                'priority': 'high',
                'action': 'optimize',
                'description': 'Otimize o uso de memória virtual'
            })
        return recommendations
    
    def _analyze_processes(self, system_info: Dict) -> List[Dict]:
        """Analisa e recomenda otimizações de processos."""
        recommendations = []
        process_count = system_info.get('running_processes', 0)
        if process_count > 100:
            recommendations.append({
                'type': 'process',
                'priority': 'medium',
                'action': 'cleanup',
                'description': 'Reduza o número de processos em execução'
            })
        return recommendations

class AnalysisAgent:
    """Agente especializado em análise geral do sistema."""
    
    def __init__(self, models):
        self.models = models
        self.history = []
    
    def analyze(self, system_info: Dict) -> Dict:
        """Realiza análise geral do sistema."""
        analysis = {
            'status': self._determine_overall_status(system_info),
            'issues': self._identify_issues(system_info),
            'recommendations': self._generate_recommendations(system_info),
            'trends': self._analyze_trends(system_info)
        }
        self.history.append(analysis)
        return analysis
    
    def _determine_overall_status(self, system_info: Dict) -> str:
        """Determina o status geral do sistema."""
        critical_metrics = [
            system_info.get('cpu_usage', 0),
            system_info.get('memory_usage', 0),
            system_info.get('disk_usage', 0)
        ]
        
        if any(m > 90 for m in critical_metrics):
            return "crítico"
        elif any(m > 80 for m in critical_metrics):
            return "atenção"
        return "bom"
    
    def _identify_issues(self, system_info: Dict) -> List[str]:
        """Identifica problemas no sistema."""
        issues = []
        if system_info.get('cpu_usage', 0) > 80:
            issues.append("Alto uso de CPU")
        if system_info.get('memory_usage', 0) > 80:
            issues.append("Alto uso de memória")
        if system_info.get('disk_usage', 0) > 90:
            issues.append("Espaço em disco crítico")
        return issues
    
    def _generate_recommendations(self, system_info: Dict) -> List[str]:
        """Gera recomendações baseadas na análise."""
        recommendations = []
        if "Alto uso de CPU" in self._identify_issues(system_info):
            recommendations.append("Otimize processos em segundo plano")
        if "Alto uso de memória" in self._identify_issues(system_info):
            recommendations.append("Aumente a memória virtual")
        if "Espaço em disco crítico" in self._identify_issues(system_info):
            recommendations.append("Libere espaço no disco")
        return recommendations
    
    def _analyze_trends(self, system_info: Dict) -> Dict:
        """Analisa tendências do sistema."""
        if len(self.history) < 2:
            return {'trend': 'estável', 'confidence': 0.0}
        
        # Análise simples de tendências
        recent = self.history[-1]
        previous = self.history[-2]
        
        if recent['status'] == 'crítico' and previous['status'] != 'crítico':
            return {'trend': 'piorando', 'confidence': 0.8}
        elif recent['status'] == 'bom' and previous['status'] != 'bom':
            return {'trend': 'melhorando', 'confidence': 0.8}
        
        return {'trend': 'estável', 'confidence': 0.6}

class PredictionAgent:
    """Agente especializado em previsões do sistema."""
    
    def __init__(self, models):
        self.models = models
        self.history = []
    
    def predict(self, system_info: Dict) -> Dict:
        """Realiza previsões sobre o sistema."""
        self.history.append(system_info)
        
        if len(self.history) < 3:
            return {
                'short_term': ["Dados insuficientes para previsões"],
                'long_term': ["Dados insuficientes para previsões"]
            }
        
        return {
            'short_term': self._predict_short_term(),
            'long_term': self._predict_long_term()
        }
    
    def _predict_short_term(self) -> List[str]:
        """Faz previsões de curto prazo."""
        predictions = []
        recent = self.history[-3:]
        
        # Análise de tendência de CPU
        cpu_trend = [h.get('cpu_usage', 0) for h in recent]
        if all(cpu_trend[i] > cpu_trend[i-1] for i in range(1, len(cpu_trend))):
            predictions.append("Uso de CPU continuará aumentando")
        
        # Análise de tendência de memória
        memory_trend = [h.get('memory_usage', 0) for h in recent]
        if all(memory_trend[i] > memory_trend[i-1] for i in range(1, len(memory_trend))):
            predictions.append("Uso de memória continuará aumentando")
        
        return predictions
    
    def _predict_long_term(self) -> List[str]:
        """Faz previsões de longo prazo."""
        predictions = []
        
        # Análise de tendência de disco
        disk_usage = [h.get('disk_usage', 0) for h in self.history]
        if len(disk_usage) > 5 and all(disk_usage[i] > disk_usage[i-1] for i in range(1, len(disk_usage))):
            predictions.append("Espaço em disco pode se tornar crítico em breve")
        
        return predictions

class SystemOptimizer:
    """Classe para otimização do sistema."""
    
    def __init__(self):
        self.llm_agent = LLMAgent()
        self.ai_agents = AIAgents()
        self.analyzer = SystemAnalyzer(self.llm_agent)
        self.optimization_results = {}
        
    def run_optimization(self):
        """Executa todas as otimizações."""
        print(f"\n{Fore.GREEN}=== Iniciando Otimização do Sistema ==={Style.RESET_ALL}")
        
        # Inicializa os agentes de IA
        self.ai_agents.initialize_agents()
        
        # Verifica privilégios de administrador
        if not self._check_admin():
            self._request_admin()
            return
        
        # Análise inicial do sistema
        print(f"\n{Fore.CYAN}Realizando análise inicial do sistema...{Style.RESET_ALL}")
        initial_state = self.analyzer.get_system_info()
        
        # Análise com agentes de IA
        if self.ai_agents.available:
            print(f"\n{Fore.CYAN}Realizando análise com agentes de IA...{Style.RESET_ALL}")
            ai_analysis = self.ai_agents.analyze_system(initial_state)
            initial_state['ai_analysis'] = ai_analysis
        
        # Lista de otimizações a serem realizadas
        optimizations = [
            ("Otimização de Memória", self._optimize_memory),
            ("Otimização de Disco", self._optimize_disk),
            ("Otimização de Rede", self._optimize_network),
            ("Otimização de Inicialização", self._optimize_startup)
        ]
        
        # Executa otimizações com barra de progresso
        with tqdm(total=len(optimizations), desc="Progresso", unit="otimização") as pbar:
            for name, func in optimizations:
                print(f"\n{Fore.YELLOW}Executando: {name}{Style.RESET_ALL}")
                try:
                    # Obtém plano de otimização do LLM
                    task_data = {
                        "estado_inicial": initial_state,
                        "resultados_anteriores": self.optimization_results
                    }
                    optimization_plan = self.llm_agent.optimize_task(name, task_data)
                    
                    # Executa otimização seguindo o plano
                    result = func(optimization_plan)
                    self.optimization_results.update(result)
                    print(f"{Fore.GREEN}✓ {name} concluída{Style.RESET_ALL}")
                except Exception as e:
                    print(f"{Fore.RED}✗ Erro em {name}: {str(e)}{Style.RESET_ALL}")
                pbar.update(1)
        
        # Análise final do sistema
        print(f"\n{Fore.CYAN}Realizando análise final do sistema...{Style.RESET_ALL}")
        final_state = self.analyzer.get_system_info()
        
        # Gera relatório
        self._generate_report(initial_state, final_state)
        
        # Após as otimizações principais, sugere remoção de softwares antigos
        self._suggest_software_removal()
        
    def _check_admin(self) -> bool:
        """Verifica privilégios de administrador."""
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False
    
    def _request_admin(self):
        """Solicita privilégios de administrador."""
        try:
            python_exe = sys.executable
            script_path = os.path.abspath(__file__)
            cmd = f'Start-Process "{python_exe}" -ArgumentList "{script_path}" -Verb RunAs'
            subprocess.run(['powershell', '-Command', cmd], check=True)
            sys.exit()
        except Exception as e:
            logging.error(f"Erro ao solicitar privilégios de administrador: {str(e)}")
            sys.exit(1)
    
    def _optimize_memory(self, plan: Dict = None) -> Dict:
        """Otimiza o uso de memória."""
        results = {'memory_optimization': {}}
        try:
            if plan and 'acoes' in plan:
                for acao in plan['acoes']:
                    if 'limpar_temp' in acao.lower():
                        self._clear_temp_files()
                    elif 'limpar_cache' in acao.lower():
                        self._clear_system_cache()
                    elif 'otimizar_virtual' in acao.lower():
                        self._optimize_virtual_memory()
            else:
                # Fallback para ações padrão
                self._clear_temp_files()
                self._clear_system_cache()
                self._optimize_virtual_memory()
            
            results['memory_optimization']['status'] = 'success'
        except Exception as e:
            results['memory_optimization']['status'] = 'error'
            results['memory_optimization']['error'] = str(e)
        return results
    
    def _optimize_disk(self, plan: Dict = None) -> Dict:
        """Otimiza o disco."""
        results = {'disk_optimization': {}}
        try:
            if plan and 'acoes' in plan:
                for acao in plan['acoes']:
                    if 'limpar_temp' in acao.lower():
                        self._clear_temp_files()
                    elif 'defrag' in acao.lower():
                        self._defrag_disk()
                    elif 'limpar_lixeira' in acao.lower():
                        self._clear_recycle_bin()
            else:
                # Fallback para ações padrão
                self._clear_temp_files()
                self._defrag_disk()
                self._clear_recycle_bin()
            
            results['disk_optimization']['status'] = 'success'
        except Exception as e:
            results['disk_optimization']['status'] = 'error'
            results['disk_optimization']['error'] = str(e)
        return results
    
    def _optimize_network(self, plan: Dict = None) -> Dict:
        """Otimiza a rede."""
        results = {'network_optimization': {}}
        try:
            if plan and 'acoes' in plan:
                for acao in plan['acoes']:
                    if 'limpar_cache' in acao.lower():
                        self._clear_dns_cache()
                    elif 'reset_rede' in acao.lower():
                        self._reset_network_settings()
            else:
                # Fallback para ações padrão
                self._clear_dns_cache()
                self._reset_network_settings()
            
            results['network_optimization']['status'] = 'success'
        except Exception as e:
            results['network_optimization']['status'] = 'error'
            results['network_optimization']['error'] = str(e)
        return results
    
    def _optimize_startup(self, plan: Dict = None) -> Dict:
        """Otimiza programas de inicialização."""
        results = {'startup_optimization': {}}
        try:
            if plan and 'acoes' in plan:
                for acao in plan['acoes']:
                    if 'desativar_programas' in acao.lower():
                        self._disable_unnecessary_startup()
                    elif 'otimizar_servicos' in acao.lower():
                        self._optimize_services()
            else:
                # Fallback para ações padrão
                self._disable_unnecessary_startup()
                self._optimize_services()
            
            results['startup_optimization']['status'] = 'success'
        except Exception as e:
            results['startup_optimization']['status'] = 'error'
            results['startup_optimization']['error'] = str(e)
        return results
    
    def _clear_temp_files(self):
        """Limpa arquivos temporários."""
        temp_folders = [
            os.environ.get('TEMP'),
            os.path.join(os.environ.get('WINDIR', 'C:\\Windows'), 'Temp'),
            os.path.join(os.environ.get('USERPROFILE'), 'AppData', 'Local', 'Temp'),
        ]
        
        files_in_use = []
        max_retries = 3
        retry_delay = 1  # segundos
        
        for folder in temp_folders:
            if not os.path.exists(folder):
                continue
                
            print(f"{Fore.CYAN}Limpando pasta temporária: {folder}{Style.RESET_ALL}")
            files_cleaned = 0
            files_skipped = 0
            
            try:
                for item in os.listdir(folder):
                    item_path = os.path.join(folder, item)
                    try:
                        if os.path.isfile(item_path):
                            # Tenta deletar o arquivo com retry
                            for attempt in range(max_retries):
                                try:
                                    os.unlink(item_path)
                                    files_cleaned += 1
                                    break
                                except PermissionError:
                                    if attempt < max_retries - 1:
                                        time.sleep(retry_delay)
                                    else:
                                        files_in_use.append(item_path)
                                        files_skipped += 1
                                except Exception as e:
                                    logging.warning(f"Erro ao deletar {item_path}: {str(e)}")
                                    files_skipped += 1
                                    break
                        elif os.path.isdir(item_path):
                            try:
                                shutil.rmtree(item_path, ignore_errors=True)
                                files_cleaned += 1
                            except Exception as e:
                                logging.warning(f"Erro ao deletar pasta {item_path}: {str(e)}")
                                files_skipped += 1
                    except Exception as e:
                        logging.warning(f"Erro ao processar {item_path}: {str(e)}")
                        files_skipped += 1
                        
                print(f"{Fore.GREEN}✓ {files_cleaned} arquivos limpos{Style.RESET_ALL}")
                if files_skipped > 0:
                    print(f"{Fore.YELLOW}⚠ {files_skipped} arquivos não puderam ser removidos{Style.RESET_ALL}")
                    
            except Exception as e:
                logging.error(f"Erro ao acessar pasta {folder}: {str(e)}")
                print(f"{Fore.RED}✗ Erro ao acessar pasta {folder}{Style.RESET_ALL}")
        
        # Tenta limpar arquivos em uso usando o Disk Cleanup
        if files_in_use:
            print(f"\n{Fore.YELLOW}Tentando limpar arquivos em uso usando Disk Cleanup...{Style.RESET_ALL}")
            try:
                subprocess.run(['cleanmgr', '/sagerun:1'], check=False)
                print(f"{Fore.GREEN}✓ Disk Cleanup iniciado{Style.RESET_ALL}")
            except Exception as e:
                logging.error(f"Erro ao iniciar Disk Cleanup: {str(e)}")
                print(f"{Fore.RED}✗ Erro ao iniciar Disk Cleanup{Style.RESET_ALL}")
        
        # Tenta limpar usando o método alternativo
        if files_in_use:
            print(f"\n{Fore.YELLOW}Tentando método alternativo de limpeza...{Style.RESET_ALL}")
            try:
                # Tenta forçar a liberação de arquivos
                subprocess.run(['taskkill', '/F', '/IM', 'explorer.exe'], check=False)
                time.sleep(2)
                subprocess.run(['start', 'explorer.exe'], check=False)
                
                # Tenta limpar novamente os arquivos em uso
                for file_path in files_in_use:
                    try:
                        os.unlink(file_path)
                        print(f"{Fore.GREEN}✓ Arquivo {os.path.basename(file_path)} removido{Style.RESET_ALL}")
                    except:
                        continue
            except Exception as e:
                logging.error(f"Erro no método alternativo: {str(e)}")
                print(f"{Fore.RED}✗ Erro no método alternativo{Style.RESET_ALL}")
    
    def _clear_system_cache(self):
        """Limpa cache do sistema."""
        print(f"{Fore.CYAN}Limpando cache do sistema...{Style.RESET_ALL}")
        try:
            # Limpa cache do Windows
            subprocess.run(['cleanmgr', '/sagerun:1'], check=False)
            
            # Limpa cache do DNS
            subprocess.run(['ipconfig', '/flushdns'], check=False)
            
            # Limpa cache do Windows Store
            subprocess.run(['wsreset.exe'], check=False)
            
            print(f"{Fore.GREEN}✓ Cache do sistema limpo{Style.RESET_ALL}")
        except Exception as e:
            logging.error(f"Erro ao limpar cache do sistema: {str(e)}")
            print(f"{Fore.RED}✗ Erro ao limpar cache do sistema{Style.RESET_ALL}")
    
    def _optimize_virtual_memory(self):
        """Otimiza memória virtual."""
        try:
            # Ajusta tamanho do arquivo de paginação
            subprocess.run(['wmic', 'computersystem', 'set', 'AutomaticManagedPagefile=False'], check=True)
            subprocess.run(['wmic', 'pagefileset', 'create', 'name="C:\\pagefile.sys",initialsize=2048,maximumsize=4096'], check=True)
        except Exception as e:
            logging.error(f"Erro ao otimizar memória virtual: {str(e)}")
    
    def _defrag_disk(self):
        """Desfragmenta o disco."""
        try:
            subprocess.run(['defrag', 'C:', '/O'], check=True)
        except Exception as e:
            logging.error(f"Erro ao desfragmentar disco: {str(e)}")
    
    def _clear_recycle_bin(self):
        """Limpa a lixeira."""
        try:
            # Tenta primeiro o método do win32com
            try:
                shell = win32com.client.Dispatch("Shell.Application")
                recycle_bin = shell.Namespace(10)
                for item in recycle_bin.Items():
                    item.Delete()
            except Exception as e:
                # Se falhar, tenta o método alternativo
                subprocess.run(['rd', '/s', '/q', 'C:\\$Recycle.Bin'], check=False)
                logging.info("Lixeira limpa usando método alternativo")
        except Exception as e:
            logging.error(f"Erro ao limpar lixeira: {str(e)}")
            print(f"{Fore.YELLOW}Aviso: Não foi possível limpar a lixeira completamente{Style.RESET_ALL}")
    
    def _clear_dns_cache(self):
        """Limpa cache DNS."""
        try:
            subprocess.run(['ipconfig', '/flushdns'], check=True)
        except Exception as e:
            logging.error(f"Erro ao limpar cache DNS: {str(e)}")
    
    def _reset_network_settings(self):
        """Reseta configurações de rede."""
        try:
            subprocess.run(['netsh', 'winsock', 'reset'], check=True)
            subprocess.run(['netsh', 'int', 'ip', 'reset'], check=True)
        except Exception as e:
            logging.error(f"Erro ao resetar configurações de rede: {str(e)}")
    
    def _disable_unnecessary_startup(self):
        """Desativa programas desnecessários de inicialização."""
        startup_key = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run"
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, startup_key, 0, winreg.KEY_ALL_ACCESS) as key:
                i = 0
                while True:
                    try:
                        name, value, type = winreg.EnumValue(key, i)
                        if "update" not in name.lower() and "security" not in name.lower():
                            winreg.DeleteValue(key, name)
                        i += 1
                    except WindowsError:
                        break
        except Exception as e:
            logging.error(f"Erro ao modificar programas de inicialização: {str(e)}")
    
    def _optimize_services(self):
        """Otimiza serviços do Windows."""
        try:
            # Desativa serviços desnecessários
            services_to_disable = [
                'DiagTrack',  # Serviço de telemetria
                'SysMain',    # Superfetch
                'WSearch'     # Windows Search
            ]
            
            for service in services_to_disable:
                try:
                    # Primeiro tenta parar o serviço
                    subprocess.run(['sc', 'stop', service], check=False)
                    # Depois configura para não iniciar
                    subprocess.run(['sc', 'config', service, 'start=', 'disabled'], check=False)
                    print(f"{Fore.GREEN}Serviço {service} configurado com sucesso{Style.RESET_ALL}")
                except Exception as e:
                    print(f"{Fore.YELLOW}Aviso: Não foi possível configurar o serviço {service}: {str(e)}{Style.RESET_ALL}")
                    continue
        except Exception as e:
            logging.error(f"Erro ao otimizar serviços: {str(e)}")
            raise
    
    def _check_disk_space(self, drive: str = 'C:') -> Dict:
        """Verifica o espaço em disco e retorna recomendações."""
        try:
            usage = psutil.disk_usage(drive)
            free_gb = usage.free / (1024**3)
            total_gb = usage.total / (1024**3)
            used_percent = usage.percent
            
            return {
                'free_gb': round(free_gb, 2),
                'total_gb': round(total_gb, 2),
                'used_percent': used_percent,
                'is_critical': free_gb < 5 or used_percent > 95,
                'recommendations': self._get_disk_recommendations(free_gb, total_gb, used_percent)
            }
        except Exception as e:
            logging.error(f"Erro ao verificar espaço em disco: {str(e)}")
            return {}

    def _get_disk_recommendations(self, free_gb: float, total_gb: float, used_percent: float) -> List[str]:
        """Gera recomendações específicas baseadas no espaço em disco."""
        recommendations = []
        
        if free_gb < 5:
            recommendations.append(f"CRÍTICO: Apenas {free_gb:.2f} GB livres no disco C:. Recomendado ter pelo menos 5 GB.")
        if used_percent > 95:
            recommendations.append(f"CRÍTICO: Disco C: com {used_percent:.1f}% de uso. Recomendado manter abaixo de 90%.")
        if free_gb < (total_gb * 0.1):
            recommendations.append(f"AVISO: Menos de 10% do disco livre. Considere liberar espaço.")
        
        return recommendations

    def _generate_report(self, initial_state: Dict, final_state: Dict):
        """Gera relatório de otimização formatado."""
        try:
            print(f"\n{Fore.GREEN}=== Relatório de Otimização do Sistema ==={Style.RESET_ALL}")
            
            # Análise LLM do estado final
            if 'llm_analysis' in final_state:
                analysis = final_state['llm_analysis']
                print(f"\n{Fore.CYAN}Análise do Sistema:{Style.RESET_ALL}")
                print("-" * 50)
                print(f"Estado: {analysis.get('estado', 'Desconhecido')}")
                print("\nProblemas Identificados:")
                for problema in analysis.get('problemas', []):
                    print(f"• {problema}")
                print("\nRecomendações:")
                for rec in analysis.get('recomendacoes', []):
                    print(f"• {rec}")
                print(f"\nPrioridade: {analysis.get('prioridade', 3)}/5")
            
            # Verificação de espaço em disco
            disk_check = self._check_disk_space()
            if disk_check.get('is_critical', False):
                print(f"\n{Fore.RED}=== ALERTA CRÍTICO DE ESPAÇO EM DISCO ==={Style.RESET_ALL}")
                for rec in disk_check.get('recommendations', []):
                    print(f"{Fore.RED}• {rec}{Style.RESET_ALL}")
                print(f"{Fore.RED}Recomendado resolver estes problemas antes de continuar.{Style.RESET_ALL}\n")
            
            # Comparação de métricas
            print(f"\n{Fore.CYAN}Comparação de Métricas:{Style.RESET_ALL}")
            print("-" * 50)
            print(f"{'Métrica':<20} {'Antes':<15} {'Depois':<15} {'Diferença':<15}")
            print("-" * 50)
            
            metrics = [
                ('CPU', 'cpu_usage', '%'),
                ('Memória', 'memory_usage', '%'),
                ('Disco', 'disk_usage', '%'),
                ('Processos', 'running_processes', '')
            ]
            
            for name, key, unit in metrics:
                before = initial_state.get(key, 0)
                after = final_state.get(key, 0)
                diff = after - before
                if isinstance(diff, float):
                    diff_str = f"{diff:+.1f}{unit}" if diff != 0 else f"0{unit}"
                else:
                    diff_str = f"{diff:+d}{unit}" if diff != 0 else f"0{unit}"
                print(f"{name:<20} {before:<15}{unit} {after:<15}{unit} {diff_str:<15}")
            
            # Informações do Sistema
            print(f"\n{Fore.CYAN}Informações do Sistema:{Style.RESET_ALL}")
            print("-" * 50)
            print(f"Sistema Operacional: {initial_state.get('os', 'N/A')}")
            print(f"Processador: {initial_state.get('processor', 'N/A')}")
            print(f"Memória RAM: {initial_state.get('ram', 'N/A')}")
            
            # Informações de Disco
            print(f"\n{Fore.CYAN}Informações de Disco:{Style.RESET_ALL}")
            print("-" * 50)
            for disk in initial_state.get('disk', []):
                print(f"Drive {disk['drive']}:")
                print(f"  Total: {disk['total']}")
                print(f"  Livre: {disk['free']}")
                print(f"  Uso: {disk['usage']}")
                
                # Adiciona recomendações específicas para o disco
                if float(disk['usage'].strip('%')) > 90:
                    print(f"  {Fore.YELLOW}Recomendação: Libere espaço neste disco{Style.RESET_ALL}")
            
            # Informações de GPU
            if initial_state.get('gpu'):
                print(f"\n{Fore.CYAN}Informações de GPU:{Style.RESET_ALL}")
                print("-" * 50)
                for gpu in initial_state['gpu']:
                    print(f"GPU: {gpu['name']}")
                    print(f"  Memória Total: {gpu['memory_total']}")
                    print(f"  Memória Usada: {gpu['memory_used']}")
                    print(f"  Temperatura: {gpu['temperature']}")
            
            # Recomendações
            print(f"\n{Fore.CYAN}Recomendações:{Style.RESET_ALL}")
            print("-" * 50)
            
            # Recomendações baseadas no estado do sistema
            recommendations = [
                "1. Mantenha o Windows atualizado",
                "2. Use um antivírus atualizado",
                "3. Mantenha pelo menos 20% de espaço livre no disco C:",
                "4. Faça backup regular dos seus dados",
                "5. Monitore a temperatura do sistema",
                "6. Mantenha os drivers atualizados",
                "7. Desative programas desnecessários na inicialização",
                "8. Limpe regularmente arquivos temporários",
                "9. Mantenha o sistema desfragmentado"
            ]
            
            # Adiciona recomendações específicas baseadas no estado do sistema
            if disk_check.get('is_critical', False):
                recommendations.extend([
                    "10. URGENTE: Libere espaço no disco C:",
                    "11. Considere mover arquivos grandes para outro disco",
                    "12. Use o Disk Cleanup para remover arquivos temporários",
                    "13. Desinstale programas não utilizados"
                ])
            
            if initial_state.get('memory_usage', 0) > 80:
                recommendations.extend([
                    "14. Considere aumentar a memória RAM",
                    "15. Feche programas que não estão em uso"
                ])
            
            for rec in recommendations:
                print(rec)
            
            print(f"\n{Fore.GREEN}Otimização concluída com sucesso!{Style.RESET_ALL}")
            
            # Adiciona contagem regressiva para reiniciar o Windows
            print(f"\n{Fore.YELLOW}O sistema será reiniciado em 10 segundos para aplicar todas as alterações...{Style.RESET_ALL}")
            for i in range(10, 0, -1):
                print(f"{Fore.YELLOW}Reiniciando em {i} segundos...{Style.RESET_ALL}")
                time.sleep(1)
            
            # Reinicia o Windows
            subprocess.run(['shutdown', '/r', '/t', '0'], check=True)
            
        except Exception as e:
            print(f"{Fore.RED}Erro ao gerar relatório: {str(e)}{Style.RESET_ALL}")
            logging.error(f"Erro ao gerar relatório: {str(e)}")
            # Tenta reiniciar mesmo em caso de erro
            try:
                subprocess.run(['shutdown', '/r', '/t', '0'], check=True)
            except:
                pass

    def _list_installed_software(self) -> list:
        """Lista todos os softwares instalados no Windows."""
        uninstall_keys = [
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
            r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"
        ]
        software_list = []
        for root in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):
            for key_path in uninstall_keys:
                try:
                    with winreg.OpenKey(root, key_path) as key:
                        for i in range(0, winreg.QueryInfoKey(key)[0]):
                            try:
                                subkey_name = winreg.EnumKey(key, i)
                                with winreg.OpenKey(key, subkey_name) as subkey:
                                    name = winreg.QueryValueEx(subkey, "DisplayName")[0] if self._has_value(subkey, "DisplayName") else None
                                    install_date = winreg.QueryValueEx(subkey, "InstallDate")[0] if self._has_value(subkey, "InstallDate") else None
                                    last_used = winreg.QueryValueEx(subkey, "LastUsed")[0] if self._has_value(subkey, "LastUsed") else None
                                    uninstall_str = winreg.QueryValueEx(subkey, "UninstallString")[0] if self._has_value(subkey, "UninstallString") else None
                                    if name:
                                        software_list.append({
                                            "name": name,
                                            "install_date": install_date,
                                            "last_used": last_used,
                                            "uninstall_str": uninstall_str
                                        })
                            except Exception:
                                continue
                except Exception:
                    continue
        return software_list

    def _has_value(self, key, value):
        try:
            winreg.QueryValueEx(key, value)
            return True
        except:
            return False

    def _suggest_software_removal(self):
        """Sugere softwares para remoção com base no último uso e criticidade."""
        print(f"\n{Fore.CYAN}Analisando softwares instalados...{Style.RESET_ALL}")
        softwares = self._list_installed_software()
        now = datetime.now()
        threshold = now - timedelta(days=90)
        candidates = []
        for sw in softwares:
            # Tenta obter a data de último uso ou instalação
            last_used = sw.get("last_used") or sw.get("install_date")
            if last_used and len(str(last_used)) >= 8:
                try:
                    # Formato esperado: AAAAMMDD
                    dt = datetime.strptime(str(last_used)[:8], "%Y%m%d")
                    if dt < threshold:
                        # Filtros de criticidade
                        if not self._is_critical_software(sw["name"]):
                            candidates.append(sw)
                except Exception:
                    continue
        if not candidates:
            print(f"{Fore.GREEN}Nenhum software antigo e não crítico encontrado para remoção.{Style.RESET_ALL}")
            return
        print(f"{Fore.YELLOW}Softwares sugeridos para desinstalação:{Style.RESET_ALL}")
        for idx, sw in enumerate(candidates, 1):
            print(f"{idx}. {sw['name']} (Último uso/instalação: {sw.get('last_used') or sw.get('install_date')})")
        # Pergunta ao usuário se deseja remover
        resp = input(f"\nDeseja desinstalar todos os softwares listados acima? (s/N): ").strip().lower()
        if resp == 's':
            for sw in candidates:
                self._uninstall_software(sw)
        else:
            print(f"{Fore.YELLOW}Nenhum software foi removido.{Style.RESET_ALL}")

    def _is_critical_software(self, name: str) -> bool:
        """Define se o software é crítico para o sistema."""
        critical_keywords = [
            "Microsoft", "Windows", "Driver", "NVIDIA", "Intel", "AMD", "Framework", "Security", "Update", "Redistributable"
        ]
        return any(kw.lower() in name.lower() for kw in critical_keywords)

    def _uninstall_software(self, sw: dict):
        """Executa a desinstalação do software."""
        uninstall_str = sw.get("uninstall_str")
        if uninstall_str:
            print(f"{Fore.YELLOW}Desinstalando: {sw['name']}...{Style.RESET_ALL}")
            try:
                subprocess.run(uninstall_str, shell=True, check=False)
                print(f"{Fore.GREEN}✓ {sw['name']} removido (verifique a conclusão na tela).{Style.RESET_ALL}")
            except Exception as e:
                print(f"{Fore.RED}✗ Erro ao remover {sw['name']}: {str(e)}{Style.RESET_ALL}")
        else:
            print(f"{Fore.RED}✗ Não foi possível encontrar comando de desinstalação para {sw['name']}.{Style.RESET_ALL}")

def main():
    """Função principal."""
    try:
        optimizer = SystemOptimizer()
        optimizer.run_optimization()
    except Exception as e:
        print(f"{Fore.RED}Erro durante a execução: {str(e)}{Style.RESET_ALL}")
        logging.error(f"Erro durante a execução: {str(e)}")
        input("\nPressione Enter para sair...")

if __name__ == "__main__":
    main() 
