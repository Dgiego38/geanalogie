import os
import codecs


# Ouvre le fichier en mode lecture
with codecs.open("/mnt/chromeos/MyFiles/Downloads/genea1.ged", 'r', encoding='utf-8',
                 errors='ignore') as filin:
    lignes = filin.readlines()
    x=0
    for ligne in lignes:
         print(ligne)
         x=x+1
#        print(x)
         if x>100:
              break
        

