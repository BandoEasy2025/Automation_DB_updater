"""
Configuration of grant sources by priority for the crawler
"""

# Priority 1: Regional government sources
REGIONAL_SOURCES = [
    {
        "name": "Valle D'Aosta",
        "url": "https://www.regione.vda.it/amministrazione/bandi/default_i.aspx",
        "scraper_type": "regional"
    },
    {
        "name": "Piemonte",
        "url": "https://bandi.regione.piemonte.it/contributi-finanziamenti",
        "scraper_type": "regional"
    },
    {
        "name": "Lombardia",
        "url": "https://www.bandi.regione.lombardia.it/",
        "scraper_type": "regional"
    },
    {
        "name": "Sardegna",
        "url": "https://www.regione.sardegna.it/servizi/cittadino/bandi/",
        "scraper_type": "regional"
    },
    {
        "name": "Sicilia",
        "url": "https://www.regione.sicilia.it/la-regione-informa/bandi",
        "scraper_type": "regional"
    },
    {
        "name": "Calabria",
        "url": "https://www.regione.calabria.it/website/organizzazione/dipartimento3/subsite/bandiegare/",
        "scraper_type": "regional"
    },
    {
        "name": "Basilicata",
        "url": "https://www.regione.basilicata.it/giunta/site/giunta/department.jsp?dep=100435&area=3039402",
        "scraper_type": "regional"
    },
    {
        "name": "Puglia",
        "url": "https://www.regione.puglia.it/web/bandi-e-avvisi",
        "scraper_type": "regional"
    },
    {
        "name": "Campania",
        "url": "http://portalebandi.regione.campania.it/",
        "scraper_type": "regional"
    },
    {
        "name": "Molise",
        "url": "https://www.regione.molise.it/flex/cm/pages/ServeBLOB.php/L/IT/IDPagina/15952",
        "scraper_type": "regional"
    },
    {
        "name": "Abruzzo",
        "url": "https://www.regione.abruzzo.it/content/bandi-di-gara-aperti",
        "scraper_type": "regional"
    },
    {
        "name": "Lazio",
        "url": "https://www.regione.lazio.it/bandi-e-concorsi",
        "scraper_type": "regional"
    },
    {
        "name": "Umbria",
        "url": "https://www.regione.umbria.it/la-regione/bandi",
        "scraper_type": "regional"
    },
    {
        "name": "Marche",
        "url": "https://www.regione.marche.it/Entra-in-Regione/Bandi",
        "scraper_type": "regional"
    },
    {
        "name": "Toscana",
        "url": "https://www.regione.toscana.it/bandi-aperti",
        "scraper_type": "regional"
    },
    {
        "name": "Emilia-Romagna",
        "url": "https://bandi.regione.emilia-romagna.it/",
        "scraper_type": "regional"
    },
    {
        "name": "Liguria",
        "url": "https://www.regione.liguria.it/bandi-e-avvisi/contributi.html",
        "scraper_type": "regional"
    },
    {
        "name": "Friuli-Venezia Giulia",
        "url": "https://www.regione.fvg.it/rafvg/cms/RAFVG/MODULI/bandi_avvisi/",
        "scraper_type": "regional"
    },
    {
        "name": "Veneto",
        "url": "https://bandi.regione.veneto.it/Public/Elenco?Tipo=1",
        "scraper_type": "regional"
    },
    {
        "name": "Provincia Autonoma di Trento",
        "url": "https://www.provincia.tn.it/Servizi/Bandi-Aperti",
        "scraper_type": "regional"
    }
]

# Priority 2: Chamber of commerce websites
CHAMBER_SOURCES = [
    {
        "name": "Camera di Commercio di Torino",
        "url": "https://www.to.camcom.it/bandi",
        "scraper_type": "chamber"
    },
    {
        "name": "Camera di Commercio Arezzo-Siena",
        "url": "https://www.as.camcom.it/bandi-e-contributi",
        "scraper_type": "chamber"
    },
    {
        "name": "Camera di Commercio Ferrara-Ravenna",
        "url": "https://www.ra.camcom.gov.it/attivita-promozionali/contributi",
        "scraper_type": "chamber"
    },
    {
        "name": "Camera di Commercio di Pistoia-Prato",
        "url": "https://www.ptpo.camcom.it/bandi-contributi/",
        "scraper_type": "chamber"
    },
    {
        "name": "Camera di Commercio di Cosenza",
        "url": "https://www.cs.camcom.gov.it/it/content/service/bandi-e-contributi",
        "scraper_type": "chamber"
    },
    {
        "name": "Camera di Commercio di Brescia",
        "url": "https://www.bs.camcom.it/contributi",
        "scraper_type": "chamber"
    },
    {
        "name": "Camera di Commercio della Maremma e del Tirreno",
        "url": "https://www.lg.camcom.it/pagina2037_bandi-per-contributi-alle-imprese.html",
        "scraper_type": "chamber"
    },
    {
        "name": "Camera di Commercio di Gran Sasso d'Italia",
        "url": "https://www.cameragransasso.camcom.it/bandi",
        "scraper_type": "chamber"
    },
    {
        "name": "Camera di Commercio di Roma",
        "url": "https://www.rm.camcom.it/pagina122_bandi-e-avvisi.html",
        "scraper_type": "chamber"
    },
    {
        "name": "Camera di Commercio di Firenze",
        "url": "https://www.fi.camcom.gov.it/bandi",
        "scraper_type": "chamber"
    },
    {
        "name": "Camera di Commercio di Modena",
        "url": "https://www.mo.camcom.it/promozione/contributi-camerali",
        "scraper_type": "chamber"
    },
    {
        "name": "Camera di Commercio di Genova",
        "url": "https://www.ge.camcom.it/bandi-e-contributi",
        "scraper_type": "chamber"
    },
    {
        "name": "Camera di Commercio Venezia-Giulia",
        "url": "https://www.vg.camcom.it/bandi",
        "scraper_type": "chamber"
    },
    {
        "name": "Camera di Commercio di Vicenza",
        "url": "https://www.vi.camcom.it/it/bandi-e-contributi",
        "scraper_type": "chamber"
    },
    {
        "name": "Camera di Commercio di Trento",
        "url": "https://www.tn.camcom.it/content/bandi-e-contributi",
        "scraper_type": "chamber"
    },
    {
        "name": "Camera di Commercio di Milano Monza Brianza Lodi",
        "url": "https://www.milomb.camcom.it/bandi",
        "scraper_type": "chamber"
    }
]

# Priority 3: National sources
NATIONAL_SOURCES = [
    {
        "name": "Gazzetta Ufficiale",
        "url": "https://www.gazzettaufficiale.it/",
        "scraper_type": "national"
    },
    {
        "name": "Invitalia",
        "url": "https://www.invitalia.it/cosa-facciamo/rafforziamo-le-imprese/tutti-gli-incentivi",
        "scraper_type": "national"
    },
    {
        "name": "Ministero delle Imprese e del Made in Italy",
        "url": "https://www.mise.gov.it/it/incentivi",
        "scraper_type": "national"
    },
    {
        "name": "MISE",
        "url": "https://www.mise.gov.it/it/incentivi/agevolazioni",
        "scraper_type": "national"
    },
    {
        "name": "SIMEST",
        "url": "https://www.simest.it/finanziamenti-pnrr/finanziamenti-agevolati-pnrr-nextgenerationeu",
        "scraper_type": "national"
    }
]

# Priority 4: European Union sources
EU_SOURCES = [
    {
        "name": "European Union Grants",
        "url": "https://ec.europa.eu/info/funding-tenders/opportunities/portal/screen/home",
        "scraper_type": "eu"
    },
    {
        "name": "Europa Funding Portal",
        "url": "https://ec.europa.eu/info/funding-tenders",
        "scraper_type": "eu"
    }
]

# Complete source list in priority order
ALL_SOURCES = REGIONAL_SOURCES + CHAMBER_SOURCES + NATIONAL_SOURCES + EU_SOURCES