
import bibtexparser
import html
import re
from pathlib import Path


# --------------------------------------------------
# 1. Chemins des fichiers
# --------------------------------------------------

ROOT = Path(__file__).resolve().parent.parent

BIB_FILE = ROOT / "publications" / "cv.bib"
HTML_FILE = ROOT / "index.html"

START_MARKER = "<!-- PUBLICATIONS:START -->"
END_MARKER = "<!-- PUBLICATIONS:END -->"


# --------------------------------------------------
# 2. Nettoyage des données BibTeX
# --------------------------------------------------

def clean_text(text):
    """Nettoie les caractères et commandes LaTeX simples."""

    text = str(text)

    # Décodage des entités HTML, y compris imbriquées
    for _ in range(3):
        text = html.unescape(text)

    # Suppression des accolades BibTeX
    text = text.replace("{", "").replace("}", "")

    # Quelques substitutions LaTeX
    text = text.replace(r"\&", "&")
    text = text.replace("--", "–")
    text = text.replace("~", " ")

    return text.strip()



def format_authors(author_string):
    authors = author_string.split(" and ")
    formatted_authors = []

    for author in authors:
        # Détecter d'abord la commande LaTeX
        match = re.search(r"\\textbf\s*\{(.*?)\}", author)

        if match:
            name = clean_text(match.group(1))
            formatted_author = (
                author[:match.start()]
                + "<strong>" + html.escape(name) + "</strong>"
                + author[match.end():]
            )
        else:
            formatted_author = html.escape(clean_text(author))

        formatted_authors.append(formatted_author)

    return ", ".join(formatted_authors)



# --------------------------------------------------
# 3. Détermination du type de publication
# --------------------------------------------------

def get_publication_type(entry):

    entry_type = entry.get("ENTRYTYPE", "").lower()

    publisher = entry.get("publisher", "").lower()
    note = entry.get("note", "").lower()

    if "biorxiv" in publisher or "preprint" in note:
        return "Prépublication"

    if "poster" in note:
        return "Poster scientifique"

    if entry_type == "inproceedings":
        return "Communication scientifique"

    if entry_type == "article":
        return "Article scientifique"

    return "Autre contribution"


# --------------------------------------------------
# 4. Création du HTML pour une publication
# --------------------------------------------------

def create_publication_html(entry):

    title = clean_text(entry.get("title", "Titre inconnu"))
    authors = format_authors(entry.get("author", ""))
    year = clean_text(entry.get("year", ""))

    journal = clean_text(
        entry.get("journal")
        or entry.get("booktitle")
        or entry.get("publisher")
        or ""
    )

    note = clean_text(entry.get("note", ""))
    pub_type = get_publication_type(entry)

    doi = clean_text(entry.get("doi", ""))
    url = clean_text(entry.get("url", ""))

    # Création du lien DOI ou URL
    link = ""

    if doi:
        doi_url = "https://doi.org/" + doi

        link = (
            f'<a href="{html.escape(doi_url, quote=True)}" '
            f'target="_blank" rel="noopener noreferrer">'
            f'DOI</a>'
        )

    elif url:
        link = (
            f'<a href="{html.escape(url, quote=True)}" '
            f'target="_blank" rel="noopener noreferrer">'
            f'Lien</a>'
        )

    # Construction du bloc HTML
    result = f"""
    <article class="publication-item">

        <span class="publication-year">
            {html.escape(year)}
        </span>

        <div class="publication-content">

            <h3>{html.escape(title)}</h3>

            <p class="publication-authors">
                {authors}
            </p>

            <p class="publication-details">
                <span>{html.escape(journal)}</span>
                <span class="publication-type">
                    {html.escape(pub_type)}
                </span>
            </p>

            {f'<p class="publication-note">{html.escape(note)}</p>' if note else ''}

            {f'<p class="publication-link">{link}</p>' if link else ''}

        </div>

    </article>
    """

    return result


# --------------------------------------------------
# 5. Lecture et classement du fichier BibTeX
# --------------------------------------------------

def generate_bibliography():

    with open(BIB_FILE, encoding="utf-8") as file:
        bib_database = bibtexparser.load(file)

    entries = bib_database.entries

    # Classement chronologique décroissant
    entries.sort(
        key=lambda entry: int(
            re.search(r"\d{4}", entry.get("year", "0")).group()
            if re.search(r"\d{4}", entry.get("year", ""))
            else 0
        ),
        reverse=True
    )

    publications_html = "\n".join(
        create_publication_html(entry)
        for entry in entries
    )

    # --------------------------------------------------
    # 6. Insertion dans index.html
    # --------------------------------------------------

    with open(HTML_FILE, encoding="utf-8") as file:
        page = file.read()

    if START_MARKER not in page or END_MARKER not in page:
        raise ValueError(
            "Les marqueurs PUBLICATIONS sont absents de index.html."
        )

    start = page.index(START_MARKER) + len(START_MARKER)
    end = page.index(END_MARKER)

    page = (
        page[:start]
        + "\n"
        + publications_html
        + "\n"
        + page[end:]
    )

    with open(HTML_FILE, "w", encoding="utf-8") as file:
        file.write(page)

    print(f"{len(entries)} références ajoutées à index.html !")


# --------------------------------------------------
# 7. Exécution du programme
# --------------------------------------------------

if __name__ == "__main__":
    generate_bibliography()
