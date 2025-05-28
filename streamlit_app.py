import streamlit as st
import tempfile
import os
import PyPDF2
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
import time
from datetime import datetime
import json

# Configuração da página - DEVE ser a primeira linha do Streamlit
st.set_page_config(
    page_title="LexFácil", 
    layout="wide", 
    initial_sidebar_state="collapsed",
    page_icon="⚖️"
)

# CSS personalizado para interface moderna
st.markdown("""
<style>
    /* Reset e variáveis */
    :root {
        --primary-color: #2E86AB;
        --secondary-color: #A23B72;
        --accent-color: #F18F01;
        --success-color: #06D6A0;
        --warning-color: #F18F01;
        --error-color: #F71735;
        --text-color: #2D3436;
        --bg-gradient: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        --card-shadow: 0 8px 32px rgba(31, 38, 135, 0.37);
        --glass-bg: rgba(255, 255, 255, 0.25);
        --border-radius: 16px;
    }
    
    /* Layout principal */
    .main-container {
        background: var(--bg-gradient);
        min-height: 100vh;
        padding: 0;
        margin: 0;
    }
    
    /* Header moderno */
    .modern-header {
        background: rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
        padding: 1.5rem 2rem;
        border-radius: 0 0 24px 24px;
        margin-bottom: 2rem;
        box-shadow: var(--card-shadow);
    }
    
    .header-title {
        font-size: 2.5rem;
        font-weight: 700;
        background: linear-gradient(45deg, #667eea, #764ba2);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin: 0;
    }
    
    .header-subtitle {
        text-align: center;
        color: rgba(255, 255, 255, 0.8);
        font-size: 1.1rem;
        margin-top: 0.5rem;
    }
    
    /* Cards modernos */
    .glass-card {
        background: var(--glass-bg);
        backdrop-filter: blur(16px);
        border-radius: var(--border-radius);
        padding: 2rem;
        box-shadow: var(--card-shadow);
        border: 1px solid rgba(255, 255, 255, 0.18);
        margin-bottom: 1.5rem;
    }
    
    /* Chat interface */
    .chat-container {
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(10px);
        border-radius: var(--border-radius);
        padding: 1.5rem;
        margin-bottom: 2rem;
        box-shadow: var(--card-shadow);
        max-height: 600px;
        overflow-y: auto;
    }
    
    /* Personas modernas */
    .persona-selector {
        display: flex;
        gap: 1rem;
        flex-wrap: wrap;
        margin-bottom: 1.5rem;
    }
    
    .persona-card {
        background: rgba(255, 255, 255, 0.2);
        border: 2px solid transparent;
        border-radius: 12px;
        padding: 1rem;
        cursor: pointer;
        transition: all 0.3s ease;
        flex: 1;
        min-width: 200px;
        text-align: center;
    }
    
    .persona-card:hover {
        background: rgba(255, 255, 255, 0.3);
        transform: translateY(-2px);
    }
    
    .persona-card.active {
        border-color: var(--accent-color);
        background: rgba(241, 143, 1, 0.2);
    }
    
    .persona-icon {
        font-size: 2rem;
        margin-bottom: 0.5rem;
    }
    
    .persona-title {
        font-weight: 600;
        color: white;
        margin-bottom: 0.25rem;
    }
    
    .persona-desc {
        font-size: 0.9rem;
        color: rgba(255, 255, 255, 0.8);
    }
    
    /* Upload area moderna */
    .upload-zone {
        border: 2px dashed rgba(255, 255, 255, 0.5);
        border-radius: var(--border-radius);
        padding: 3rem;
        text-align: center;
        background: rgba(255, 255, 255, 0.1);
        transition: all 0.3s ease;
        margin-bottom: 2rem;
    }
    
    .upload-zone:hover {
        border-color: var(--accent-color);
        background: rgba(255, 255, 255, 0.15);
    }
    
    /* Botões de ação rápida */
    .quick-actions {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 1rem;
        margin-bottom: 2rem;
    }
    
    .action-button {
        background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
        color: white;
        border: none;
        padding: 1rem 1.5rem;
        border-radius: 12px;
        cursor: pointer;
        transition: all 0.3s ease;
        font-weight: 600;
        text-align: center;
    }
    
    .action-button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(46, 134, 171, 0.4);
    }
    
    /* Sugestões de perguntas */
    .suggestions-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
        gap: 1rem;
        margin-top: 1rem;
    }
    
    .suggestion-chip {
        background: rgba(255, 255, 255, 0.2);
        border: 1px solid rgba(255, 255, 255, 0.3);
        border-radius: 25px;
        padding: 0.75rem 1.5rem;
        cursor: pointer;
        transition: all 0.3s ease;
        text-align: center;
        color: white;
        font-weight: 500;
    }
    
    .suggestion-chip:hover {
        background: var(--accent-color);
        transform: translateY(-1px);
        box-shadow: 0 4px 15px rgba(241, 143, 1, 0.4);
    }
    
    /* Status indicator */
    .status-indicator {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        background: var(--success-color);
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-size: 0.9rem;
        font-weight: 600;
    }
    
    /* Loading spinner moderno */
    .modern-spinner {
        border: 3px solid rgba(255, 255, 255, 0.3);
        border-top: 3px solid var(--accent-color);
        border-radius: 50%;
        width: 40px;
        height: 40px;
        animation: spin 1s linear infinite;
        margin: 0 auto;
    }
    
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    
    /* Chat messages styling */
    .chat-message {
        margin-bottom: 1rem;
        padding: 1rem;
        border-radius: 12px;
        max-width: 80%;
    }
    
    .user-message {
        background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
        color: white;
        margin-left: auto;
        text-align: right;
    }
    
    .assistant-message {
        background: rgba(255, 255, 255, 0.9);
        color: var(--text-color);
        margin-right: auto;
    }
    
    /* Responsivo */
    @media (max-width: 768px) {
        .persona-selector {
            flex-direction: column;
        }
        
        .quick-actions {
            grid-template-columns: 1fr;
        }
        
        .suggestions-grid {
            grid-template-columns: 1fr;
        }
    }
    
    /* Animações */
    .fade-in {
        animation: fadeIn 0.5s ease-in;
    }
    
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    /* Esconder elementos padrão do Streamlit */
    .stDeployButton { display: none; }
    .stDecoration { display: none; }
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# Configuração da API
GOOGLE_API_KEY = "AIzaSyAi-EZdS0Jners99DuB_5DkROiK16ghPnM"  # Replace with your actual API key

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

# Inicialização do session state
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

# --- Helper Functions ---
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
    contexto_base = criar_contexto_inicial()
    
    # Histórico das últimas 3 mensagens para contexto
    historico_recente = ""
    if len(st.session_state.chat_messages) > 0:
        ultimas_msgs = st.session_state.chat_messages[-6:]  # Últimas 3 trocas (user + assistant)
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

# --- Interface Principal ---

# Header moderno
st.markdown("""
<div class="main-container">
    <div class="modern-header fade-in">
        <h1 class="header-title">⚖️ LexFácil</h1>
        <p class="header-subtitle">Seu assistente jurídico inteligente que transforma juridiquês em linguagem humana</p>
    </div>
</div>
""", unsafe_allow_html=True)

# Container principal
with st.container():
    # Seletor de Persona moderno
    st.markdown("""
    <div class="glass-card fade-in">
        <h3 style="color: white; margin-bottom: 1rem;">👤 Como posso te ajudar hoje?</h3>
        <div class="persona-selector">
    """, unsafe_allow_html=True)
    
    personas = {
        "👨‍👩‍👧‍👦 Cidadão": {
            "icon": "👨‍👩‍👧‍👦",
            "title": "Cidadão",
            "desc": "Linguagem simples e exemplos do dia a dia"
        },
        "👨‍💼 Empresário": {
            "icon": "👨‍💼", 
            "title": "Empresário",
            "desc": "Foco em impactos comerciais e negócios"
        },
        "👩‍⚖️ Advogado": {
            "icon": "👩‍⚖️",
            "title": "Advogado", 
            "desc": "Análise técnica e jurídica detalhada"
        },
        "🏛️ Servidor Público": {
            "icon": "🏛️",
            "title": "Servidor Público",
            "desc": "Aplicação prática da norma"
        }
    }
    
    # Criar colunas para personas
    cols = st.columns(4)
    for i, (key, persona) in enumerate(personas.items()):
        with cols[i]:
            active_class = "active" if key == st.session_state.persona_usuario else ""
            if st.button(
                f"{persona['icon']}\n{persona['title']}\n{persona['desc']}", 
                key=f"persona_{i}",
                use_container_width=True
            ):
                if key != st.session_state.persona_usuario:
                    st.session_state.persona_usuario = key
                    st.success(f"✅ Perfil alterado para {persona['title']}")
                    time.sleep(1)
                    st.rerun()
    
    st.markdown("</div></div>", unsafe_allow_html=True)
    
    # Upload de arquivo com interface moderna
    if not st.session_state.texto_lei:
        st.markdown("""
        <div class="glass-card fade-in">
            <div class="upload-zone">
                <h2 style="color: white; margin-bottom: 1rem;">📄 Carregue seu documento jurídico</h2>
                <p style="color: rgba(255,255,255,0.8); margin-bottom: 2rem;">
                    Arraste e solte ou clique para selecionar um arquivo PDF
                </p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        uploaded_file = st.file_uploader(
            "Escolher arquivo PDF", 
            type=["pdf"],
            label_visibility="collapsed"
        )
        
        if uploaded_file:
            if uploaded_file.name != st.session_state.nome_documento:
                # Novo arquivo carregado
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                    tmp_file.write(uploaded_file.getvalue())
                    tmp_file_path = tmp_file.name

                with st.spinner("🔄 Processando documento..."):
                    texto_extraido = extrair_texto_pdf(tmp_file_path)
                    os.unlink(tmp_file_path)
                    
                    if texto_extraido:
                        st.session_state.texto_lei = texto_extraido
                        st.session_state.nome_documento = uploaded_file.name
                        st.session_state.chat_messages = []  # Limpa chat anterior
                        st.session_state.analise_realizada = False
                        st.session_state.resumo_realizado = False
                        
                        st.success("✅ Documento carregado com sucesso!")
                        
                        # Mensagem de boas-vindas automática
                        boas_vindas = f"""Perfeito! Acabei de processar o documento **{uploaded_file.name}**. 🎉

Agora posso ajudar você a entender este texto jurídico de forma simples e clara. 

**O que você gostaria de fazer primeiro?**

💡 **Dica**: Use os botões de ação rápida abaixo ou me faça perguntas específicas sobre a lei!"""
                        
                        st.session_state.chat_messages.append({
                            "role": "assistant",
                            "content": boas_vindas,
                            "timestamp": datetime.now()
                        })
                        st.rerun()
                    else:
                        st.error("❌ Não foi possível extrair texto do PDF")
    
    # Interface principal quando documento está carregado
    if st.session_state.texto_lei:
        # Status do documento
        st.markdown(f"""
        <div class="glass-card fade-in">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <h3 style="color: white; margin: 0;">📋 {st.session_state.nome_documento}</h3>
                    <p style="color: rgba(255,255,255,0.8); margin: 0.5rem 0 0 0;">
                        {len(st.session_state.texto_lei):,} caracteres • Modo: {st.session_state.persona_usuario}
                    </p>
                </div>
                <div class="status-indicator">
                    ✅ Ativo
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Ações rápidas
        st.markdown("""
        <div class="glass-card fade-in">
            <h3 style="color: white; margin-bottom: 1.5rem;">🚀 Ações Rápidas</h3>
            <div class="quick-actions">
        """, unsafe_allow_html=True)
        
        col1, col2, col3, col4 = st.columns(
