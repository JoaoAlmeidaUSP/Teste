import streamlit as st
import tempfile
import os
import PyPDF2
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
import time
from datetime import datetime

# Configuração da página
st.set_page_config(
    page_title="LexFácil", 
    layout="wide", 
    initial_sidebar_state="collapsed",
    page_icon="⚖️"
)

# CSS personalizado para um layout moderno
st.markdown("""
<style>
    /* Configurações gerais */
    .main {
        padding-top: 1rem;
    }
    
    /* Header personalizado */
    .header-container {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem 1rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        text-align: center;
        color: white;
        box-shadow: 0 10px 30px rgba(0,0,0,0.1);
    }
    
    .header-title {
        font-size: 3rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }
    
    .header-subtitle {
        font-size: 1.2rem;
        opacity: 0.9;
        margin-bottom: 0;
    }
    
    /* Cards de status */
    .status-card {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        border-left: 4px solid #667eea;
        box-shadow: 0 4px 15px rgba(0,0,0,0.08);
        margin-bottom: 1rem;
    }
    
    .document-info {
        background: linear-gradient(135deg, #f8f9ff 0%, #e8f4f8 100%);
        padding: 1.5rem;
        border-radius: 12px;
        border: 1px solid #e1e8ed;
        margin-bottom: 1.5rem;
    }
    
    /* Persona selector */
    .persona-container {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.08);
        margin-bottom: 1.5rem;
    }
    
    /* Quick actions */
    .quick-actions {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 1rem;
        margin-bottom: 2rem;
    }
    
    .action-card {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        text-align: center;
        box-shadow: 0 4px 15px rgba(0,0,0,0.08);
        transition: transform 0.2s, box-shadow 0.2s;
        cursor: pointer;
        border: 1px solid #f0f2f6;
    }
    
    .action-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(0,0,0,0.12);
    }
    
    /* Chat container */
    .chat-container {
        background: white;
        border-radius: 15px;
        padding: 0;
        box-shadow: 0 4px 20px rgba(0,0,0,0.08);
        border: 1px solid #e8eaed;
        min-height: 500px;
        margin-bottom: 2rem;
    }
    
    .chat-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem 1.5rem;
        border-radius: 15px 15px 0 0;
        font-weight: 600;
    }
    
    /* Sugestões */
    .suggestions-container {
        background: #f8f9ff;
        padding: 1.5rem;
        border-radius: 12px;
        border: 1px solid #e1e8ed;
        margin-bottom: 1.5rem;
    }
    
    /* Botões melhorados */
    .stButton > button {
        width: 100%;
        border-radius: 8px;
        border: none;
        padding: 0.75rem 1.5rem;
        font-weight: 500;
        transition: all 0.2s;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
    }
    
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
    }
    
    /* Upload area */
    .upload-container {
        background: white;
        padding: 2rem;
        border-radius: 12px;
        border: 2px dashed #667eea;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    /* Responsivo */
    @media (max-width: 768px) {
        .header-title {
            font-size: 2rem;
        }
        .quick-actions {
            grid-template-columns: 1fr;
        }
    }
    
    /* Ocultar elementos padrão do Streamlit */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display:none;}
</style>
""", unsafe_allow_html=True)

# Configuração da API
GOOGLE_API_KEY = "AIzaSyAi-EZdS0Jners99DuB_5DkROiK16ghPnM"  # Substitua por sua chave API real

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

def dividir_texto_em_chunks(texto, max_chars=100000):
    """Divide texto em chunks menores se necessário, preservando parágrafos"""
    if len(texto) <= max_chars:
        return [texto]
    
    chunks = []
    paragrafos = texto.split('\n\n')
    chunk_atual = ""
    
    for paragrafo in paragrafos:
        if len(chunk_atual + paragrafo) <= max_chars:
            chunk_atual += paragrafo + '\n\n'
        else:
            if chunk_atual:
                chunks.append(chunk_atual.strip())
                chunk_atual = paragrafo + '\n\n'
            else:
                # Se um parágrafo for muito grande, divide por frases
                frases = paragrafo.split('. ')
                for frase in frases:
                    if len(chunk_atual + frase) <= max_chars:
                        chunk_atual += frase + '. '
                    else:
                        if chunk_atual:
                            chunks.append(chunk_atual.strip())
                            chunk_atual = frase + '. '
                        else:
                            # Se uma frase for muito grande, força a divisão
                            chunks.append(frase[:max_chars])
                            chunk_atual = frase[max_chars:] + '. '
    
    if chunk_atual:
        chunks.append(chunk_atual.strip())
    
    return chunks

def processar_texto_grande(texto, prompt_template, task_name="tarefa"):
    """Processa textos grandes dividindo em chunks e combinando resultados"""
    chunks = dividir_texto_em_chunks(texto)
    
    if len(chunks) == 1:
        # Texto pequeno, processa normalmente
        prompt = prompt_template.replace("{texto}", chunks[0])
        return call_gemini_api(prompt, task_name)
    
    # Texto grande, processa em partes
    resultados = []
    for i, chunk in enumerate(chunks):
        st.write(f"Processando parte {i+1} de {len(chunks)}...")
        prompt = prompt_template.replace("{texto}", chunk)
        resultado = call_gemini_api(prompt, f"{task_name} - Parte {i+1}")
        resultados.append(resultado)
    
    # Combina os resultados
    if task_name.lower().startswith("análise"):
        # Para análises, cria um resumo consolidado
        prompt_consolidacao = f"""
        Consolide estas análises parciais de um documento jurídico em uma análise única e coerente:
        
        {chr(10).join([f"## Parte {i+1}:{chr(10)}{resultado}{chr(10)}" for i, resultado in enumerate(resultados)])}
        
        Forneça uma análise consolidada considerando todo o documento.
        """
        return call_gemini_api(prompt_consolidacao, "Consolidação de Análise")
    
    elif task_name.lower().startswith("resumo"):
        # Para resumos, consolida os pontos principais
        prompt_consolidacao = f"""
        Consolide estes resumos parciais de um documento jurídico em um resumo único e coerente:
        
        {chr(10).join([f"## Parte {i+1}:{chr(10)}{resultado}{chr(10)}" for i, resultado in enumerate(resultados)])}
        
        Forneça um resumo consolidado considerando todo o documento, eliminando redundâncias.
        """
        return call_gemini_api(prompt_consolidacao, "Consolidação de Resumo")
    
    else:
        # Para outros casos, simplesmente concatena
        return "\n\n---\n\n".join(resultados)

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
        
        # Para documentos muito grandes, usa apenas os primeiros 50.000 caracteres para o contexto
        texto_contexto = st.session_state.texto_lei[:50000] if len(st.session_state.texto_lei) > 50000 else st.session_state.texto_lei
        
        contexto = f"""
        DOCUMENTO JURÍDICO CARREGADO: {st.session_state.nome_documento}
        TAMANHO DO DOCUMENTO: {len(st.session_state.texto_lei):,} caracteres
        
        TEXTO DA LEI/NORMA (INÍCIO):
        {texto_contexto}
        
        PERFIL DO USUÁRIO: {st.session_state.persona_usuario}
        INSTRUÇÕES ESPECÍFICAS: {contexto_persona}
        
        INSTRUÇÕES PARA O AGENTE:
        Você é o LexFácil, um assistente jurídico especializado em simplificar textos normativos.
        Sua missão é ajudar as pessoas a compreenderem leis e regulamentos de forma clara e acessível.
        
        IMPORTANTE: O documento completo tem {len(st.session_state.texto_lei):,} caracteres. Para perguntas sobre partes específicas do documento que não aparecem no contexto acima, informe que pode analisar seções específicas se o usuário indicar artigos, capítulos ou temas específicos.
        
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
    prompt_template = """
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
    {texto}
    ---
    """
    return processar_texto_grande(texto, prompt_template, "Análise de Legibilidade")

def gerar_resumo_gemini(texto):
    """Gera um resumo simplificado da lei"""
    prompt_template = """
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
    {texto}
    ---

    Resumo Acessível:
    """
    return processar_texto_grande(texto, prompt_template, "Resumo Simplificado")

def gerar_casos_praticos(texto):
    """Gera casos práticos baseados na lei"""
    # Para casos práticos, usa apenas uma amostra do texto para não sobrecarregar
    texto_amostra = texto[:30000] if len(texto) > 30000 else texto
    
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
    {texto_amostra}
    ---
    """
    return call_gemini_api(prompt, "Geração de Casos Práticos")

def extrair_prazos_importantes(texto):
    """Extrai prazos e datas importantes da lei"""
    prompt_template = """
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
    {texto}
    ---
    """
    return processar_texto_grande(texto, prompt_template, "Extração de Prazos")

def busca_semantica(texto, consulta):
    """Realiza busca semântica no texto da lei"""
    # Para busca, pode processar o texto todo se necessário
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
    {texto[:50000]}
    ---
    """
    return call_gemini_api(prompt, "Busca Semântica")

# --- INTERFACE PRINCIPAL ---
# Header moderno
st.markdown("""
<div class="header-container">
    <h1 class="header-title">⚖️ LexFácil</h1>
    <p class="header-subtitle">Seu assistente jurídico inteligente • Transformando juridiquês em linguagem acessível</p>
</div>
""", unsafe_allow_html=True)

# Layout principal em duas colunas
col_main, col_sidebar = st.columns([2, 1])

with col_sidebar:
    # Seletor de Persona
    st.markdown("""
    <div class="persona-container">
        <h3>👤 Seu Perfil</h3>
    </div>
    """, unsafe_allow_html=True)
    
    personas = {
        "👨‍👩‍👧‍👦 Cidadão": "Linguagem simples e exemplos do dia a dia",
        "👨‍💼 Empresário": "Foco em impactos comerciais e negócios", 
        "👩‍⚖️ Advogado": "Análise técnica e jurídica detalhada",
        "🏛️ Servidor Público": "Aplicação prática da norma"
    }
    
    persona_escolhida = st.selectbox(
        "Como você quer que eu te ajude?",
        options=list(personas.keys()),
        index=list(personas.keys()).index(st.session_state.persona_usuario),
        help="Escolha seu perfil para respostas personalizadas"
    )
    
    if persona_escolhida != st.session_state.persona_usuario:
        st.session_state.persona_usuario = persona_escolhida
        st.success(f"✅ Perfil alterado para {persona_escolhida}")
        time.sleep(1)
        st.rerun()
    
    st.info(personas[st.session_state.persona_usuario])
    
    # Upload de arquivo
    st.markdown("### 📄 Carregar Documento")
    uploaded_file = st.file_uploader("", type=["pdf"], help="Arraste e solte seu PDF aqui")
    
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
                    st.success("✅ Documento carregado!")
                    
                    # Mensagem de boas-vindas automática
                    boas_vindas = f"""👋 **Documento carregado com sucesso!**

📁 **{uploaded_file.name}**
📊 {len(texto_extraido):,} caracteres processados

Agora posso ajudar você a entender este texto jurídico de forma simples e clara! 

**🚀 Como posso ajudar?**
- Faça perguntas sobre qualquer parte da lei
- Solicite análises e resumos simplificados  
- Peça casos práticos e exemplos reais
- Busque por temas específicos

**💡 Dica:** Use as ações rápidas ao lado ou converse comigo naturalmente!"""
                    
                    st.session_state.chat_messages.append({
                        "role": "assistant",
                        "content": boas_vindas,
                        "timestamp": datetime.now()
                    })
                    st.rerun()
                else:
                    st.error("❌ Não foi possível extrair texto do PDF")
    
    # Info do documento carregado
    if st.session_state.texto_lei:
        st.markdown(f"""
        <div class="document-info">
            <h4>📋 Documento Atual</h4>
            <p><strong>{st.session_state.nome_documento}</strong></p>
            <p>📊 {len(st.session_state.texto_lei):,} caracteres</p>
            <p>👤 <strong>Modo:</strong> {st.session_state.persona_usuario}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Busca semântica
        st.markdown("### 🔍 Busca Inteligente")
        busca_query = st.text_input("", placeholder="Ex: multas, prazos, obrigações...", key="busca_input")
        if st.button("🔍 Buscar", use_container_width=True) and busca_query:
            with st.spinner("Buscando..."):
                resultado_busca = busca_semantica(st.session_state.texto_lei, busca_query)
                st.session_state.chat_messages.append({
                    "role": "user",
                    "content": f"Buscar por: {busca_query}",
                    "timestamp": datetime.now()
                })
                st.session_state.chat_messages.append({
                    "role": "assistant",
                    "content": f"## 🔍 Resultados da Busca: '{busca_query}'\n\n{resultado_busca}",
                    "timestamp": datetime.now()
                })
                st.rerun()

with col_main:
    if not st.session_state.texto_lei:
        st.markdown("""
        <div class="welcome-container">
            <div class="welcome-hero">
                <h2>🤖 Assistente Jurídico Inteligente</h2>
                <p>Carregue um documento PDF para começar nossa conversa</p>
            </div>
            
            <div class="features-grid">
                <div class="feature-card">
                    <div class="feature-icon">📖</div>
                    <h4>Análise Inteligente</h4>
                    <p>Analiso complexidade e estrutura do texto jurídico</p>
                </div>
                <div class="feature-card">
                    <div class="feature-icon">💡</div>
                    <h4>Linguagem Simples</h4>
                    <p>Traduzo juridiquês para linguagem do dia a dia</p>
                </div>
                <div class="feature-card">
                    <div class="feature-icon">🎯</div>
                    <h4>Casos Práticos</h4>
                    <p>Mostro como a lei funciona em situações reais</p>
                </div>
                <div class="feature-card">
                    <div class="feature-icon">⏰</div>
                    <h4>Prazos Importantes</h4>
                    <p>Identifico datas e prazos que você não pode perder</p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # CSS adicional para o estado inicial
        st.markdown("""
        <style>
        .welcome-container {
            text-align: center;
            padding: 3rem 1rem;
        }
        
        .welcome-hero {
            margin-bottom: 3rem;
        }
        
        .welcome-hero h2 {
            color: #667eea;
            font-size: 2.5rem;
            margin-bottom: 1rem;
        }
        
        .welcome-hero p {
            font-size: 1.2rem;
            color: #666;
            margin-bottom: 0;
        }
        
        .features-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 1.5rem;
            margin-top: 2rem;
        }
        
        .feature-card {
            background: white;
            padding: 2rem;
            border-radius: 16px;
            box-shadow: 0 4px 20px rgba(102, 126, 234, 0.1);
            border: 1px solid #f0f2f6;
            transition: transform 0.3s ease;
        }
        
        .feature-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 8px 30px rgba(102, 126, 234, 0.15);
        }
        
        .feature-icon {
            font-size: 2.5rem;
            margin-bottom: 1rem;
        }
        
        .feature-card h4 {
            color: #333;
            margin-bottom: 0.5rem;
            font-weight: 600;
        }
        
        .feature-card p {
            color: #666;
            font-size: 0.9rem;
            line-height: 1.4;
        }
        </style>
        """, unsafe_allow_html=True)
        
    else:
        # Layout principal com documento carregado
        # Ações rápidas em cards modernos
        st.markdown("""
        <div class="quick-actions-header">
            <h3>🚀 Ações Rápidas</h3>
            <p>Clique em qualquer opção para começar</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Grid de ações em 4 colunas
        action_col1, action_col2, action_col3, action_col4 = st.columns(4)
        
        with action_col1:
            if st.button("📊 **Análise Completa**", use_container_width=True, help="Análise detalhada de legibilidade"):
                if not st.session_state.analise_realizada:
                    with st.spinner("🔄 Analisando documento..."):
                        analise = analisar_legibilidade_gemini(st.session_state.texto_lei)
                        st.session_state.chat_messages.append({
                            "role": "user",
                            "content": "Fazer análise completa do documento",
                            "timestamp": datetime.now()
                        })
                        st.session_state.chat_messages.append({
                            "role": "assistant", 
                            "content": f"## 📊 Análise Completa de Legibilidade\n\n{analise}",
                            "timestamp": datetime.now()
                        })
                        st.session_state.analise_realizada = True
                        st.rerun()
                else:
                    st.success("✅ Análise já realizada - veja no chat!")
        
        with action_col2:
            if st.button("📝 **Resumo Simplificado**", use_container_width=True, help="Resumo em linguagem simples"):
                if not st.session_state.resumo_realizado:
                    with st.spinner("📝 Criando resumo..."):
                        resumo = gerar_resumo_gemini(st.session_state.texto_lei)
                        st.session_state.chat_messages.append({
                            "role": "user",
                            "content": "Gerar resumo simplificado",
                            "timestamp": datetime.now()
                        })
                        st.session_state.chat_messages.append({
                            "role": "assistant",
                            "content": f"## 📝 Resumo Simplificado\n\n{resumo}",
                            "timestamp": datetime.now()
                        })
                        st.session_state.resumo_realizado = True
                        st.rerun()
                else:
                    st.success("✅ Resumo já criado - veja no chat!")
        
        with action_col3:
            if st.button("🎯 **Casos Práticos**", use_container_width=True, help="Exemplos reais de aplicação"):
                with st.spinner("🎯 Gerando casos práticos..."):
                    casos = gerar_casos_praticos(st.session_state.texto_lei)
                    st.session_state.chat_messages.append({
                        "role": "user",
                        "content": "Mostrar casos práticos",
                        "timestamp": datetime.now()
                    })
                    st.session_state.chat_messages.append({
                        "role": "assistant",
                        "content": f"## 🎯 Casos Práticos\n\n{casos}",
                        "timestamp": datetime.now()
                    })
                    st.rerun()
        
        with action_col4:
            if st.button("⏰ **Prazos Importantes**", use_container_width=True, help="Datas e prazos da lei"):
                with st.spinner("⏰ Extraindo prazos..."):
                    prazos = extrair_prazos_importantes(st.session_state.texto_lei)
                    st.session_state.chat_messages.append({
                        "role": "user",
                        "content": "Extrair prazos importantes",
                        "timestamp": datetime.now()
                    })
                    st.session_state.chat_messages.append({
                        "role": "assistant",
                        "content": f"## ⏰ Prazos Importantes\n\n{prazos}",
                        "timestamp": datetime.now()
                    })
                    st.rerun()

        # Container do chat moderno
        st.markdown("---")
        
        # Chat interface moderna
        st.markdown("""
        <div class="chat-container">
            <div class="chat-header">
                <div class="chat-header-content">
                    <span class="chat-title">💬 Conversa com LexFácil</span>
                    <span class="chat-status">🟢 Online</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Área de mensagens com scroll
        chat_container = st.container()
        with chat_container:
            if st.session_state.chat_messages:
                for i, message in enumerate(st.session_state.chat_messages):
                    if message["role"] == "user":
                        st.markdown(f"""
                        <div class="message-container user-message">
                            <div class="message-avatar user-avatar">👤</div>
                            <div class="message-content user-content">
                                <div class="message-header">
                                    <span class="message-author">Você</span>
                                    <span class="message-time">{message.get('timestamp', datetime.now()).strftime('%H:%M')}</span>
                                </div>
                                <div class="message-text">{message['content']}</div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown(f"""
                        <div class="message-container assistant-message">
                            <div class="message-avatar assistant-avatar">⚖️</div>
                            <div class="message-content assistant-content">
                                <div class="message-header">
                                    <span class="message-author">LexFácil</span>
                                    <span class="message-time">{message.get('timestamp', datetime.now()).strftime('%H:%M')}</span>
                                </div>
                                <div class="message-text-container">
                        """, unsafe_allow_html=True)
                        
                        # Renderizar conteúdo markdown
                        st.markdown(message['content'])
                        
                        st.markdown("</div></div></div>", unsafe_allow_html=True)
            
            else:
                # Sugestões iniciais quando não há mensagens
                st.markdown(f"""
                <div class="suggestions-container">
                    <h4>💡 Sugestões para começar:</h4>
                    <div class="suggestions-grid">
                        <div class="suggestion-item">
                            <strong>🤔 "Explique o que é esta lei"</strong>
                            <p>Peça uma explicação geral do documento</p>
                        </div>
                        <div class="suggestion-item">
                            <strong>📋 "Quais são as principais obrigações?"</strong>
                            <p>Descubra o que você precisa cumprir</p>
                        </div>
                        <div class="suggestion-item">
                            <strong>⚠️ "O que acontece se eu não cumprir?"</strong>
                            <p>Entenda as consequências e multas</p>
                        </div>
                        <div class="suggestion-item">
                            <strong>📅 "Existem prazos importantes?"</strong>
                            <p>Identifique datas que não pode perder</p>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        
        # Input de chat moderno na parte inferior
        st.markdown("---")
        
        chat_col1, chat_col2 = st.columns([5, 1])
        
        with chat_col1:
            user_question = st.text_input(
                "",
                placeholder=f"💬 Faça sua pergunta sobre {st.session_state.nome_documento}...",
                key="chat_input",
                label_visibility="collapsed"
            )
        
        with chat_col2:
            send_button = st.button("🚀 Enviar", use_container_width=True, type="primary")
        
        # Processa pergunta quando enviada
        if (send_button or user_question) and user_question:
            # Adiciona pergunta do usuário
            st.session_state.chat_messages.append({
                "role": "user",
                "content": user_question,
                "timestamp": datetime.now()
            })
            
            # Processa resposta
            with st.spinner("🤔 Analisando sua pergunta..."):
                resposta = processar_pergunta_chat(user_question)
                st.session_state.chat_messages.append({
                    "role": "assistant",
                    "content": resposta,
                    "timestamp": datetime.now()
                })
            
            st.rerun()

# CSS adicional para o chat moderno
st.markdown("""
<style>
/* Quick Actions Header */
.quick-actions-header {
    text-align: center;
    margin-bottom: 1.5rem;
}

.quick-actions-header h3 {
    color: #333;
    margin-bottom: 0.5rem;
}

.quick-actions-header p {
    color: #666;
    font-size: 0.9rem;
}

/* Chat Styling Moderno */
.chat-header-content {
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.chat-title {
    font-weight: 600;
    font-size: 1.1rem;
}

.chat-status {
    font-size: 0.8rem;
    opacity: 0.9;
}

/* Mensagens do Chat */
.message-container {
    display: flex;
    margin-bottom: 1.5rem;
    gap: 12px;
    animation: slideIn 0.3s ease-out;
}

@keyframes slideIn {
    from {
        opacity: 0;
        transform: translateY(10px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

.message-avatar {
    width: 40px;
    height: 40px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.2rem;
    flex-shrink: 0;
}

.user-avatar {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
}

.assistant-avatar {
    background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
    color: white;
}

.message-content {
    flex: 1;
    min-width: 0;
}

.message-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0.5rem;
}

.message-author {
    font-weight: 600;
    color: #333;
    font-size: 0.9rem;
}

.message-time {
    color: #999;
    font-size: 0.8rem;
}

.user-content {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 1rem 1.25rem;
    border-radius: 18px 18px 4px 18px;
    box-shadow: 0 2px 10px rgba(102, 126, 234, 0.2);
}

.user-content .message-header .message-author,
.user-content .message-header .message-time {
    color: rgba(255, 255, 255, 0.9);
}

.assistant-content {
    background: white;
    border: 1px solid #e8eaed;
    padding: 1rem 1.25rem;
    border-radius: 18px 18px 18px 4px;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
}

.message-text {
    line-height: 1.5;
    word-wrap: break-word;
}

.message-text-container {
    line-height: 1.6;
}

/* Sugestões */
.suggestions-container {
    background: linear-gradient(135deg, #f8f9ff 0%, #e8f4f8 100%);
    border: 1px solid #e1e8ed;
    border-radius: 16px;
    padding: 1.5rem;
    margin: 1rem 0;
}

.suggestions-container h4 {
    color: #333;
    margin-bottom: 1rem;
    text-align: center;
}

.suggestions-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 1rem;
}

.suggestion-item {
    background: white;
    padding: 1rem;
    border-radius: 12px;
    border: 1px solid #e8eaed;
    transition: all 0.2s ease;
    cursor: pointer;
}

.suggestion-item:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
    border-color: #667eea;
}

.suggestion-item strong {
    color: #667eea;
    display: block;
    margin-bottom: 0.5rem;
}

.suggestion-item p {
    color: #666;
    font-size: 0.85rem;
    margin: 0;
    line-height: 1.4;
}

/* Input de chat */
.stTextInput > div > div > input {
    border-radius: 25px !important;
    border: 2px solid #e8eaed !important;
    padding: 0.75rem 1.25rem !important;
    font-size: 1rem !important;
    transition: all 0.2s ease !important;
}

.stTextInput > div > div > input:focus {
    border-color: #667eea !important;
    box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1) !important;
}

/* Botão de envio */
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
    border: none !important;
    border-radius: 25px !important;
    padding: 0.75rem 1.5rem !important;
    font-weight: 600 !important;
    transition: all 0.2s ease !important;
}

.stButton > button[kind="primary"]:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4) !important;
}

/* Responsividade */
@media (max-width: 768px) {
    .message-container {
        gap: 8px;
    }
    
    .message-avatar {
        width: 32px;
        height: 32px;
        font-size: 1rem;
    }
    
    .suggestions-grid {
        grid-template-columns: 1fr;
    }
    
    .features-grid {
        grid-template-columns: 1fr;
    }
}

/* Loading states */
.stSpinner {
    text-align: center;
}

/* Melhorias na barra lateral */
.stSelectbox > div > div {
    border-radius: 12px !important;
}

.stFileUploader > div {
    border-radius: 12px !important;
    border: 2px dashed #667eea !important;
    background: linear-gradient(135deg, #f8f9ff 0%, #ffffff 100%) !important;
}

/* Scrollbar customizada */
::-webkit-scrollbar {
    width: 6px;
}

::-webkit-scrollbar-track {
    background: #f1f1f1;
    border-radius: 10px;
}

::-webkit-scrollbar-thumb {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border-radius: 10px;
}

::-webkit-scrollbar-thumb:hover {
    background: linear-gradient(135deg, #5a6fd8 0%, #6b4190 100%);
}
</style>
""", unsafe_allow_html=True)

# Footer moderno
st.markdown("---")
st.markdown("""
<div style="text-align: center; padding: 1rem; color: #666; font-size: 0.9rem;">
    <p>⚖️ <strong>LexFácil</strong> - Democratizando o acesso à informação jurídica</p>
    <p>Transformando documentos complexos em conhecimento acessível para todos</p>
</div>
""", unsafe_allow_html=True)
