# -*- coding: utf-8 -*-


import re, urllib2, time, os, json, unicodedata, base64, subprocess
from xml.dom import minidom
from core import *

### configuration

cheminDossierFragments = "fragments"
cheminDossierImages = "images"
cheminDossierInfos = "infos"
cheminDossierImageMagick = "ImageMagick"
cheminJavaScript = "core.js"

refererGoogleArtProject = "http://www.googleartproject.com/"
dureeSleep = 0.5

separateur = "\t"

### contenu d'une page Web

def getContenuUrl(url, referer = ""):
    time.sleep(dureeSleep)

    requete = urllib2.Request(url)
    if referer:
        requete.add_header("Referer", referer)

    print "(%s)" % url
    
    return urllib2.urlopen(requete).read()

### URL d'un fragment d'image, décryptage d'un fragment d'image







def getUrlFragment(urlImage, x, y, zoom, timestamp):
    return getUrlFragmentTrue(urlImage, x, y, zoom, timestamp)


def decrypterFragmentTrue(t):	
	return m_oc(m_Wc(m_Uc(),t))

def decrypterFragment(contenuFragment):
    arrayFragment = [ord(char) & 0xFF for char in contenuFragment]
    base64Fragment = decrypterFragmentTrue(arrayFragment)
    return base64.b64decode(base64Fragment)

### infos sur un tableau (peintre, titre, date...)

def getInfosTableau(urlPageTableau):
    regexJsonTableau = re.compile("""var CURRENT_ARTWORK = new ap.Artwork\((.+)\);""")

    infosTableau = {}

    contenuPageTableau = getContenuUrl(urlPageTableau, refererGoogleArtProject)
    
    jsonTableau = json.loads(re.findall(regexJsonTableau, contenuPageTableau)[0])

    infosTableau["urlImage"] = str(jsonTableau["aggregation_image_url"])
    if infosTableau["urlImage"][:5] <> "http:":
        infosTableau["urlImage"] = "http:" + infosTableau["urlImage"]

    infosTableau["peintre"] = jsonTableau["artist_display_name"]
    
    infosTableau["titre"] = jsonTableau["title"]

    try:
        infosTableau["date"] = str(jsonTableau["pretty_display_date"])
    except:
        infosTableau["date"] = ""

    try:
        infosTableau["titre original"] = jsonTableau["facets"]["Original Title"][0]
    except:
        infosTableau["titre original"] = ""

    try:
        infosTableau["autre titre"] = jsonTableau["facets"]["Non-English title"][0]
    except:
        infosTableau["autre titre"] = ""
    
    try:
        infosTableau["mouvements"] = jsonTableau["facets"]["Style"][0]
    except:
        infosTableau["mouvements"] = ""
    
    try:
        infosTableau["techniques"] = jsonTableau["facets"]["Medium"][0]
    except:
        infosTableau["techniques"] = ""
    
    return infosTableau

### téléchargements des fragments d'image

def getInfosFragments(urlImage, zoom):
    docXml = minidom.parse(urllib2.urlopen(urlImage + "=g"))
    
    largeurFragment = int(docXml.firstChild.attributes["tile_width"].value)
    hauteurFragment = int(docXml.firstChild.attributes["tile_height"].value)
    
    zoomMax = int(docXml.firstChild.attributes["full_pyramid_depth"].value) - 1

    if zoom > zoomMax:
        zoom = zoomMax
    
    xMax = int(docXml.getElementsByTagName("pyramid_level")[zoom].attributes["num_tiles_x"].value)
    yMax = int(docXml.getElementsByTagName("pyramid_level")[zoom].attributes["num_tiles_y"].value)
    
    return zoom, xMax, yMax, largeurFragment, hauteurFragment

def telechargerFragment(urlImage, cheminFragment, x, y, zoom):
    timestamp = int(time.time())
    urlFragment = getUrlFragment(urlImage, x, y, zoom, timestamp)

    contenuFragment = getContenuUrl(urlFragment, refererGoogleArtProject)

    contenuFragment = decrypterFragment(contenuFragment)
    
    fichierFragment = open(cheminFragment, "wb")
    fichierFragment.write(contenuFragment)
    fichierFragment.close()

def telechargerTousFragments(urlImage, xMax, yMax, zoom):
    i = 0
    for y in range(yMax):
        for x in range(xMax):
            i = i+1
            
            cheminFragment = os.path.join(cheminDossierFragments, "fragment_%s.jpg" % format(i, "03d"))
            
            telechargerFragment(urlImage, cheminFragment, x, y, zoom)

### reconstitution de l'image à partir des fragments

def reconstituerImage(nomFichierImage, xMax, yMax, largeurFragment, hauteurFragment):
    #commandeAssembler = (os.path.join(cheminDossierImageMagick, "montage.exe")
    #                     + " " + os.path.join(cheminDossierFragments, "fragment_[0-9]*.jpg")
    #                     + " -quality 100"
    #                     + " -tile " + str(xMax) + "x" + str(yMax)
    #                     + " -geometry " + str(largeurFragment) + "x" + str(hauteurFragment)
    #                     + " " + os.path.join(cheminDossierImages, nomFichierImage))
    commandeAssembler="montage " + os.path.join(cheminDossierFragments, "fragment_[0-9]*.jpg") + " -quality 100"+" -tile " + str(xMax) + "x" + str(yMax)+" -geometry " + str(largeurFragment) + "x" + str(hauteurFragment)+ " " + os.path.join(cheminDossierImages, nomFichierImage)
    
    #commandeRogner = (os.path.join(cheminDossierImageMagick, "mogrify.exe")
    #                  + " -quality 100"
    #                  + " -trim"
    #                  + " -fuzz 10%"
    #                  + " " + os.path.join(cheminDossierImages, nomFichierImage))
    #
    commandeRogner = "mogrify "+ " -quality 100"+ " -trim"+ " -fuzz 10%" + " " + os.path.join(cheminDossierImages, nomFichierImage)
    p1 = subprocess.Popen(commandeAssembler, shell=True)#, creationflags=0x08000000)
    p1.communicate()
    
    p2 = subprocess.Popen(commandeRogner, shell=True)#, creationflags=0x08000000)
    p2.communicate()

### liste des tableaux d'un peintre

def getUrlPagesTableaux(idPeintre):
    listeUrlPagesTableaux = []
    
    urlJsonTableaux = "http://www.googleartproject.com/api/int/gap2/artwork/?canonical_artist=%i&limit=500&offset=0&format=json" % idPeintre
    jsonTableau = json.loads(getContenuUrl(urlJsonTableaux, refererGoogleArtProject))

    for tableau in jsonTableau["objects"]:
        listeUrlPagesTableaux.append("http://www.googleartproject.com" + str(tableau["absolute_url"]))

    return listeUrlPagesTableaux

### normalisation d'un chaîne de caractères

def normaliserChaine(chaine):
    # encodage UTF-8
    try:
        chaine = unicode(chaine)
    except:
        chaine = unicode(chaine, "iso-8859-1")
    
    # suppression des accents
    chaine = unicodedata.normalize("NFKD", chaine)

    # encodage ASCII
    chaine = chaine.encode("ASCII", "ignore")

    return chaine

def normaliserNomFichier(chaine):
    chaine = normaliserChaine(chaine)
    
    # caractère non alpha-numérique => "_"
    chaine = re.sub("[^0-9a-zA-Z\.\-]", "_", chaine)

    return chaine

### téléchargement des images et infos

def nettoyerDossier(cheminDossier):
    for nomFichier in os.listdir(cheminDossier):
        cheminFichier = os.path.join(cheminDossier, nomFichier)
        if os.path.isfile(cheminFichier):
            os.remove(cheminFichier)

def telechargerTableau(urlImage, nomFichierImage, zoom):
    zoom, xMax, yMax, largeurFragment, hauteurFragment = getInfosFragments(urlImage, zoom)
    
    nettoyerDossier(cheminDossierFragments) # nettoyage du dossier des fragments
    
    telechargerTousFragments(urlImage, xMax, yMax, zoom)
    reconstituerImage(nomFichierImage, xMax, yMax, largeurFragment, hauteurFragment)

def telechargerTableauxPeintre(nomPeintre, idPeintre, zoom):
    listeChamps = ["image", "peintre", "titre", "date", "titre original", "autre titre", "mouvements", "techniques"]
    
    fichierInfos = open(os.path.join(cheminDossierInfos, normaliserNomFichier(nomPeintre) + ".csv"), "w")
    fichierInfos.write(separateur.join(listeChamps) + "\n")

    listeUrlPagesTableaux = getUrlPagesTableaux(idPeintre)

    print "### %s : %i tableaux" % (nomPeintre, len(listeUrlPagesTableaux))

    i = 0
    for urlPageTableau in listeUrlPagesTableaux:
        i = i+1
        
        print "# %s, tableau %i/%i : %s" % (nomPeintre, i, len(listeUrlPagesTableaux), urlPageTableau)
        
        infosTableau = getInfosTableau(urlPageTableau)
        urlImage = infosTableau["urlImage"]
        
        nomFichierImage = normaliserNomFichier(nomPeintre) + "-" + format(i, "03d") + ".jpg"

        telechargerTableau(urlImage, nomFichierImage, zoom)

        infosTableau["image"] = nomFichierImage
        fichierInfos.write(separateur.join([normaliserChaine(infosTableau[champ]) for champ in listeChamps]) + "\n")

    fichierInfos.close()

### fonctions principales

def telechargerOeuvre(urlOeuvre, nomFichierImage, zoom):
    contenuPageOeuvre = getContenuUrl(urlOeuvre, refererGoogleArtProject)
    
    regexUrlImage = re.compile("""data-image-url=\"([^\"]+)\"""")
    urlImage = re.findall(regexUrlImage, contenuPageOeuvre)[0]
    if urlImage.find("http:") == -1 : ###### add this code
    	urlImage = "http:"+ urlImage ##### add this code
    telechargerTableau(urlImage, normaliserNomFichier(nomFichierImage), zoom)

def telechargerArtiste(urlArtiste, zoom):
    contenuPageArtiste = getContenuUrl(urlArtiste, refererGoogleArtProject)
    
    regexNomArtiste = re.compile("""data-artist-name=\"([^\"]+)\"""")
    regexIdArtiste = re.compile("""data-artist-id=\"([^\"]+)\"""")
    
    nomArtiste = re.findall(regexNomArtiste, contenuPageArtiste)[0]
    idArtiste = int(re.findall(regexIdArtiste, contenuPageArtiste)[0])

    nomArtiste
    
    telechargerTableauxPeintre(nomArtiste, idArtiste, zoom)

### exécution du script
timeout=20
a=[]
with open("images.txt","r") as f:
  for line in f:
   a.append(line)
jjj=[]
for i in a:
  if i[0]=="#":
   continue
  if len(i)<25:
   if i.split(" ")[0]=="timeout":
	try:
		timeout=int(i.split(" ")[1])
	except:
		pass
   continue
  jjj.append(	[	i.split(" ")[0],	i.split(" ")[1],	int(i.split(" ")[2])]	)
for i in jjj:
	telechargerOeuvre(i[0], i[1], i[2])
	time.sleep(timeout)
















