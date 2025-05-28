import streamlit as st
import tempfile
import os
import PyPDF2
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
import time
from datetime import datetime

# Configuração da API (mantida igual)
# [...] (manter todas as funções de backend iguais)

# --- NOVO DESIGN MINIMALISTA ---
st.set_page_config(
    page_title="LexFácil - Assistente Jurídico",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS Customizado Minimalista
st.markdown("""
<style>
    /* Fonte clean */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&display=swap');
    
    * {
        font-family: 'Inter', sans-serif;
    }
    
    /* Sidebar minimalista */
    [data-testid="stSidebar"] {
        background: white !important;
        border-right: 1px solid #f0f0f0 !important;
    }
    
    /* Títulos clean */
    h1, h2, h3, h4, h5, h6 {
        font-weight: 600 !important;
        color: #333 !important;
    }
    
    /* Botões minimalistas */
    .stButton>button {
        border: 1px solid #e0e0e0 !important;
        background: white !important;
        color: #333 !important;
        border-radius: 8px !important;
        padding: 8px 16px !important;
        transition: all 0.2s !important;
    }
    
    .stButton>button:hover {
        background: #f8f8f8 !important;
        border-color: #d0d0d0 !important;
    }
    
    /* Inputs clean */
    .stTextInput>div>div>input {
        border-radius: 8px !important;
        border: 1px solid #e0e0e0 !important;
    }
    
    /* Mensagens do chat */
    [data-testid="stChatMessage"] {
        padding: 12px 0 !important;
    }
    
    .user-message {
        background: #f8f9fa !important;
        border-radius: 12px 12px 0 12px !important;
    }
    
    .assistant-message {
        background: white !important;
        border-radius: 12px 12px 12px 0 !important;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05) !important;
    }
    
    /* Cards de ferramentas */
    .tool-card {
        background: white;
        border-radius: 8px;
        padding: 16px;
        margin-bottom: 12px;
        border: 1px solid #f0f0f0;
    }
    
    .tool-card h4 {
        margin-top: 0;
        color: #444;
    }
    
    .tool-card p {
        color: #666;
        font-size: 0.9rem;
    }
    
    /* Sugestões clean */
    .suggestion-chip {
        display: inline-block;
        background: #f8f9fa;
        color: #333;
        padding: 8px 12px;
        border-radius: 12px;
        margin: 4px;
        font-size: 0.9rem;
        border: 1px solid #e0e0e0;
        cursor: pointer;
    }
    
    /* Expanders clean */
    .stExpander {
        border: 1px solid #f0f0f0 !important;
        border-radius: 8px !important;
    }
    
    .stExpander label {
        font-weight: 500 !important;
    }
</style>
""", unsafe_allow_html=True)

# Layout Principal
st.title("LexFácil")
st.caption("Seu assistente jurídico inteligente")

# Sidebar Minimalista
with st.sidebar:
    st.markdown("""
    <div style="margin-bottom: 2rem;">
        <h3 style="margin-bottom: 0;">LexFácil</h3>
        <p style="color: #666; margin-top: 0;">Simplificando leis complexas</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Seção de Perfil
    with st.expander("**Seu Perfil**", expanded=True):
        personas = {
            "👨‍👩‍👧‍👦 Cidadão": "Linguagem simples",
            "👨‍💼 Empresário": "Foco em negócios", 
            "👩‍⚖️ Advogado": "Análise técnica",
            "🏛️ Servidor": "Aplicação prática"
        }
        
        persona_escolhida = st.radio(
            "Selecione:",
            options=list(personas.keys()),
            index=list(personas.keys()).index(st.session_state.persona_usuario),
            label_visibility="collapsed"
        )
        
        if persona_escolhida != st.session_state.persona_usuario:
            st.session_state.persona_usuario = persona_escolhida
            st.rerun()
    
    st.markdown("---")
    
    # Seção de Documento
    with st.expander("**Documento Atual**", expanded=True):
        uploaded_file = st.file_uploader(
            "Carregar PDF",
            type=["pdf"],
            label_visibility="collapsed"
        )
        
        if uploaded_file:
            if uploaded_file.name != st.session_state.nome_documento:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                    tmp_file.write(uploaded_file.getvalue())
                    tmp_file_path = tmp_file.name

                with st.spinner("Processando..."):
                    texto_extraido = extrair_texto_pdf(tmp_file_path)
                    os.unlink(tmp_file_path)
                    
                    if texto_extraido:
                        st.session_state.texto_lei = texto_extraido
                        st.session_state.nome_documento = uploaded_file.name
                        st.session_state.chat_messages = []
                        
                        boas_vindas = f"""Olá! Analisei o documento **{uploaded_file.name}**. 

Como posso ajudar você hoje?"""
                        
                        st.session_state.chat_messages.append({
                            "role": "assistant",
                            "content": boas_vindas,
                            "timestamp": datetime.now()
                        })
                        st.rerun()
        
        if st.session_state.texto_lei:
            st.info(f"""
            **Documento:**  
            {st.session_state.nome_documento}  
            **Perfil:** {st.session_state.persona_usuario.split(' ')[1]}
            """)
    
    st.markdown("---")
    
    # Ferramentas (apenas com documento)
    if st.session_state.texto_lei:
        with st.expander("**Ferramentas**", expanded=True):
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("📊 Análise", use_container_width=True):
                    if not st.session_state.analise_realizada:
                        with st.spinner("Analisando..."):
                            analise = analisar_legibilidade_gemini(st.session_state.texto_lei)
                            st.session_state.chat_messages.append({
                                "role": "user",
                                "content": "Analisar legibilidade",
                                "timestamp": datetime.now()
                            })
                            st.session_state.chat_messages.append({
                                "role": "assistant", 
                                "content": f"## Análise de Legibilidade\n\n{analise}",
                                "timestamp": datetime.now()
                            })
                            st.session_state.analise_realizada = True
                            st.rerun()
            
            with col2:
                if st.button("📝 Resumo", use_container_width=True):
                    if not st.session_state.resumo_realizado:
                        with st.spinner("Resumindo..."):
                            resumo = gerar_resumo_gemini(st.session_state.texto_lei)
                            st.session_state.chat_messages.append({
                                "role": "user",
                                "content": "Gerar resumo",
                                "timestamp": datetime.now()
                            })
                            st.session_state.chat_messages.append({
                                "role": "assistant",
                                "content": f"## Resumo\n\n{resumo}",
                                "timestamp": datetime.now()
                            })
                            st.session_state.resumo_realizado = True
                            st.rerun()
            
            if st.button("🎯 Casos Práticos", use_container_width=True):
                with st.spinner("Gerando..."):
                    casos = gerar_casos_praticos(st.session_state.texto_lei)
                    st.session_state.chat_messages.append({
                        "role": "user",
                        "content": "Casos práticos",
                        "timestamp": datetime.now()
                    })
                    st.session_state.chat_messages.append({
                        "role": "assistant",
                        "content": f"## Casos Práticos\n\n{casos}",
                        "timestamp": datetime.now()
                    })
                    st.rerun()
            
            if st.button("⏰ Prazos", use_container_width=True):
                with st.spinner("Buscando..."):
                    prazos = extrair_prazos_importantes(st.session_state.texto_lei)
                    st.session_state.chat_messages.append({
                        "role": "user",
                        "content": "Prazos importantes",
                        "timestamp": datetime.now()
                    })
                    st.session_state.chat_messages.append({
                        "role": "assistant",
                        "content": f"## Prazos\n\n{prazos}",
                        "timestamp": datetime.now()
                    })
                    st.rerun()
            
            busca_query = st.text_input("Buscar:", placeholder="Ex: multas, prazos...")
            if st.button("🔍 Buscar", use_container_width=True) and busca_query:
                with st.spinner("Processando..."):
                    resultado_busca = busca_semantica(st.session_state.texto_lei, busca_query)
                    st.session_state.chat_messages.append({
                        "role": "user",
                        "content": f"Buscar: {busca_query}",
                        "timestamp": datetime.now()
                    })
                    st.session_state.chat_messages.append({
                        "role": "assistant",
                        "content": f"## Resultados para '{busca_query}'\n\n{resultado_busca}",
                        "timestamp": datetime.now()
                    })
                    st.rerun()

# Área Principal
if not st.session_state.texto_lei:
    # Tela inicial clean
    st.markdown("""
    ## Bem-vindo ao LexFácil
    
    Seu assistente para simplificar textos jurídicos.
    
    **Como começar:**
    1. Carregue um PDF na barra lateral
    2. Converse sobre o documento
    3. Use as ferramentas de análise
    
    """)
    
    st.image("https://via.placeholder.com/600x300?text=LexF%C3%A1cil", caption="Assistente Jurídico Inteligente")
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        ### Recursos Principais
        - Análise de complexidade
        - Resumo simplificado
        - Casos práticos
        - Prazos importantes
        - Busca inteligente
        """)
    
    with col2:
        st.markdown("""
        ### Personalização
        Escolha seu perfil:
        - Cidadão
        - Empresário
        - Advogado
        - Servidor Público
        """)
else:
    # Chat
    for message in st.session_state.chat_messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    if prompt := st.chat_input("Digite sua pergunta..."):
        st.session_state.chat_messages.append({
            "role": "user",
            "content": prompt,
            "timestamp": datetime.now()
        })
        
        with st.chat_message("user"):
            st.markdown(prompt)
        
        with st.chat_message("assistant"):
            with st.spinner("Pensando..."):
                resposta = processar_pergunta_chat(prompt)
                st.markdown(resposta)
                st.session_state.chat_messages.append({
                    "role": "assistant",
                    "content": resposta,
                    "timestamp": datetime.now()
                })

# Sugestões (quando aplicável)
if st.session_state.texto_lei and len(st.session_state.chat_messages) <= 1:
    st.markdown("**Sugestões:**")
    
    sugestoes = {
        "👨‍👩‍👧‍👦 Cidadão": ["Como me afeta?", "Quais meus direitos?", "O que acontece se não cumprir?"],
        "👨‍💼 Empresário": ["Impactos para negócios?", "Custos de adequação?", "Prazos?"],
        "👩‍⚖️ Advogado": ["Principais mudanças?", "Interpretação do artigo X?", "Sanções?"],
        "🏛️ Servidor": ["Como aplicar?", "Procedimentos?", "Competências?"]
    }.get(st.session_state.persona_usuario, [])
    
    cols = st.columns(3)
    for i, sug in enumerate(sugestoes):
        with cols[i % 3]:
            st.markdown(f'<div class="suggestion-chip">{sug}</div>', unsafe_allow_html=True)
            if st.button(sug, key=f"sug_{i}", label_visibility="hidden"):
                st.session_state.chat_messages.append({
                    "role": "user",
                    "content": sug,
                    "timestamp": datetime.now()
                })
                
                with st.spinner("Pensando..."):
                    resposta = processar_pergunta_chat(sug)
                    st.session_state.chat_messages.append({
                        "role": "assistant",
                        "content": resposta,
                        "timestamp": datetime.now()
                    })
                st.rerun()

# Footer minimalista
st.markdown("---")
st.caption("LexFácil © - Transformando leis complexas em linguagem acessível")
