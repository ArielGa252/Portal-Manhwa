# baixar_todos_capitulos.py
# Use apenas em conteúdos que você tem autorização para baixar/usar.
#
# COMO USAR:
#
# 1) Feche o Chrome.
#
# 2) Abra o Chrome pelo CMD com depuração remota:
#    "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir="C:\ChromeDev"
#
# 3) No Chrome que abriu, entre no site e faça login.
#
# 4) Coloque este arquivo dentro da pasta do projeto, junto com:
#    - mangas_resultado.json
#    OU a pasta data/ com mangas-1.json, mangas-2.json...
#
# 5) Instale as dependências:
#    pip install playwright requests
#    playwright install chromium
#
# 6) Rode:
#    python baixar_todos_capitulos.py
#
# RESULTADO:
# - As imagens serão salvas em:
#   imagens/ID_DO_MANHWA/capitulo-XX/001.jpg
#
# - O arquivo gerado será:
#   capitulos-imagens.json
#
# Depois esse JSON poderá ser usado no Portal Manhwa.

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from pathlib import Path
from urllib.parse import urlparse
import json
import re
import time
import requests

PASTA_IMAGENS = Path("imagens")
ARQUIVO_SAIDA = Path("capitulos-imagens.json")
CDP_URL = "http://127.0.0.1:9222"
PAUSA_ENTRE_CAPITULOS = 1.5
SOMENTE_COMIC_ID = None
LIMITE_CAPITULOS_POR_MANHWA = None


def carregar_json(caminho: Path):
    if not caminho.exists():
        return None
    with caminho.open("r", encoding="utf-8") as f:
        return json.load(f)


def normalizar_url(url: str) -> str:
    return str(url or "").rstrip("/")


def extrair_id_comic(url: str) -> str:
    match = re.search(r"/comics/(\d+)", url or "")
    if match:
        return match.group(1)
    return re.sub(r"\W+", "_", url or "sem_id").strip("_")


def montar_url_capitulo(url_manhwa: str, numero: int) -> str:
    return f"{normalizar_url(url_manhwa)}/ler/capitulo-{numero:02d}"


def carregar_lista_mangas():
    arquivo_principal = carregar_json(Path("mangas_resultado.json"))
    if isinstance(arquivo_principal, list):
        return arquivo_principal

    data_dir = Path("data")
    partes = sorted(data_dir.glob("mangas-*.json"))
    mangas = []

    for parte in partes:
        dados = carregar_json(parte)
        if isinstance(dados, list):
            mangas.extend(dados)

    if mangas:
        return mangas

    raise FileNotFoundError("Não encontrei mangas_resultado.json nem arquivos data/mangas-*.json")


def lista_capitulos(item):
    if isinstance(item.get("capitulos"), list):
        capitulos = []
        for cap in item["capitulos"]:
            if isinstance(cap, int):
                capitulos.append(cap)
            elif isinstance(cap, str):
                num = re.sub(r"\D+", "", cap)
                if num:
                    capitulos.append(int(num))
            elif isinstance(cap, dict):
                num = cap.get("numero") or cap.get("capitulo") or cap.get("chapter")
                if num:
                    capitulos.append(int(num))
        return sorted(set(capitulos))

    total = int(item.get("total") or 0)
    if total > 0:
        return list(range(1, total + 1))

    return []


def rolar_ate_carregar_tudo(page):
    ultimo_total = -1
    repeticoes_sem_mudar = 0

    for _ in range(60):
        total = page.locator("#pages img, img.slice, .slice img").count()

        if total == ultimo_total:
            repeticoes_sem_mudar += 1
        else:
            repeticoes_sem_mudar = 0

        if repeticoes_sem_mudar >= 4:
            break

        ultimo_total = total
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(900)

    page.evaluate("window.scrollTo(0, 0)")
    page.wait_for_timeout(500)


def descobrir_imagens(page):
    seletores = ["#pages img", "img.slice", ".slice img", "#reader img", "main img"]

    for seletor in seletores:
        try:
            elementos = page.query_selector_all(seletor)
            srcs = []
            for img in elementos:
                src = img.get_attribute("src")
                if src and src not in srcs:
                    srcs.append(src)
            if srcs:
                return srcs
        except Exception:
            pass

    return []


def baixar_blob(page, src: str, destino: Path):
    data = page.evaluate(
        """
        async (url) => {
            const res = await fetch(url);
            const blob = await res.blob();
            const buffer = await blob.arrayBuffer();
            return Array.from(new Uint8Array(buffer));
        }
        """,
        src,
    )
    destino.write_bytes(bytes(data))


def baixar_url_normal(src: str, destino: Path):
    headers = {"User-Agent": "Mozilla/5.0", "Referer": "https://blackoutcomics.com/"}
    r = requests.get(src, headers=headers, timeout=60)
    r.raise_for_status()
    destino.write_bytes(r.content)


def extensao_da_imagem(src: str) -> str:
    try:
        path = urlparse(src).path.lower()
    except Exception:
        return ".jpg"

    for ext in [".webp", ".png", ".jpg", ".jpeg"]:
        if path.endswith(ext):
            return ".jpg" if ext == ".jpeg" else ext

    return ".jpg"


def baixar_imagens_do_capitulo(page, url_capitulo: str, pasta_capitulo: Path):
    print(f"\n➡ Abrindo: {url_capitulo}")
    page.goto(url_capitulo, wait_until="domcontentloaded", timeout=90000)

    try:
        page.wait_for_load_state("networkidle", timeout=45000)
    except PlaywrightTimeoutError:
        pass

    try:
        page.wait_for_selector("#pages img, img.slice, .slice img, main img", timeout=60000)
    except PlaywrightTimeoutError:
        print("⚠ Não encontrou imagens nesse capítulo.")
        return []

    rolar_ate_carregar_tudo(page)
    srcs = descobrir_imagens(page)

    if not srcs:
        print("⚠ Nenhuma imagem encontrada.")
        return []

    pasta_capitulo.mkdir(parents=True, exist_ok=True)
    caminhos_relativos = []
    print(f"✔ Imagens encontradas: {len(srcs)}")

    for i, src in enumerate(srcs, start=1):
        ext = extensao_da_imagem(src)
        destino = pasta_capitulo / f"{i:03d}{ext}"

        if destino.exists() and destino.stat().st_size > 0:
            print(f"  ↪ Já existe: {destino}")
        else:
            try:
                if src.startswith("blob:"):
                    baixar_blob(page, src, destino)
                else:
                    baixar_url_normal(src, destino)
                print(f"  ✔ Baixada: {destino}")
            except Exception as e:
                print(f"  ❌ Erro na imagem {i}: {e}")
                continue

        caminhos_relativos.append(str(destino).replace("\\", "/"))

    return caminhos_relativos


def salvar_json(resultado):
    with ARQUIVO_SAIDA.open("w", encoding="utf-8") as f:
        json.dump(resultado, f, ensure_ascii=False, indent=2)


def main():
    PASTA_IMAGENS.mkdir(exist_ok=True)
    mangas = carregar_lista_mangas()
    print(f"✔ Manhwas carregados: {len(mangas)}")

    resultado = {}
    if ARQUIVO_SAIDA.exists():
        try:
            resultado = carregar_json(ARQUIVO_SAIDA) or {}
            print(f"✔ Continuando arquivo existente: {ARQUIVO_SAIDA}")
        except Exception:
            resultado = {}

    with sync_playwright() as pw:
        browser = pw.chromium.connect_over_cdp(CDP_URL)

        if not browser.contexts:
            print("❌ Nenhum contexto encontrado no Chrome. Abra o Chrome com --remote-debugging-port=9222")
            return

        context = browser.contexts[0]
        page = None

        for aba in context.pages:
            if "blackoutcomics.com" in aba.url:
                page = aba
                break

        if page is None:
            page = context.new_page()

        page.bring_to_front()

        for idx, manga in enumerate(mangas, start=1):
            url_manhwa = normalizar_url(manga.get("url"))
            if not url_manhwa:
                continue

            comic_id = extrair_id_comic(url_manhwa)

            if SOMENTE_COMIC_ID and str(SOMENTE_COMIC_ID) != str(comic_id):
                continue

            capitulos = lista_capitulos(manga)
            if LIMITE_CAPITULOS_POR_MANHWA:
                capitulos = capitulos[:LIMITE_CAPITULOS_POR_MANHWA]

            print("\n" + "=" * 80)
            print(f"[{idx}/{len(mangas)}] {manga.get('nome', 'Sem nome')} | ID {comic_id}")
            print(f"Capítulos: {len(capitulos)}")
            print("=" * 80)

            if url_manhwa not in resultado:
                resultado[url_manhwa] = {}

            for numero in capitulos:
                numero_str = str(numero)

                if numero_str in resultado[url_manhwa] and resultado[url_manhwa][numero_str]:
                    print(f"↪ Capítulo {numero} já está no JSON. Pulando.")
                    continue

                url_capitulo = montar_url_capitulo(url_manhwa, int(numero))
                pasta_capitulo = PASTA_IMAGENS / comic_id / f"capitulo-{int(numero):02d}"

                try:
                    imagens = baixar_imagens_do_capitulo(page, url_capitulo, pasta_capitulo)

                    if imagens:
                        resultado[url_manhwa][numero_str] = imagens
                        salvar_json(resultado)
                        print(f"✔ Capítulo {numero} salvo no JSON.")
                    else:
                        print(f"⚠ Capítulo {numero} sem imagens salvas.")

                except Exception as e:
                    print(f"❌ Erro no capítulo {numero}: {e}")

                time.sleep(PAUSA_ENTRE_CAPITULOS)

    salvar_json(resultado)
    print("\n✔ FINALIZADO")
    print(f"✔ Imagens em: {PASTA_IMAGENS.resolve()}")
    print(f"✔ JSON em: {ARQUIVO_SAIDA.resolve()}")


if __name__ == "__main__":
    main()
