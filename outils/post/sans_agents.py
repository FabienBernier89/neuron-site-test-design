"""Page Actualités du blog : phrases sur l'« IA agentique » retirées (décision de Fabien du 2026-10-16).

Corrext n'a pas d'agents IA. Deux actualités reprises de la V1 évoquaient une vision « agentique » ; ce
post-traitement retire ces deux passages, sans rien toucher d'autre. Si la V1 change et qu'un passage attendu
manque, le build s'arrête plutôt que de publier la page sans le vérifier.
"""
PAGE = "ressources/blog/actualites/"
RETIRES = (
    " Pendant son pitch, Paula a également présenté notre vision de l’avenir de <strong>l’IA agentique dans les "
    "opérations juridiques</strong>, où des outils intelligents s’intègrent naturellement aux flux de travail juridiques du quotidien.",
    "<p>Pour l’avenir, nous sommes convaincus que <strong>la traduction par IA agentique</strong> redéfinira le "
    "libre-service dans les contextes juridiques, en le rendant non seulement réalisable, mais aussi véritablement "
    "intuitif et valorisant pour les professionnels du droit.</p>",
)


def traiter(html, page):
    if page != PAGE:
        return html
    for passage in RETIRES:
        if html.count(passage) != 1:
            raise ValueError(f"{PAGE} : passage « agentique » de la V1 introuvable ou en double : {passage[:60]}")
        html = html.replace(passage, "", 1)
    return html
