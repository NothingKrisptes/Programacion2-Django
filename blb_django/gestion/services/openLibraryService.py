import requests

class OpenLibraryError(Exception):
    pass

def fetchBookByTitle(nombreLibro):
    if not nombreLibro:
        raise OpenLibraryError("Ingrese el nombre del libro.")

    try:
        url = "https://openlibrary.org/search.json"
        params = {"q": nombreLibro, "lang": "es", "limit": 1}
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        docs = data.get("docs") or []
        if not docs:
            raise OpenLibraryError("No se encontró ningún libro con ese nombre en OpenLibrary.")

        libro = docs[0]
        workKey = libro.get("key")  # "/works/OLxxxxW"
        titulo = libro.get("title") or "Sin título"
        autorNombre = (libro.get("author_name") or ["Desconocido"])[0]
        anio = libro.get("first_publish_year")
        editorialNombre = (libro.get("publisher") or ["Desconocido"])[0]
        isbn = (libro.get("isbn") or [None])[0]

        paginas = 0
        descripcion = ""
        generos = []
        coverId = libro.get("cover_i")  # útil para Covers API

        # Consultar work para descripción/subjects
        if workKey:
            workUrl = f"https://openlibrary.org{workKey}.json"
            workResp = requests.get(workUrl, timeout=10)
            if workResp.ok:
                workData = workResp.json()

                desc = workData.get("description")
                if isinstance(desc, dict):
                    descripcion = desc.get("value", "") or ""
                elif isinstance(desc, str):
                    descripcion = desc

                if workData.get("subjects"):
                    generos = workData["subjects"][:3]

            # Ediciones para páginas/ISBN/editorial (como en Odoo)
            editionsUrl = f"https://openlibrary.org{workKey}/editions.json"
            edResp = requests.get(editionsUrl, timeout=10)
            if edResp.ok:
                edData = edResp.json()
                entries = edData.get("entries") or []
                if entries:
                    entry = entries[0]
                    paginas = entry.get("number_of_pages") or 0
                    isbn = (entry.get("isbn_10") or [None])[0] or isbn
                    editorialNombre = (entry.get("publishers") or [editorialNombre])[0] or editorialNombre

        # fechaPublicacion estilo "YYYY-01-01"
        fechaPublicacion = None
        if anio and str(anio).isdigit() and len(str(anio)) == 4:
            fechaPublicacion = f"{anio}-01-01"

        return {
            "titulo": titulo,
            "autorNombre": autorNombre,
            "editorialNombre": editorialNombre,
            "isbn": isbn or "No disponible",
            "paginas": paginas,
            "fechaPublicacion": fechaPublicacion,   # string ISO o None
            "descripcion": descripcion or "No hay descripción disponible.",
            "genero": ", ".join(generos) if generos else "Desconocido",
            "coverId": coverId,
        }

    except requests.RequestException as e:
        raise OpenLibraryError(f"Error al conectar con OpenLibrary: {e}")
