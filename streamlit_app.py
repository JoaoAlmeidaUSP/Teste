import streamlit as st
import tempfile
import os
import PyPDF2
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
import time
from datetime import datetime, timedelta
import json
import hashlib
from pathlib import Path
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

# Configuração da página com tema escuro e moderno
st.set_page_config(
    page_title="LexFácil • AI Legal Assistant", 
    layout="wide", 
    initial_sidebar_state="expanded",
    page_icon="⚖️"
)

# CSS customizado para layout moderno
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Variáveis CSS */
    :root {
        --primary-color: #667eea;
        --secondary-color: #764ba2;
        --accent-color: #f093fb;
        --background-dark: #0f1419;
        --surface-dark: #1a1f2e;
        --text-primary: #ffffff;
        --text-secondary: #94a3b8;
        --border-color: #334155;
        --success-color: #10b981;
        --warning-color: #f59e0b;
        --error-color: #ef4444;
    }
    
    /* Reset e base */
    .stApp {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        font-family: 'Inter', sans-serif;
    }
    
    /* Sidebar moderna */
    .css-1d391kg {
        background: rgba(15, 20, 25, 0.95);
        backdrop-filter: blur(10px);
        border-right: 1px solid var(--border-color);
    }
    
    /* Main content area */
    .main .block-container {
        background: rgba(26, 31, 46, 0.9);
        backdrop-filter: blur(20px);
        border-radius: 20px;
        border: 1px solid var(--border-color);
        box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
        margin-top: 2rem;
        padding: 2rem;
    }
    
    /* Títulos com gradiente */
    .gradient-title {
        background: linear-gradient(135deg, #667eea, #764ba2, #f093fb);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-weight: 700;
        font-size: 2.5rem;
        text-align: center;
        margin-bottom: 1rem;
    }
    
    /* Cards modernos */
    .modern-card {
        background: rgba(51, 65, 85, 0.3);
        border: 1px solid var(--border-color);
        border-radius: 16px;
        padding: 1.5rem;
        margin: 1rem 0;
        backdrop-filter: blur(10px);
        transition: all 0.3s ease;
    }
    
    .modern-card:hover {
        transform: translateY(-2px);
        border-color: var(--primary-color);
        box-shadow: 0 10px 25px rgba(102, 126, 234, 0.2);
    }
    
    /* Botões com estilo futurista */
    .stButton > button {
        background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
        border: none;
        border-radius: 12px;
        color: white;
        font-weight: 600;
        padding: 0.75rem 1.5rem;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4);
    }
    
    /* Chat messages estilizadas */
    .chat-message {
        background: rgba(51, 65, 85, 0.3);
        border-radius: 16px;
        padding: 1rem;
        margin: 0.5rem 0;
        border-left: 4px solid var(--primary-color);
        backdrop-filter: blur(10px);
    }
    
    /* Indicadores de status */
    .status-indicator {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.5rem 1rem;
        background: rgba(16, 185, 129, 0.2);
        border: 1px solid var(--success-color);
        border-radius: 20px;
        color: var(--success-color);
        font-size: 0.875rem;
        font-weight: 500;
    }
    
    /* Métricas dashboard */
    .metric-card {
        background: rgba(51, 65, 85, 0.2);
        border-radius: 12px;
        padding: 1rem;
        text-align: center;
        border: 1px solid var(--border-color);
        backdrop-filter: blur(10px);
    }
    
    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        color: var(--primary-color);
    }
    
    .metric-label {
        color: var(--text-secondary);
        font-size: 0.875rem;
        margin-top: 0.25rem;
    }
    
    /* Upload area */
    .upload-area {
        border: 2px dashed var(--primary-color);
        border-radius: 16px;
        padding: 2rem;
        text-align: center;
        background: rgba(102, 126, 234, 0.1);
        transition: all 0.3s ease;
    }
    
    .upload-area:hover {
        background: rgba(102, 126, 234, 0.2);
        border-color: var(--accent-color);
    }
    
    /* Animations */
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }
    
    .loading-pulse {
        animation: pulse 2s infinite;
    }
    
    /* Scrollbar customizada */
    ::-webkit-scrollbar {
        width: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: var(--surface-dark);
    }
    
    ::-webkit-scrollbar-thumb {
        background: var(--primary-color);
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: var(--secondary-color);
    }
</style>
""", unsafe_allow_html=True)

# Configuração da API (mantenha sua chave)
GOOGLE_API_KEY = "AIzaSyAi-EZdS0Jners99DuB_5DkROiK16ghPnM"

if not GOOGLE_API_KEY or GOOGLE_API_KEY == "YOUR_ACTUAL_API_KEY_HERE": 
    st.error("⚠️ ATENÇÃO: A CHAVE API DO GEMINI NÃO FOI DEFINIDA CORRETAMENTE NO CÓDIGO!")
    st.error("Por favor, substitua 'YOUR_ACTUAL_API_KEY_HERE' pela sua chave API real na variável GOOGLE_API_KEY no código-fonte.")
    st.warning("Lembre-se: Não compartilhe este código com sua chave API real em repositórios públicos.")
    st.stop()

try:
    genai.configure(api_key=GOOGLE_API_KEY)
    safety_settings = {
        HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
    }
    model = genai.GenerativeModel(
        model_name='gemini-1.5-flash-latest',
        safety_settings=safety_settings
    )
except Exception as e:
    st.error(f"❌ Falha ao configurar a API do Gemini: {str(e)}")
    st.stop()

# === SISTEMA DE MÉTRICAS ===
class MetricsTracker:
    def __init__(self):
        self.metrics_file = Path("lexfacil_metrics.json")
        self.session_id = self._generate_session_id()
        
    def _generate_session_id(self):
        """Gera um ID único para a sessão"""
        timestamp = str(datetime.now().timestamp())
        return hashlib.md5(timestamp.encode()).hexdigest()[:8]
    
    def _load_metrics(self):
        """Carrega métricas do arquivo"""
        if self.metrics_file.exists():
            try:
                with open(self.metrics_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return self._get_default_metrics()
        return self._get_default_metrics()
    
    def _get_default_metrics(self):
        """Retorna estrutura padrão de métricas"""
        return {
            "total_sessions": 0,
            "total_documents": 0,
            "total_questions": 0,
            "total_analyses": 0,
            "persona_usage": {
                "👨‍👩‍👧‍👦 Cidadão": 0,
                "👨‍💼 Empresário": 0,
                "👩‍⚖️ Advogado": 0,
                "🏛️ Servidor Público": 0
            },
            "feature_usage": {
                "analysis": 0,
                "summary": 0,
                "practical_cases": 0,
                "deadlines": 0,
                "semantic_search": 0
            },
            "sessions": [],
            "daily_stats": {}
        }
    
    def _save_metrics(self, metrics):
        """Salva métricas no arquivo"""
        try:
            with open(self.metrics_file, 'w', encoding='utf-8') as f:
                json.dump(metrics, f, indent=2, ensure_ascii=False, default=str)
        except Exception as e:
            st.error(f"Erro ao salvar métricas: {e}")
    
    def track_session_start(self):
        """Registra início de sessão"""
        metrics = self._load_metrics()
        metrics["total_sessions"] += 1
        
        today = datetime.now().strftime("%Y-%m-%d")
        if today not in metrics["daily_stats"]:
            metrics["daily_stats"][today] = {
                "sessions": 0,
                "documents": 0,
                "questions": 0
            }
        metrics["daily_stats"][today]["sessions"] += 1
        
        session_data = {
            "id": self.session_id,
            "start_time": datetime.now().isoformat(),
            "persona": st.session_state.get("persona_usuario", "👨‍👩‍👧‍👦 Cidadão"),
            "questions": 0,
            "features_used": []
        }
        metrics["sessions"].append(session_data)
        
        self._save_metrics(metrics)
    
    def track_document_upload(self, filename):
        """Registra upload de documento"""
        metrics = self._load_metrics()
        metrics["total_documents"] += 1
        
        today = datetime.now().strftime("%Y-%m-%d")
        if today in metrics["daily_stats"]:
            metrics["daily_stats"][today]["documents"] += 1
        
        self._save_metrics(metrics)
    
    def track_question(self):
        """Registra pergunta feita"""
        metrics = self._load_metrics()
        metrics["total_questions"] += 1
        
        today = datetime.now().strftime("%Y-%m-%d")
        if today in metrics["daily_stats"]:
            metrics["daily_stats"][today]["questions"] += 1
        
        self._save_metrics(metrics)
    
    def track_feature_usage(self, feature):
        """Registra uso de funcionalidade"""
        metrics = self._load_metrics()
        if feature in metrics["feature_usage"]:
            metrics["feature_usage"][feature] += 1
        
        self._save_metrics(metrics)
    
    def track_persona_change(self, persona):
        """Registra mudança de persona"""
        metrics = self._load_metrics()
        if persona in metrics["persona_usage"]:
            metrics["persona_usage"][persona] += 1
        
        self._save_metrics(metrics)
    
    def get_dashboard_data(self):
        """Retorna dados para dashboard"""
        metrics = self._load_metrics()
        
        # Dados dos últimos 7 dias
        last_7_days = []
        for i in range(7):
            date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            last_7_days.append({
                "date": date,
                "sessions": metrics["daily_stats"].get(date, {}).get("sessions", 0),
                "questions": metrics["daily_stats"].get(date, {}).get("questions", 0),
                "documents": metrics["daily_stats"].get(date, {}).get("documents", 0)
            })
        
        return {
            "summary": metrics,
            "last_7_days": list(reversed(last_7_days))
        }

# Inicializar tracker de métricas
if 'metrics_tracker' not in st.session_state:
    st.session_state.metrics_tracker = MetricsTracker()
    st.session_state.metrics_tracker.track_session_start()

# Inicialização do session state (mantém o original)
if 'chat_messages' not in st.session_state:
    st.session_state.chat_messages = []
if 'texto_lei' not in st.session_state:
    st.session_state.texto_lei = ""
if 'nome_documento' not in st.session_state:
    st.session_state.nome_documento = ""
if 'analise_realizada' not in st.session_state:
    st.session_state.analise_realizada = False
if 'resumo_realizado' not in st.session_state:
    st.session_state.resumo_realizado = False
if 'contexto_conversa' not in st.session_state:
    st.session_state.contexto_conversa = ""
if 'persona_usuario' not in st.session_state:
    st.session_state.persona_usuario = "👨‍👩‍👧‍👦 Cidadão"
if 'casos_praticos' not in st.session_state:
    st.session_state.casos_praticos = []
if 'prazos_extraidos' not in st.session_state:
    st.session_state.prazos_extraidos = []

# === FUNÇÕES HELPER (mantém as originais) ===
def extrair_texto_pdf(caminho_pdf):
    texto = ""
    try:
        with open(caminho_pdf, 'rb') as arquivo:
            leitor = PyPDF2.PdfReader(arquivo)
            if not leitor.pages:
                return ""
            for pagina_num, pagina in enumerate(leitor.pages):
                texto_pagina = pagina.extract_text()
                if texto_pagina:
                    texto += texto_pagina
        return texto.strip()
    except Exception as e:
        st.error(f"Erro ao processar o PDF: {str(e)}")
        return ""

def call_gemini_api(prompt_text, task_name="tarefa"):
    try:
        response = model.generate_content(prompt_text)
        if not response.candidates:
            if response.prompt_feedback and response.prompt_feedback.block_reason:
                block_reason_message = response.prompt_feedback.block_reason.name
                return f"Conteúdo bloqueado: {block_reason_message}"
            else:
                return "Nenhum conteúdo gerado."
        return response.text
    except Exception as e:
        st.error(f"❌ Erro durante a {task_name} com a API Gemini: {str(e)}")
        return f"Erro na API: {str(e)}"

def criar_contexto_inicial():
    """Cria o contexto inicial para o agente conversacional"""
    if st.session_state.texto_lei:
        personas = {
            "👨‍👩‍👧‍👦 Cidadão": "Use linguagem ultra-simples, foque no impacto pessoal e familiar, dê exemplos do cotidiano",
            "👨‍💼 Empresário": "Foque em impactos comerciais, custos, prazos de adequação, riscos para negócios",
            "👩‍⚖️ Advogado": "Pode usar termos técnicos, foque em interpretação jurídica, precedentes, aplicação prática",
            "🏛️ Servidor Público": "Foque na aplicação da norma, procedimentos, competências dos órgãos"
        }
        
        contexto_persona = personas.get(st.session_state.persona_usuario, personas["👨‍👩‍👧‍👦 Cidadão"])
        
        contexto = f"""
        DOCUMENTO JURÍDICO CARREGADO: {st.session_state.nome_documento}
        
        TEXTO DA LEI/NORMA:
        {st.session_state.texto_lei[:15000]}
        
        PERFIL DO USUÁRIO: {st.session_state.persona_usuario}
        INSTRUÇÕES ESPECÍFICAS: {contexto_persona}
        
        INSTRUÇÕES PARA O AGENTE:
        Você é o LexFácil, um assistente jurídico especializado em simplificar textos normativos.
        Sua missão é ajudar as pessoas a compreenderem leis e regulamentos de forma clara e acessível.
        
        DIRETRIZES:
        1. Adapte sua linguagem ao perfil do usuário selecionado
        2. Quando mencionar artigos ou seções, explique seu significado prático
        3. Use exemplos relevantes ao perfil do usuário
        4. Se um termo jurídico for necessário, explique conforme o nível do usuário
        5. Seja objetivo mas amigável
        6. Foque sempre no documento carregado pelo usuário
        7. Se não souber algo específico do documento, seja honesto
        8. Sugira funcionalidades úteis (casos práticos, análise de prazos, etc.)
        
        Responda sempre baseado no documento carregado acima.
        """
        return contexto
    return ""

def processar_pergunta_chat(pergunta):
    """Processa uma pergunta no chat considerando o contexto da lei"""
    # Track da pergunta
    st.session_state.metrics_tracker.track_question()
    
    contexto_base = criar_contexto_inicial()
    
    # Histórico das últimas 3 mensagens para contexto
    historico_recente = ""
    if len(st.session_state.chat_messages) > 0:
        ultimas_msgs = st.session_state.chat_messages[-6:]
        for msg in ultimas_msgs:
            papel = "USUÁRIO" if msg["role"] == "user" else "ASSISTENTE"
            historico_recente += f"{papel}: {msg['content']}\n"
    
    prompt = f"""
    {contexto_base}
    
    HISTÓRICO DA CONVERSA:
    {historico_recente}
    
    PERGUNTA ATUAL DO USUÁRIO:
    {pergunta}
    
    Responda de forma clara, prática e acessível, sempre baseado no documento jurídico carregado.
    """
    
    return call_gemini_api(prompt, "resposta do chat")

# Outras funções de análise (analisar_legibilidade_gemini, gerar_resumo_gemini, etc.)
# [Manter as funções originais aqui - não vou replicar todas para economizar espaço]

def analisar_legibilidade_gemini(texto):
    prompt = f"""
    Analise a legibilidade deste texto jurídico (em português) considerando os seguintes critérios.
    Para cada critério, forneça uma avaliação e, se aplicável, sugestões de melhoria.

    1.  **Complexidade Linguística Geral:**
        *   Avaliação (escala de 1-Fácil a 10-Muito Difícil):
        *   Justificativa:
    2.  **Densidade Conceitual:**
        *   Avaliação (Baixa, Média, Alta):
        *   Exemplos de conceitos densos (se houver):
    3.  **Uso de Termos Técnicos (Jargão Jurídico):**
        *   Avaliação (Moderado, Frequente, Excessivo):
        *   Exemplos de termos técnicos chave:
        *   Sugestões para simplificar ou explicar termos:
    4.  **Estrutura das Frases:**
        *   Avaliação (Comprimento médio, Clareza, Uso de voz passiva/ativa):
        *   Exemplos de frases complexas (se houver):
        *   Sugestões para melhorar a clareza das frases:
    5.  **Coerência e Coesão:**
        *   Avaliação (Como as ideias se conectam, clareza do fluxo lógico):
    6.  **Público-Alvo Ideal:**
        *   Para quem este texto é mais adequado em sua forma atual?
    7.  **Recomendações Gerais para Simplificação:**
        *   Liste 3-5 ações concretas para tornar o texto mais acessível a um público leigo.

    Formato de Resposta: Utilize estritamente MARKDOWN, com títulos (usando ## ou ###) e bullet points (usando * ou -).

    Texto para Análise:
    ---
    {texto[:18000]}
    ---
    """
    return call_gemini_api(prompt, "Análise de Legibilidade")

def gerar_resumo_gemini(texto):
    """Gera um resumo simplificado da lei"""
    prompt = f"""
    Você é um assistente especializado em simplificar textos jurídicos para o público leigo.
    Sua tarefa é gerar um resumo conciso e em linguagem acessível do texto jurídico fornecido.
    O resumo deve:
    1.  Identificar e explicar os pontos principais do texto de forma clara.
    2.  Mencionar artigos, parágrafos ou seções relevantes, explicando seu significado prático.
    3.  Descrever os efeitos práticos ou as consequências do que está estabelecido no texto.
    4.  Evitar jargões jurídicos sempre que possível. Se um termo técnico for essencial, explique-o brevemente.
    5.  Ser estruturado de forma lógica e fácil de seguir.
    6.  Utilizar formato MARKDOWN para melhor legibilidade (títulos, bullet points, negrito).

    Texto Jurídico para Resumir:
    ---
    {texto[:18000]}
    ---

    Resumo Acessível:
    """
    return call_gemini_api(prompt, "Geração de Resumo")

def gerar_casos_praticos(texto):
    """Gera casos práticos baseados na lei"""
    prompt = f"""
    Com base neste texto jurídico, crie 3 casos práticos/exemplos reais de como esta lei se aplica no dia a dia.
    
    Para cada caso, forneça:
    1. **Situação**: Descreva um cenário específico e realista
    2. **Aplicação da Lei**: Como a lei se aplica neste caso
    3. **Consequências**: O que acontece na prática
    4. **Dica Prática**: Uma orientação útil
    
    Casos devem ser:
    - Realistas e específicos
    - Fáceis de entender
    - Relevantes para diferentes perfis de pessoas
    - Escritos em linguagem simples
    
    Use formato MARKDOWN com títulos e seções claras.
    
    Texto da Lei:
    ---
    {texto[:15000]}
    ---
    """
    return call_gemini_api(prompt, "Geração de Casos Práticos")

def extrair_prazos_importantes(texto):
    """Extrai prazos e datas importantes da lei"""
    prompt = f"""
    Analise este texto jurídico e identifique TODOS os prazos, datas e períodos importantes mencionados.
    
    Para cada prazo encontrado, forneça:
    1. **Prazo**: O período específico (dias, meses, anos)
    2. **Para que serve**: O que deve ser feito neste prazo
    3. **Quem deve cumprir**: Responsável pela ação
    4. **Consequência**: O que acontece se não cumprir
    5. **Artigo/Seção**: Onde está previsto no texto
    
    Organize em ordem de importância/urgência.
    Use formato MARKDOWN com emojis para facilitar visualização.
    
    Se não encontrar prazos específicos, informe que a lei não estabelece prazos determinados.
    
    Texto da Lei:
    ---
    {texto[:15000]}
    ---
    """
    return call_gemini_api(prompt, "Extração de Prazos")

def busca_semantica(texto, consulta):
    """Realiza busca semântica no texto da lei"""
    prompt = f"""
    O usuário quer encontrar informações sobre: "{consulta}"
    
    Procure no texto jurídico abaixo todas as informações relacionadas a esta consulta.
    Considere sinônimos, conceitos relacionados e contexto.
    
    Retorne:
    1. **Trechos Relevantes**: Cite os artigos/parágrafos específicos
    2. **Explicação Simplificada**: O que significa na prática
    3. **Palavras-chave Encontradas**: Termos relacionados identificados
    
    Se não encontrar nenhuma informação relacionada, informe claramente.
    
    Consulta do usuário: {consulta}
    
    Texto da Lei:
    ---
    {texto[:15000]}
    ---
    """
    return call_gemini_api(prompt, "Busca Semântica")

# === INTERFACE MODERNIZADA ===

# Header com título gradiente
st.markdown("""
<div class="gradient-title">
    ⚖️ LexFácil
</div>
<div style="text-align: center; color: #94a3b8; font-size: 1.2rem; margin-bottom: 2rem;">
    Seu Assistente Jurídico Inteligente • Powered by AI
</div>
""", unsafe_allow_html=True)

# Sidebar moderna
with st.sidebar:
    st.markdown("""
    <div style="text-align: center; margin-bottom: 2rem;">
        <div style="font-size: 2rem; margin-bottom: 0.5rem;">🤖</div>
        <div style="font-size: 1.25rem; font-weight: 600; color: white;">LexFácil AI</div>
        <div style="color: #94a3b8; font-size: 0.875rem;">Legal Assistant v2.0</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Dashboard de métricas (para admins ou demo)
    with st.expander("📊 Analytics Dashboard", expanded=False):
        dashboard_data = st.session_state.metrics_tracker.get_dashboard_data()
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{dashboard_data['summary']['total_sessions']}</div>
                <div class="metric-label">Sessões</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{dashboard_data['summary']['total_questions']}</div>
                <div class="metric-label">Perguntas</div>
            </div>
            """, unsafe_allow_html=True)
        
        # Gráfico de uso dos últimos 7 dias
        if dashboard_data['last_7_days']:
            df_stats = pd.DataFrame(dashboard_data['last_7_days'])
            fig = px.line(df_stats, x='date', y=['sessions', 'questions'], 
                         title="Atividade dos Últimos 7 Dias",
                         color_discrete_map={'sessions': '#667eea', 'questions': '#764ba2'})
            fig.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font_color='white',
                height=300
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Top personas
        persona_data = dashboard_data['summary']['persona_usage']
        if sum(persona_data.values()) > 0:
            fig_pie = px.pie(values=list(persona_data.values()), 
                            names=list(persona_data.keys()),
                            title="Distribuição de Personas")
            fig_pie.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font_color='white',
                height=300
            )
            st.plotly_chart(fig_pie, use_container_width=True)
    
    st.markdown("---")
    
    # Seletor de Persona com design
