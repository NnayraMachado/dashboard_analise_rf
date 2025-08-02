import json
import os
from collections import Counter
from statistics import mean
from datetime import datetime

LOG_JSON_PATH = os.path.join("logs", "historico_perguntas.json")
OUTPUT_HTML = os.path.join("logs", "resumo_logs.html")
OUTPUT_MD = os.path.join("logs", "resumo_logs.md")


def carregar_logs(caminho_json=LOG_JSON_PATH):
    if not os.path.exists(caminho_json):
        print(f"Aviso: arquivo de log não encontrado em {caminho_json}")
        return []
    try:
        with open(caminho_json, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Erro ao carregar JSON de logs (possivelmente corrompido): {e}")
        # Tentativa de recuperação simples: carregar linha a linha ignorando inválidos
        recovered = []
        with open(caminho_json, "r", encoding="utf-8", errors="ignore") as f:
            try:
                content = f.read()
                # tentativa simplista de extrair múltiplos objetos
                recovered = json.loads(content)
            except Exception:
                print("Recuperação falhou; retornando lista vazia.")
        return recovered


def gerar_resumo(logs):
    total = len(logs)
    perguntas = [l.get("pergunta", "").strip() for l in logs if l.get("pergunta")]
    frequencia_perguntas = Counter(perguntas).most_common(10)
    niveis = [l.get("nivel_confianca") for l in logs if l.get("nivel_confianca")]
    freq_niveis = Counter(niveis)
    filtrados = [l.get("total_filtrado", 0) for l in logs if isinstance(l.get("total_filtrado"), (int, float))]
    media_filtrada = mean(filtrados) if filtrados else 0
    datas = []
    for l in logs:
        ts = l.get("timestamp")
        if ts:
            try:
                dt = datetime.fromisoformat(ts)
                datas.append(dt)
            except Exception:
                pass
    primeira = min(datas).isoformat() if datas else "n/a"
    ultima = max(datas).isoformat() if datas else "n/a"

    resumo = {
        "total_registros_log": total,
        "intervalo_temporal": {"primeira": primeira, "ultima": ultima},
        "top_perguntas": frequencia_perguntas,
        "distribuicao_niveis_confianca": dict(freq_niveis),
        "media_total_filtrado": media_filtrada,
    }
    return resumo


def render_markdown(resumo_dict):
    md = []
    md.append(f"# Resumo dos Logs de Interação ({resumo_dict['total_registros_log']} consultas)\n")
    intervalo = resumo_dict["intervalo_temporal"]
    md.append(f"- **Período registrado:** {intervalo['primeira']} até {intervalo['ultima']}\n")
    md.append(f"- **Média de registros filtrados por consulta:** {resumo_dict['media_total_filtrado']:.1f}\n")
    md.append("## Perguntas mais comuns (top 10)")
    for pergunta, count in resumo_dict["top_perguntas"]:
        md.append(f"- {count}x — {pergunta}")
    md.append("\n## Distribuição de níveis de confiança")
    for nivel, freq in resumo_dict["distribuicao_niveis_confianca"].items():
        md.append(f"- {nivel}: {freq}")
    md.append("\n*Gerado em " + datetime.utcnow().isoformat() + "*\n")
    return "\n".join(md)


def salvar_relatorio(resumo_md, caminho_md=OUTPUT_MD, caminho_html=OUTPUT_HTML):
    # salva markdown
    with open(caminho_md, "w", encoding="utf-8") as f:
        f.write(resumo_md)
    # converte simples para HTML (envolve em <pre> para preservar formato)
    html_content = f"""<html>
<head><meta charset="utf-8"><title>Resumo de Logs</title></head>
<body>
<pre style="font-family: system-ui; white-space: pre-wrap;">{resumo_md}</pre>
</body>
</html>
"""
    with open(caminho_html, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"Relatórios salvos em: {caminho_md} e {caminho_html}")


def main():
    logs = carregar_logs()
    if not logs:
        print("Nenhum log válido carregado.")
        return
    resumo = gerar_resumo(logs)
    md = render_markdown(resumo)
    salvar_relatorio(md)


if __name__ == "__main__":
    main()
