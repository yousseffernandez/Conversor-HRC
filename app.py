import json
import re
import streamlit as st

# Configuração da página do Streamlit
st.set_page_config(
    page_title="Conversor Poker → HRC JSON",
    page_icon="🃏",
    layout="centered"
)

st.title("🃏 Conversor Poker → HRC JSON")
st.markdown("Transforme os dados do PokerCraft ou SharkScope em arquivos estruturados para o HRC.")
st.markdown("---")

# Inputs da interface web
nome_torneio = st.text_input("Nome do Torneio:", placeholder="Ex: Daily Main Event $250")
chips_raw = st.text_input("Quantidade de Fichas (Chips):", placeholder="Ex: 100000")
texto = st.text_area("Cole os dados do Torneio aqui:", height=250, placeholder="Cole as linhas do PokerCraft ou SharkScope...")

if st.button("CONVERTER DADOS", type="primary"):
    # Validações iniciais
    if not nome_torneio:
        st.error("⚠️ Por favor, digite o nome do torneio.")
    elif not chips_raw:
        st.error("⚠️ Por favor, digite a quantidade de fichas.")
    else:
        try:
            # Suporta tanto vírgula quanto ponto para decimais/milhar
            chips = float(chips_raw.replace(",", "."))
            
            # Processamento do texto
            linhas = [l.strip() for l in texto.strip().split("\n") if l.strip()]
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
                    valores = re.findall(r'[$¥€]([\d,]+\.\d+)', linha_valor)

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

            # 🛠️ FILTRO DE SEGURANÇA (LIMPEZA DO BUG)
            # Remove qualquer posição que tenha valor zero, nulo ou que não seja estritamente maior que 0
            prizes_limpos = {}
            for pos, val in prizes.items():
                try:
                    val_float = float(val)
                    # Só adiciona se for um número válido maior que zero e a posição for válida
                    if val_float > 0 and pos.isdigit():
                        prizes_limpos[pos] = val_float
                except:
                    continue

            # Se deu tudo certo e achou prêmios válidos
            if not prizes_limpos:
                st.warning("🕵️‍♂️ Nenhum dado válido de premiação foi encontrado no texto. Verifique a formatação.")
            else:
                # Monta a estrutura do JSON com o dicionário filtrado
                data = {
                    "name": "/",
                    "folders": [],
                    "structures": [
                        {
                            "name": nome_torneio,
                            "bountyType": "PKO",
                            "progressiveFactor": 0.5,
                            "chips": chips,
                            "prizes": prizes_limpos
                        }
                    ]
                }

                # Transforma o dicionário em string formatada em JSON
                json_string = json.dumps(data, ensure_ascii=False, indent=2)
                
                # Nome do arquivo limpo para o download
                nome_arquivo = re.sub(r'[\\/*?:"<>|]', "", nome_torneio) + ".json"

                st.success("✅ Dados processados e limpos com sucesso!")
                
                # Botão nativo do Streamlit para baixar o arquivo gerado
                st.download_button(
                    label="📥 BAIXAR ARQUIVO JSON",
                    data=json_string,
                    file_name=nome_arquivo,
                    mime="application/json"
                )

        except ValueError:
            st.error("⚠️ A quantidade de fichas deve ser um número válido.")
        except Exception as e:
            st.error(f"💥 Ocorreu um erro inesperado: {str(e)}")
