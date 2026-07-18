import json
import re
import streamlit as st
import easyocr
import cv2
import numpy as np
from streamlit_paste_button import paste_image_button

# Configuração da página do Streamlit
st.set_page_config(
    page_title="Conversor Poker → HRC JSON",
    page_icon="🃏",
    layout="centered"
)

# Inicializa o leitor de OCR em cache para não carregar toda vez
@st.cache_resource
def carregar_leitor_ocr():
    return easyocr.Reader(['pt', 'en'], gpu=False)

st.title("🃏 Conversor Poker → HRC JSON")
st.markdown("Transforme os dados do PokerCraft ou SharkScope em arquivos estruturados para o HRC.")
st.markdown("---")

# Inputs fixos na interface
nome_torneio = st.text_input("Nome do Torneio:", placeholder="Ex: Daily Main Event $250")
chips_raw = st.text_input("Quantidade de Fichas (Chips):", placeholder="Ex: 100000")

st.markdown("### Selecione o método de entrada de dados:")
aba_texto, aba_imagem = st.tabs(["📄 Colar Texto (Original)", "📸 Colar Print/Imagem (Ctrl+V)"])

texto_para_processar = ""

# --- ABA 1: TEXTO TRADICIONAL ---
with aba_texto:
    texto_puro = st.text_area(
        "Cole as linhas do PokerCraft ou SharkScope aqui:", 
        height=250, 
        placeholder="Cole as linhas copiadas...",
        key="txt_area"
    )
    if texto_puro:
        texto_para_processar = texto_puro

# --- ABA 2: LEITURA DE PRINT POR CTRL+V ---
with aba_imagem:
    st.info("💡 Tire um print da tabela (Win + Shift + S) e clique no botão abaixo para colar direto com Ctrl+V!")
    
    # Cria o botão que escuta o Ctrl+V
    colado = paste_image_button(
        label="📋 CLIQUE AQUI E DEPOIS DÊ CTRL + V PARA COLAR O PRINT",
        background_color="#FF4B4B",
        hover_background_color="#D32F2F",
        errors="ignore"
    )
    
    if colado and colado.image_data is not None:
        st.image(colado.image_data, caption="Print colado com sucesso!", use_container_width=True)
        
        with st.spinner("Processando imagem e extraindo texto..."):
            try:
                # Converte os dados da imagem colada para o formato do OpenCV
                img_bgr = cv2.cvtColor(np.array(colado.image_data), cv2.COLOR_RGB2BGR)
                
                # Executa o OCR
                reader = carregar_leitor_ocr()
                resultado_ocr = reader.readtext(img_bgr, detail=0)
                
                # Junta o texto lido
                texto_para_processar = "\n".join(resultado_ocr)
                
                st.success("🤖 Texto extraído da imagem com sucesso!")
                with st.expander("Ver texto que a Inteligência Artificial conseguiu ler:"):
                    st.code(texto_para_processar)
                    st.warning("⚠️ Atenção: Verifique se o leitor não trocou nenhuma letra ou número devido à resolução.")
            except Exception as e:
                st.error(f"Erro ao processar a imagem: {str(e)}")

# --- BOTÃO DE PROCESSAMENTO GERAL ---
st.markdown("---")
if st.button("CONVERTER DADOS", type="primary"):
    if not nome_torneio:
        st.error("⚠️ Por favor, digite o nome do torneio.")
    elif not chips_raw:
        st.error("⚠️ Por favor, digite a quantidade de fichas.")
    elif not texto_para_processar:
        st.error("⚠️ Nenhum dado encontrado. Cole o texto ou dê Ctrl+V em uma imagem válida.")
    else:
        try:
            chips = float(chips_raw.replace(",", "."))
            linhas = [l.strip() for l in texto_para_processar.strip().split("\n") if l.strip()]
            prizes = {}
            i = 0

            while i < len(linhas):
                linha = linhas[i]

                # =========================
                # CASO 1 → PokerCraft (3 linhas)
                # =========================
                if linha.isdigit() and i + 2 < len(linhas):
                    posicao = linha
                    linha_valor = linhas[i + 2]
                    valores = re.findall(r'[$¥€]([\d,]+\.\d+)', App_hrc_valor := linha_valor)

                    if valores:
                        valores_limpos = [float(v.replace(",", "")) for v in valores]
                        if len(valores_limpos) >= 3:
                            prizes[posicao] = valores_limpos[1]  # PKO
                        elif len(valores_limpos) == 1:
                            prizes[posicao] = valores_limpos[0]  # Regular
                        elif len(valores_limpos) == 2:
                            prizes[posicao] = valores_limpos[0]  # Fallback

                    i += 3
                    continue

                # =========================
                # CASO 2 → SharkScope PKO
                # =========================
                if any(w in linha for w in ["Recompensa", "Recompensas", "Bounty"]):
                    valores = re.findall(r'[$¥€]([\d,]+(?:\.\d+)?)', linha)

                    if valores and len(valores) >= 2:
                        total = float(valores[0].replace(",", ""))
                        bounty = float(valores[1].replace(",", ""))
                        valor = total - bounty
                        
                        posicao_match = re.match(r'^\d+', linha)
                        posicao = posicao_match.group(0) if posicao_match else str(len(prizes) + 1)
                        prizes[posicao] = round(valor, 2)

                    i += 1
                    continue

                # =========================
                # CASO 3 → SharkScope REGULAR
                # =========================
                match_pos = re.match(r'^\d+', linha)
                valores = re.findall(r'[$¥€]([\d,]+(?:\.\d+)?)', linha)

                if match_pos and valores and len(valores) == 1:
                    posicao = match_pos[0]
                    valor = float(valores[0].replace(",", ""))
                    prizes[posicao] = valor
                    i += 1
                    continue

                i += 1

            if not prizes:
                st.warning("🕵️‍♂️ Nenhum dado de premiação foi reconhecido pelo filtro. Garanta que os valores e posições aparecem claramente no print.")
            else:
                data = {
                    "name": "/",
                    "folders": [],
                    "structures": [
                        {
                            "name": nome_torneio,
                            "bountyType": "PKO",
                            "progressiveFactor": 0.5,
                            "chips": chips,
                            "prizes": prizes
                        }
                    ]
                }

                json_string = json.dumps(data, ensure_ascii=False, indent=2)
                nome_arquivo = re.sub(r'[\\/*?:"<>|]', "", nome_torneio) + ".json"

                st.success("✅ Dados processados com sucesso!")
                st.download_button(
                    label="📥 BAIXAR ARQUIVO JSON",
                    data=json_string,
                    file_name=nome_arquivo,
                    mime="application/json"
                )

        except ValueError:
            st.error("⚠️ A quantidade de fichas deve ser um número válido.")
        except Exception as e:
            st.error(f"💥 Erro no processamento: {str(e)}")
