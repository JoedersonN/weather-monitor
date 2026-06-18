"""
Weather Monitor - Jacobina, BA
Aplicativo de monitoramento de clima em tempo real usando a API OpenWeatherMap.

Autor: Joederson Neves
"""

import os
import tkinter as tk
from tkinter import messagebox
import requests
from datetime import datetime

# ---------------------------------------------------------
# Configuração
# ---------------------------------------------------------
# A API key NUNCA deve ficar hardcoded no código.
# Defina a variável de ambiente OPENWEATHER_API_KEY antes de rodar:
#
# Windows (PowerShell):
#   $env:OPENWEATHER_API_KEY="sua_chave_aqui"
#
# Windows (CMD):
#   set OPENWEATHER_API_KEY=sua_chave_aqui
#
# Linux/Mac:
#   export OPENWEATHER_API_KEY="sua_chave_aqui"

API_KEY = os.getenv("OPENWEATHER_API_KEY")
CIDADE_PADRAO = "Jacobina,BR"
BASE_URL = "https://api.openweathermap.org/data/2.5/weather"


def buscar_clima(cidade: str) -> dict | None:
    """Consulta a API OpenWeatherMap e retorna os dados de clima da cidade."""
    if not API_KEY:
        messagebox.showerror(
            "Erro de configuração",
            "Variável de ambiente OPENWEATHER_API_KEY não definida.\n\n"
            "Configure-a antes de rodar o aplicativo."
        )
        return None

    params = {
        "q": cidade,
        "appid": API_KEY,
        "units": "metric",
        "lang": "pt_br",
    }

    try:
        resposta = requests.get(BASE_URL, params=params, timeout=10)
        resposta.raise_for_status()
        return resposta.json()
    except requests.exceptions.HTTPError:
        if resposta.status_code == 401:
            messagebox.showerror("Erro", "API key inválida ou não autorizada.")
        elif resposta.status_code == 404:
            messagebox.showerror("Erro", f"Cidade '{cidade}' não encontrada.")
        else:
            messagebox.showerror("Erro", f"Erro HTTP {resposta.status_code}.")
    except requests.exceptions.ConnectionError:
        messagebox.showerror("Erro", "Sem conexão com a internet.")
    except requests.exceptions.Timeout:
        messagebox.showerror("Erro", "A requisição demorou demais (timeout).")
    except Exception as e:
        messagebox.showerror("Erro inesperado", str(e))

    return None


def formatar_dados(dados: dict) -> str:
    """Formata os dados retornados pela API em texto legível."""
    cidade = dados.get("name", "—")
    pais = dados.get("sys", {}).get("country", "—")
    temp = dados["main"]["temp"]
    sensacao = dados["main"]["feels_like"]
    temp_min = dados["main"]["temp_min"]
    temp_max = dados["main"]["temp_max"]
    umidade = dados["main"]["humidity"]
    pressao = dados["main"]["pressure"]
    descricao = dados["weather"][0]["description"].capitalize()
    vento = dados["wind"]["speed"]

    # Timezone offset (em segundos) retornado pela API, relativo a UTC.
    # Sem isso, sunrise/sunset calculados com fromtimestamp() usam o
    # fuso horário LOCAL DA MÁQUINA, o que gera horários incorretos
    # quando o app roda em fuso diferente do da cidade consultada.
    tz_offset = dados.get("timezone", 0)
    nascer_utc = datetime.utcfromtimestamp(dados["sys"]["sunrise"] + tz_offset)
    poente_utc = datetime.utcfromtimestamp(dados["sys"]["sunset"] + tz_offset)
    nascer = nascer_utc.strftime("%H:%M")
    poente = poente_utc.strftime("%H:%M")

    atualizado = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    return (
        f"Local: {cidade}, {pais}\n\n"
        f"Temperatura: {temp:.1f}°C\n"
        f"Sensação: {sensacao:.1f}°C\n"
        f"Mínima: {temp_min:.1f}°C   |   Máxima: {temp_max:.1f}°C\n\n"
        f"Condição: {descricao}\n"
        f"Umidade: {umidade}%\n"
        f"Pressão: {pressao} hPa\n"
        f"Vento: {vento} m/s\n\n"
        f"Nascer do sol: {nascer}   |   Pôr do sol: {poente}\n\n"
        f"Atualizado em: {atualizado}"
    )


# ---------------------------------------------------------
# Interface Tkinter
# ---------------------------------------------------------
class WeatherApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Weather Monitor")
        self.root.geometry("420x480")
        self.root.resizable(False, False)
        self.root.configure(bg="#0d1117")

        self._montar_interface()
        self.atualizar_clima()  # carrega a cidade padrão ao abrir

    def _montar_interface(self):
        fonte_titulo = ("Consolas", 16, "bold")
        fonte_label = ("Consolas", 11)
        fonte_resultado = ("Consolas", 11)

        tk.Label(
            self.root, text="Weather Monitor",
            font=fonte_titulo, bg="#0d1117", fg="#58a6ff"
        ).pack(pady=(16, 4))

        # Campo de busca
        frame_busca = tk.Frame(self.root, bg="#0d1117")
        frame_busca.pack(pady=8)

        self.entrada_cidade = tk.Entry(
            frame_busca, font=fonte_label, width=22,
            bg="#161b22", fg="#e6edf3", insertbackground="#e6edf3",
            relief="flat"
        )
        self.entrada_cidade.insert(0, CIDADE_PADRAO)
        self.entrada_cidade.pack(side="left", padx=(0, 8), ipady=4)
        self.entrada_cidade.bind("<Return>", lambda event: self.atualizar_clima())

        tk.Button(
            frame_busca, text="Buscar", command=self.atualizar_clima,
            bg="#238636", fg="white", relief="flat", font=fonte_label,
            activebackground="#2ea043", cursor="hand2"
        ).pack(side="left")

        # Área de resultado
        self.label_resultado = tk.Label(
            self.root, text="Carregando...", font=fonte_resultado,
            bg="#161b22", fg="#e6edf3", justify="left",
            anchor="nw", padx=16, pady=16, width=38, height=18,
            wraplength=360
        )
        self.label_resultado.pack(pady=12, padx=16, fill="both", expand=True)

        tk.Button(
            self.root, text="Atualizar", command=self.atualizar_clima,
            bg="#21262d", fg="#e6edf3", relief="flat", font=fonte_label,
            activebackground="#30363d", cursor="hand2"
        ).pack(pady=(0, 12))

    def atualizar_clima(self):
        cidade = self.entrada_cidade.get().strip() or CIDADE_PADRAO
        self.label_resultado.config(text="Buscando dados...")
        self.root.update_idletasks()

        dados = buscar_clima(cidade)
        if dados:
            texto = formatar_dados(dados)
            self.label_resultado.config(text=texto)
        else:
            self.label_resultado.config(text="Não foi possível obter os dados.")


def main():
    root = tk.Tk()
    WeatherApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()