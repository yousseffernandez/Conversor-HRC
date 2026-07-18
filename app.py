import json
import re
import os
import tkinter as tk
from tkinter import messagebox

def gerar_json():
    texto = entrada.get("1.0", tk.END)
    nome_torneio = campo_nome.get()
    stack = campo_stack.get()
    jogadores = campo_jogadores.get()

    prizes = {}
    bounty_detectado = False

    try:
        if not nome_torneio:
            messagebox.showerror("Erro", "Digite o nome do torneio.")
            return

        if not stack or not jogadores:
            messagebox.showerror("Erro", "Preencha stack e número de jogadores.")
            return

        stack = float(stack)
        jogadores = int(jogadores)

        chips = stack * jogadores

        linhas = [l.strip() for l in texto.strip().split("\n") if l.strip()]

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

                if "+" in linha_valor:
                    valor = float(valores[0].replace(",", ""))
                    prizes[posicao] = valor
                    bounty_detectado = True

                elif len(valores) == 1:
                    valor = float(valores[0].replace(",", ""))
                    prizes[posicao] = valor

                elif len(valores) >= 2:
                    valor = float(valores[0].replace(",", ""))
                    prizes[posicao] = valor

                i += 3
                continue

            # =========================
            # CASO 2 → SharkScope (PKO + Regular + "-")
            # =========================
            match_pos = re.match(r'^(\d+)', linha)

            if match_pos:
                posicao = match_pos.group(1)

                # caso "-"
                if "-" in linha:
                    prizes[posicao] = 0.0
                    i += 1
                    continue

                valores = re.findall(r'[$¥€]([\d,]+(?:\.\d+)?)', linha)

                # PKO
                if "Recompensa" in linha or "Recompensas" in linha or "Bounty" in linha:
                    if len(valores) >= 2:
                        total = float(valores[0].replace(",", ""))
                        bounty = float(valores[1].replace(",", ""))

                        prizes[posicao] = round(total - bounty, 2)
                        bounty_detectado = True

                # Regular
                elif len(valores) == 1:
                    prizes[posicao] = float(valores[0].replace(",", ""))

                i += 1
                continue

            i += 1

        if not prizes:
            messagebox.showerror("Erro", "Nenhum dado válido encontrado.")
            return

        # =========================
        # 🔥 ORDENAR E REMOVER ZEROS DO FINAL
        # =========================
        prizes_ordenados = dict(sorted(prizes.items(), key=lambda x: int(x[0])))

        while prizes_ordenados and list(prizes_ordenados.values())[-1] == 0.0:
            prizes_ordenados.popitem()

        prizes = prizes_ordenados

        # =========================
        # COMPATÍVEL COM HRC
        # =========================
        bounty_type = "PKO" if bounty_detectado else "NONE"
        progressive_factor = 0.5 if bounty_detectado else 0.0

        data = {
            "name": "/",
            "folders": [],
            "structures": [
                {
                    "name": nome_torneio,
                    "bountyType": bounty_type,
                    "progressiveFactor": progressive_factor,
                    "chips": chips,
                    "prizes": prizes
                }
            ]
        }

        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        caminho = os.path.join(desktop, "saida.json")

        with open(caminho, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        messagebox.showinfo("Sucesso", "JSON gerado na Área de Trabalho!")

    except Exception as e:
        messagebox.showerror("Erro", str(e))


# =========================
# INTERFACE
# =========================
janela = tk.Tk()
janela.title("Conversor Poker → JSON (HRC Ready FINAL)")
janela.geometry("650x550")

tk.Label(janela, text="Nome do torneio:").pack()
campo_nome = tk.Entry(janela, width=50)
campo_nome.pack(pady=5)

tk.Label(janela, text="Stack inicial:").pack()
campo_stack = tk.Entry(janela, width=20)
campo_stack.pack(pady=5)

tk.Label(janela, text="Quantidade de jogadores:").pack()
campo_jogadores = tk.Entry(janela, width=20)
campo_jogadores.pack(pady=5)

tk.Label(janela, text="Cole os dados:").pack(pady=10)
entrada = tk.Text(janela, height=15, width=75)
entrada.pack()

tk.Button(janela, text="Gerar JSON", command=gerar_json).pack(pady=15)

janela.mainloop()