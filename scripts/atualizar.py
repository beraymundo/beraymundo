"""Gera o README do perfil e as imagens em assets/ a partir de perfil.json
e dos repositórios públicos do usuário.

Uso:  python scripts/atualizar.py
Token (opcional, evita limite da API): variável GITHUB_TOKEN ou GH_TOKEN.
Só usa a biblioteca padrão do Python.
"""

import json
import os
import textwrap
import urllib.request
from datetime import datetime
from html import escape
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
API = "https://api.github.com"

# Paleta do tema (a mesma da Central de Ferramentas, modo escuro).
COR = {
    "fundo": "#0b0b0c",
    "cartao": "#121214",
    "borda": "#26262a",
    "texto": "#e8e8ea",
    "mudo": "#8b8b91",
    "azul": "#5b93ff",
}
TONS = ["#5b93ff", "#2f6fe8", "#9dbcff", "#1d4fb8", "#cfdcff", "#8b8b91", "#4a4a50"]
FONTE = "'Cascadia Code','Cascadia Mono','JetBrains Mono','SF Mono',Menlo,Consolas,'Liberation Mono',monospace"
MESES = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]


# --------------------------------------------------------------------------
# API do GitHub
# --------------------------------------------------------------------------

def api(caminho):
    req = urllib.request.Request(API + caminho, headers={
        "Accept": "application/vnd.github+json",
        "User-Agent": "perfil-atualizador",
    })
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token:
        req.add_header("Authorization", "Bearer " + token)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def buscar_repos(cfg):
    repos, pagina = [], 1
    while True:
        lote = api(f"/users/{cfg['usuario']}/repos?per_page=100&page={pagina}&type=owner")
        repos += lote
        if len(lote) < 100:
            break
        pagina += 1

    ocultar = set(cfg.get("ocultar", [])) | {cfg["usuario"]}
    forks = set(cfg.get("incluir_forks", []))
    saida = []
    for r in repos:
        if r["private"] or r["name"] in ocultar or r.get("archived"):
            continue
        if r["fork"] and r["name"] not in forks:
            continue
        r["linguagens"] = api(f"/repos/{r['full_name']}/languages")
        saida.append(r)
    return saida


# --------------------------------------------------------------------------
# Organização dos dados
# --------------------------------------------------------------------------

def info_repo(cfg, r):
    extra = cfg.get("repos", {}).get(r["name"], {})
    langs = sorted(r["linguagens"].items(), key=lambda x: -x[1])
    return {
        "id": r["name"],
        "nome": extra.get("nome") or r["name"],
        "descricao": extra.get("descricao") or r.get("description") or "",
        "url": r["html_url"],
        "site": r.get("homepage") or "",
        "stack": [n for n, _ in langs[:3]],
        "topicos": r.get("topics", []),
        "estrelas": r.get("stargazers_count", 0),
        "push": datetime.strptime(r["pushed_at"], "%Y-%m-%dT%H:%M:%SZ"),
        "area": extra.get("area"),
    }


def agrupar(cfg, projetos):
    areas = cfg.get("areas", [])
    grupos = {a["id"]: [] for a in areas}
    outros = []
    for p in projetos:
        alvo = p["area"]
        if not alvo:
            for a in areas:
                if any(t in p["topicos"] for t in a["topicos"]):
                    alvo = a["id"]
                    break
        (grupos[alvo] if alvo in grupos else outros).append(p)

    destaque = {nome: i for i, nome in enumerate(cfg.get("destaques", []))}
    ordem = lambda p: (destaque.get(p["id"], 999), -p["push"].timestamp())
    lista = [(a["titulo"], sorted(grupos[a["id"]], key=ordem)) for a in areas if grupos[a["id"]]]
    if outros:
        lista.append((cfg.get("area_padrao", "Outros projetos"), sorted(outros, key=ordem)))
    return lista


def somar_linguagens(repos):
    total = {}
    for r in repos:
        for nome, bytes_ in r["linguagens"].items():
            total[nome] = total.get(nome, 0) + bytes_
    return sorted(total.items(), key=lambda x: -x[1])


def mes_ano(d):
    return f"{MESES[d.month - 1]}/{d.year}"


# --------------------------------------------------------------------------
# SVG: janela de terminal
# --------------------------------------------------------------------------

def svg_terminal(cfg, projetos, linguagens):
    largura, margem, tam, alt_linha = 900, 28, 14, 22
    cols = int((largura - 2 * margem) / (tam * 0.6))
    usuario = cfg["nome"].split()[0].lower()

    linhas = []  # cada linha: lista de (classe, texto)

    def prompt(cmd):
        linhas.append([("a", f"{usuario}@github"), ("m", ":"), ("a", "~"), ("m", "$ "), ("t", cmd)])

    def saida(txt, classe="t"):
        for parte in textwrap.wrap(txt, cols) or [""]:
            linhas.append([(classe, parte)])

    prompt("whoami")
    saida(cfg["nome"])
    saida(cfg.get("titulo", ""), "m")
    linhas.append([])
    prompt("cat resumo.txt")
    saida(cfg.get("resumo", ""))
    linhas.append([])

    prompt("ls projetos/")
    nomes = [p["id"] + "/" for p in projetos] + [
        f["nome"].lower().replace(" ", "-") + "/" for f in cfg.get("fora_do_github", [])
    ]
    larg_col = max((len(n) for n in nomes), default=10) + 3
    por_linha = max(1, cols // larg_col)
    for i in range(0, len(nomes), por_linha):
        linhas.append([("a", "".join(n.ljust(larg_col) for n in nomes[i:i + por_linha]).rstrip())])
    linhas.append([])

    prompt("cat status")
    ultimo = max(projetos, key=lambda p: p["push"]) if projetos else None
    status = [
        ("repositórios", f"{len(projetos)} público{'s' if len(projetos) != 1 else ''}" + (
            f" + {len(cfg.get('fora_do_github', []))} fora do GitHub" if cfg.get("fora_do_github") else "")),
        ("linguagens", ", ".join(n for n, _ in linguagens[:5]) or "-"),
    ]
    if ultimo:
        status.append(("último push", f"{ultimo['id']}  ({ultimo['push']:%d/%m/%Y})"))
    if cfg.get("local"):
        status.append(("local", cfg["local"]))
    for chave, valor in status:
        linhas.append([("m", chave.ljust(15)), ("t", valor)])
    linhas.append([])
    linhas.append([("a", f"{usuario}@github"), ("m", ":"), ("a", "~"), ("m", "$ "), ("cursor", "")])

    topo = 40
    altura = topo + 22 + len(linhas) * alt_linha + 16
    passo = 0.09  # segundos entre linhas na animação de entrada

    corpo = []
    for i, partes in enumerate(linhas):
        y = topo + 28 + i * alt_linha
        atraso = f"{i * passo:.2f}s"
        if partes and partes[-1][0] == "cursor":
            x = margem + sum(len(t) for c, t in partes[:-1]) * tam * 0.6
            texto = "".join(f'<tspan class="{c}">{escape(t)}</tspan>' for c, t in partes[:-1])
            corpo.append(f'<g class="l" style="animation-delay:{atraso}">'
                         f'<text x="{margem}" y="{y}" xml:space="preserve">{texto}</text>'
                         f'<rect class="cur" x="{x:.1f}" y="{y - tam + 2}" width="{tam * 0.6:.1f}" height="{tam + 2}"/></g>')
            continue
        if not partes:
            continue
        texto = "".join(f'<tspan class="{c}">{escape(t)}</tspan>' for c, t in partes)
        corpo.append(f'<text class="l" style="animation-delay:{atraso}" x="{margem}" y="{y}" '
                     f'xml:space="preserve">{texto}</text>')

    titulo = f"{usuario}@github: ~"
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{largura}" height="{altura}" viewBox="0 0 {largura} {altura}" role="img" aria-label="{escape(cfg['nome'])}">
<style>
  text {{ font-family: {FONTE}; font-size: {tam}px; }}
  .t {{ fill: {COR['texto']}; }}
  .m {{ fill: {COR['mudo']}; }}
  .a {{ fill: {COR['azul']}; }}
  .tt {{ fill: {COR['mudo']}; font-size: 12px; }}
  .cur {{ fill: {COR['azul']}; animation: piscar 1.1s steps(1) infinite; }}
  .l {{ opacity: 0; animation: entrar .25s ease-out forwards; }}
  @keyframes entrar {{ from {{ opacity: 0; }} to {{ opacity: 1; }} }}
  @keyframes piscar {{ 50% {{ opacity: 0; }} }}
  @media (prefers-reduced-motion: reduce) {{ .l {{ opacity: 1; animation: none; }} .cur {{ animation: none; }} }}
</style>
<rect x="0.5" y="0.5" width="{largura - 1}" height="{altura - 1}" rx="6" fill="{COR['fundo']}" stroke="{COR['borda']}"/>
<path d="M0.5 6.5a6 6 0 0 1 6-6h{largura - 13}a6 6 0 0 1 6 6V{topo}H0.5z" fill="{COR['cartao']}"/>
<line x1="0.5" y1="{topo}" x2="{largura - 0.5}" y2="{topo}" stroke="{COR['borda']}"/>
<circle cx="22" cy="{topo / 2}" r="5" fill="#3a3a40"/>
<circle cx="40" cy="{topo / 2}" r="5" fill="#3a3a40"/>
<circle cx="58" cy="{topo / 2}" r="5" fill="#3a3a40"/>
<text class="tt" x="{largura / 2}" y="{topo / 2 + 4}" text-anchor="middle">{escape(titulo)}</text>
{chr(10).join(corpo)}
</svg>
'''


# --------------------------------------------------------------------------
# SVG: barra de linguagens
# --------------------------------------------------------------------------

def svg_linguagens(linguagens):
    largura, margem = 900, 28
    total = sum(b for _, b in linguagens) or 1
    principais = linguagens[:6]
    resto = total - sum(b for _, b in principais)
    if resto > 0:
        principais.append(("outras", resto))

    barra_w = largura - 2 * margem
    x, segs = margem, []
    for i, (nome, b) in enumerate(principais):
        w = barra_w * b / total
        segs.append(f'<rect x="{x:.2f}" y="46" width="{max(w, 1):.2f}" height="8" fill="{TONS[i % len(TONS)]}"/>')
        x += w

    legenda, lx, ly = [], margem, 84
    for i, (nome, b) in enumerate(principais):
        rotulo = f"{nome} {100 * b / total:.1f}%"
        larg = len(rotulo) * 7.8 + 34
        if lx + larg > largura - margem:
            lx, ly = margem, ly + 24
        legenda.append(f'<rect x="{lx}" y="{ly - 9}" width="10" height="10" fill="{TONS[i % len(TONS)]}"/>'
                       f'<text x="{lx + 18}" y="{ly}" class="t">{escape(nome)} <tspan class="m">{100 * b / total:.1f}%</tspan></text>')
        lx += larg
    altura = ly + 22

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{largura}" height="{altura}" viewBox="0 0 {largura} {altura}" role="img" aria-label="Linguagens nos repositórios públicos">
<style>
  text {{ font-family: {FONTE}; font-size: 13px; }}
  .t {{ fill: {COR['texto']}; }} .m {{ fill: {COR['mudo']}; }} .a {{ fill: {COR['azul']}; }}
</style>
<rect x="0.5" y="0.5" width="{largura - 1}" height="{altura - 1}" rx="6" fill="{COR['fundo']}" stroke="{COR['borda']}"/>
<text x="{margem}" y="30"><tspan class="a">$</tspan><tspan class="t"> linguagens --repos-publicos</tspan></text>
<clipPath id="c"><rect x="{margem}" y="46" width="{barra_w}" height="8" rx="4"/></clipPath>
<g clip-path="url(#c)">{''.join(segs)}</g>
{''.join(legenda)}
</svg>
'''


# --------------------------------------------------------------------------
# README
# --------------------------------------------------------------------------

def celula(txt):
    return escape(txt, quote=False).replace("|", "\\|")


def gerar_readme(cfg, grupos, tem_linguagens):
    L = []
    L.append(f'<img src="assets/terminal.svg" width="100%" alt="{escape(cfg["nome"])}: {escape(cfg.get("titulo", ""))}">')
    L.append("")

    L.append("## ~/sobre")
    L.append("")
    for p in cfg.get("sobre", []):
        L.append(p)
        L.append("")

    if cfg.get("capacidades"):
        L.append("## ~/o-que-posso-fazer")
        L.append("")
        L.append("| | |")
        L.append("|:--|:--|")
        for chave, texto in cfg["capacidades"]:
            L.append(f"| `{chave}` | {celula(texto)} |")
        L.append("")

    L.append("## ~/projetos")
    L.append("")
    if cfg.get("nota_projetos"):
        L.append(cfg["nota_projetos"])
        L.append("")
    for titulo, projetos in grupos:
        L.append(f"### {titulo}")
        L.append("")
        L.append("| projeto | o que é | stack | atualizado |")
        L.append("|:--|:--|:--|:--|")
        for p in projetos:
            nome = f'[**{celula(p["nome"])}**]({p["url"]})'
            if p["nome"] != p["id"]:
                nome += f'<br><sub><code>{p["id"]}</code></sub>'
            desc = celula(p["descricao"]) or "<sub>sem descrição</sub>"
            if p["site"]:
                desc += f' <a href="{p["site"]}">demo</a>'
            stack = " · ".join(p["stack"]) or "-"
            extra = f'<br><sub>{p["estrelas"]} estrela{"s" if p["estrelas"] != 1 else ""}</sub>' if p["estrelas"] else ""
            L.append(f"| {nome} | {desc} | {stack} | {mes_ano(p['push'])}{extra} |")
        L.append("")

    if cfg.get("fora_do_github"):
        L.append("### Fora do GitHub ou privados")
        L.append("")
        L.append("| projeto | o que é | stack |")
        L.append("|:--|:--|:--|")
        for f in cfg["fora_do_github"]:
            nome = f'[**{celula(f["nome"])}**]({f["url"]})' if f.get("url") else f'**{celula(f["nome"])}**'
            L.append(f'| {nome} | {celula(f.get("descricao", ""))} | {celula(f.get("stack", "-"))} |')
        L.append("")

    L.append("## ~/stack")
    L.append("")
    if tem_linguagens:
        L.append('<img src="assets/linguagens.svg" width="100%" alt="Linguagens nos repositórios públicos">')
        L.append("")
    if cfg.get("ferramentas"):
        L.append(" ".join(f"`{f}`" for f in cfg["ferramentas"]))
        L.append("")

    contato = {k: v for k, v in cfg.get("contato", {}).items() if v}
    if contato:
        L.append("## ~/contato")
        L.append("")
        rotulos = {"email": "email", "linkedin": "linkedin", "site": "site"}
        for k, v in contato.items():
            link = f"mailto:{v}" if k == "email" else v
            mostra = v.replace("https://", "").replace("http://", "").rstrip("/")
            L.append(f"`{rotulos.get(k, k)}` [{mostra}]({link})  ")
        L.append("")

    L.append("---")
    L.append("")
    L.append("<sub>Página gerada a partir de <code>perfil.json</code> e dos repositórios públicos. "
             "Novos projetos entram aqui sozinhos.</sub>")
    L.append("")
    return "\n".join(L)


def main():
    cfg = json.loads((RAIZ / "perfil.json").read_text(encoding="utf-8"))
    repos = buscar_repos(cfg)
    projetos = [info_repo(cfg, r) for r in repos]
    linguagens = somar_linguagens(repos)
    grupos = agrupar(cfg, projetos)
    ordem_terminal = [p for _, ps in grupos for p in ps]

    (RAIZ / "assets").mkdir(exist_ok=True)
    (RAIZ / "assets" / "terminal.svg").write_text(svg_terminal(cfg, ordem_terminal, linguagens), encoding="utf-8", newline="\n")
    if linguagens:
        (RAIZ / "assets" / "linguagens.svg").write_text(svg_linguagens(linguagens), encoding="utf-8", newline="\n")
    (RAIZ / "README.md").write_text(gerar_readme(cfg, grupos, bool(linguagens)), encoding="utf-8", newline="\n")
    print(f"{len(projetos)} repositórios, {len(linguagens)} linguagens")


if __name__ == "__main__":
    main()
