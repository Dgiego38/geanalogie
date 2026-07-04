from gedcom.element.individual import IndividualElement
from gedcom.parser import Parser
import easygui
import pandas as pd
from geopy.geocoders import Nominatim
import time
import csv
import pandas as pd
import os
import matplotlib.pyplot as plt

def copier_fichier(source: str, destination: str, gedcom_parser ):
    try:
        with open(source, 'r', encoding='utf-8-sig',errors='replace') as fichier_entree, open(destination, 'w', encoding='utf-8-sig',errors='replace') as fichier_sortie:
            for ligne in fichier_entree:
                fichier_sortie.write(ligne)
        print(f"Copie terminée : {source} -> {destination}")
    except FileNotFoundError:
        print("Erreur : Le fichier source n'existe pas.")
    except IOError as e:
        print(f"Erreur d'entrée/sortie : {e}")

# Fonction pour lire le fichier CSV de matching ADN

def lire_csv_matching_adn(csv_file):
    matching_adn = []
    with open(csv_file, mode='r', encoding='utf-8-sig') as file:
        reader = csv.DictReader(file)
        for row in reader:
            matching_adn.append(row)
    
    return matching_adn


def ecrire_csv_fichier_sortie(source, destination, repertoire , gedcom_parser):
    
    try:
        with open(destination, 'w', encoding='utf-8-sig',errors='replace') as fichier_sortie:
            with open(source, 'r', encoding='utf-8-sig',errors='replace') as fichier_entree:
                
                for ligne in fichier_entree:
                    fichier_sortie.write(ligne)
                fichier_sortie.write("\n")    

                # Écrire les données de matching ADN
                #with os.scandir(repertoire) as entries:
                for entry in os.listdir(repertoire):
                    #   for entry in entries:
                    if entry.startswith("final_shared") and entry.endswith(".csv"):
                        print(repertoire + '/' + entry )
                        matching_adn = lire_csv_matching_adn(repertoire + '/' + entry)

                        person1 = None
                        person2 = None
                        i = 0
                        total_adn = 0

                        for match in matching_adn:
                            person1_before = person1
                            listegvn1 = match['Name'].split()
                            person1 = gedcom_parser.search_individual(gedcom_parser.get_root_child_elements(), listegvn1[1], listegvn1[0])
                            person2_before = person2
                            listegvn2 = match['Match Name'].split()
                            person2 = gedcom_parser.search_individual(gedcom_parser.get_root_child_elements(), listegvn2[1], listegvn2[0])
                                

                            if ((person1 != person1_before) or (person2 != person2_before)) and person1_before and person2_before:  
                                fichier_sortie.write(f"2 SHARED_CM {total_adn:.2f}\n")
                                pct_tot = ( total_adn / 7440 ) * 100 
                                fichier_sortie.write(f"2 SHARED_PCT {pct_tot:.2f}\n")
                                total = 0

                            if person1 != person1_before and person1:
                                fichier_sortie.write(f"0 {person1.get_pointer()} DNA\n")


                            if person2 != person2_before and person2:
                                fichier_sortie.write(f"1 MATCH {person2.get_pointer()}\n")
                                total_adn = 0 
                                
            
                            total_adn += float(match['Centimorgans'])
                                    
                            if person1 and person2:
                                fichier_sortie.write(f"2 SEGMENT\n")
                                fichier_sortie.write(f"3 CHROMOSOME {match['Chromosome']}\n")
                                fichier_sortie.write(f"3 START_POS {match['Start Location']}\n")
                                fichier_sortie.write(f"3 END_POS {match['End Location']}\n")
                                fichier_sortie.write(f"3 CM {match['Centimorgans']}\n")
                                pct_seg = ( float(match['Centimorgans']) / 7440 ) * 100 
                                fichier_sortie.write(f"3 PCT {pct_seg:.2f}\n")
                                fichier_sortie.write(f"3 SNP {match['SNPs']}\n")
                            

                if person1 and person2:
                    fichier_sortie.write(f"2 SHARED_CM {total_adn:.2f}\n")
                    pct_tot = ( total_adn / 7440 ) * 100 
                    fichier_sortie.write(f"2 SHARED_PCT {pct_tot:.2f}\n")

                # Écrire les données de matching ADN
                #with os.scandir(repertoire) as entries:
                for entry in os.listdir(repertoire):
                    #   for entry in entries:
                    if entry.startswith("final_save_triangul") and entry.endswith(".csv"):
                        print(repertoire + '/' + entry )
                        matching_adn = lire_csv_matching_adn(repertoire + '/' + entry)

                        person1 = None
                        person2 = None
                        person3 = None

                        for match in matching_adn:
                            person1_before = person1
                            listegvn1 = match['Name1'].split()
                            person1 = gedcom_parser.search_individual(gedcom_parser.get_root_child_elements(), listegvn1[1], listegvn1[0])
                            if not person1:    
                                print(f"individu non trouvé : {listegvn1[0]} {listegvn1[1]}")    
                            person2_before = person2
                            listegvn2 = match['Name2'].split()
                            person2 = gedcom_parser.search_individual(gedcom_parser.get_root_child_elements(), listegvn2[1], listegvn2[0])
                            if not person2:
                                print(f"individu non trouvé : {listegvn2[0]} {listegvn2[1]}")    
                                person2 = gedcom_parser.search_individual(gedcom_parser.get_root_child_elements(), listegvn2[1], listegvn2[0])
                            person3_before = person3
                            listegvn3 = match['Name3'].split()
                            person3 = gedcom_parser.search_individual(gedcom_parser.get_root_child_elements(), listegvn3[1], listegvn3[0])  
                            if not person3:
                                print(f"individu non trouvé : {listegvn3[0]} {listegvn3[1]}")    
                                person3 = gedcom_parser.search_individual(gedcom_parser.get_root_child_elements(), listegvn3[1], listegvn3[0])  

                            if person1 and person2 and person3:
                                if person1 != person1_before and person1:
                                    fichier_sortie.write(f"0 {person1.get_pointer()} ID_TRIANGUL\n")

                                if person2 != person2_before and person2:
                                    fichier_sortie.write(f"1 ID1_TRIANGUL {person2.get_pointer()}\n")
                                                            
                                if person3 != person3_before and person3:
                                    fichier_sortie.write(f"2 ID2_TRIANGUL {person3.get_pointer()}\n")
                                
                                fichier_sortie.write(f"3 SEGMENT\n")
                                fichier_sortie.write(f"4 CHROMOSOME {match['Chromosome']}\n")
                                fichier_sortie.write(f"4 START_POS {match['Start Location']}\n")
                                fichier_sortie.write(f"4 END_POS {match['End Location']}\n")
                                fichier_sortie.write(f"4 CM {match['Centimorgans']}\n")
                                fichier_sortie.write(f"4 SNP {match['SNPs']}\n")

                            elif person1 != person1_before and person1:
                                    fichier_sortie.write(f"0 {person1.get_pointer()} ID_TRIANGUL\n")
                                    person2 != person2_before and person2
                                    fichier_sortie.write(f"1 ID1_TRIANGUL {person2.get_pointer()}\n")

                            elif person2 != person2_before and person2:
                                    fichier_sortie.write(f"1 ID1_TRIANGUL {person2.get_pointer()}\n")


        print(f"Copie terminée : {source} -> {destination}")
    except FileNotFoundError:
        print("Erreur : Le fichier source n'existe pas.")
    except IOError as e:
        print(f"Erreur d'entrée/sortie : {e}")
        

def concat_csv_files(input_directory, output_file, output_file3):
    # --- PREMIÈRE PARTIE : fichiers "Shared DNA segments" ---
    dfs = []

    # Parcourir tous les fichiers dans le répertoire d'entrée
    for filename in os.listdir(input_directory):
        # Fichiers type 1
        if filename.startswith("Shared DNA segments") and filename.endswith(".csv"):
            file_path = os.path.join(input_directory, filename)
            try:
                df = pd.read_csv(file_path)
                # Filtrer la ligne "All selected DNA Matches" sur Match Name
                if "Match Name" in df.columns:
                    df = df[df["Match Name"] != "All selected DNA Matches"]
                dfs.append(df)
            except Exception as e:
                print(f"Problème format fichier : {filename}, Erreur : {e}")

    # Concaténer tous les DataFrames en un seul
    if dfs:
        concatenated_df = pd.concat(dfs, ignore_index=True)
        concatenated_df.to_csv(output_file, index=False)
    else:
        print("Aucun fichier valide trouvé pour la concaténation.")

    # --- DEUXIÈME PARTIE : fichiers "Shared DNA segments -" (triangulation) ---
    dfs = []

    for filename in os.listdir(input_directory):
        if filename.startswith("Shared DNA segments -") and filename.endswith(".csv"):
            file_path = os.path.join(input_directory, filename)
            try:
                # première lecture pour récupérer les noms des 2 triangulaires
                df = pd.read_csv(file_path)
                MatchName2 = ""
                MatchName3 = ""
                # Parcours pour identifier
                for index, row in df.iterrows():
                    if row["Match Name"] != "All selected DNA Matches":
                        if MatchName2 == "":
                            MatchName2 = row["Match Name"]
                        elif MatchName3 == "" and row["Match Name"] != MatchName2: 
                            MatchName3 = row["Match Name"]
                # 2ème lecture pour assembler la nouvelle structure
                df = pd.read_csv(file_path)
                entete = ["Name1","Name2","Name3","Chromosome","Start Location","End Location","Start RSID","End RSID","Centimorgans","SNPs"]
                newtab = pd.DataFrame(columns=entete) 
                # Construction des lignes pour le nouveau DataFrame
                for index, row in df.iterrows():
                    if row["Match Name"] == "All selected DNA Matches":
                        nouvelle_ligne = {
                            "Name1": row.get("Name", ""),
                            "Name2": MatchName2,
                            "Name3": MatchName3,  
                            "Chromosome": row.get("Chromosome", ""),
                            "Start Location": row.get("Start Location", ""),
                            "End Location": row.get("End Location", ""),
                            "Start RSID": row.get("Start RSID", ""),
                            "End RSID": row.get("End RSID", ""),
                            "Centimorgans": row.get("Centimorgans", ""),
                            "SNPs": row.get("SNPs", "")
                        }
                        # Ajout efficace via concat
                        newtab = pd.concat([newtab, pd.DataFrame([nouvelle_ligne])], ignore_index=True)     

                dfs.append(newtab)
            except Exception as e:
                print(f"problème format fichier : {filename}, Erreur : {e}")

  
    # Concaténation et calcul Total_Cms pour chaque Name2
    concatenated_df = pd.concat(dfs, ignore_index=True)
    concatenated_df.to_csv(output_file3 , index=False)

def trier_et_supprimer_doublons(input_file, output_file, sort_by=None):
    """
    Trie un fichier CSV et supprime les lignes identiques.

    :param input_file: Chemin du fichier CSV d'entrée.
    :param output_file: Chemin du fichier CSV de sortie.
    :param sort_by: Liste des colonnes à utiliser pour le tri (par défaut None, trie par toutes les colonnes).
    """
    # Lire le fichier CSV
    df = pd.read_csv(input_file)

    # Trier le DataFrame selon les colonnes spécifiées
    if sort_by:
        df = df.sort_values(by=sort_by)
    else:
        df = df.sort_values(by=df.columns.tolist())

    # Supprimer les doublons (lignes identiques)
    df = df.drop_duplicates()

    output_file_tmp = "/mnt/chromeos/MyFiles/dossier_partage_linux/shared DNA segments/tmp_tmp_dna.csv"
    # Sauvegarder le résultat dans un nouveau fichier CSV
    df.to_csv(output_file_tmp, index=False)

    # Lire le fichier CSV
    df2 = pd.read_csv(output_file_tmp)

    # Trier le DataFrame selon les colonnes spécifiées
    if sort_by:
        df2 = df2.sort_values(by=sort_by)
    else:
        df2 = df2.sort_values(by=df2.columns.tolist())

    # Calculer la somme des Cms pour chaque Match Name et l'ajouter à chaque ligne
    if "Match Name" in df2.columns and "Centimorgans" in df2.columns:
        # Conversions nécessaires si Centimorgans est objet/str
        df2["Centimorgans"] = pd.to_numeric(df2["Centimorgans"], errors='coerce')
        df2["Total_Cms"] = df2.groupby("Match Name")["Centimorgans"].transform("sum")

    if "Name2" in df2.columns and "Centimorgans" in df2.columns:
        # Conversions nécessaires si Centimorgans est objet/str
        df2["Centimorgans"] = pd.to_numeric(df2["Centimorgans"], errors='coerce')
        df2["Total_Cms"] = df2.groupby("Name2")["Centimorgans"].transform("sum")

    # Sauvegarder le résultat dans un nouveau fichier CSV
    df2.to_csv(output_file, index=False)

def display_common_couple_ancestor( person1, person2):
    common_couple = gedcom_parser.find_common_ancestor_couple_for_list([person1, person2],2)
            
    #if common_couple:
    #    (ancestor1, ancestor2) = common_couple
    #    print(f"Couple d'ancêtres communs trouvé : {ancestor1.get_name()} et {ancestor2.get_name()}")
    #else:
    #    print("Aucun couple d'ancêtres communs trouvé.")

    #common_couple = gedcom_parser.find_common_ancestor_couple(person1, person2)
    #if common_couple:
    #    (ancestor1, ancestor2) = common_couple
    #    print(f"Couple d'ancêtres communs trouvé : {ancestor1.get_name()} et {ancestor2.get_name()}")
    #else:
    #    print("Aucun couple d'ancêtres communs trouvé.")
    
    result = gedcom_parser.find_common_ancestor_couple(person1, person2)

    if result:
        (ancestor_couple, degree) = result
        (ancestor1, ancestor2) = ancestor_couple
        print(f"Couple d'ancêtres communs trouvé : {ancestor1.get_name()} et {ancestor2.get_name()}")
        print(f"Degré de parenté : {degree}")
    else:
        print("Aucun couple d'ancêtres communs trouvé.")


def verifier_match_et_triangulation():

    person1 = None
    
    while not person1:
        nom1 = input("Veuillez entrer le nom de la première personne: ")
        prenom1 = input("Veuillez entrer le prenom de la première personne: ")
        person1 = gedcom_parser.search_individual(gedcom_parser.get_root_child_elements(), nom1, prenom1)
        if not person1: 
            print("Individu non trouvé dans l'arbre.")   

    # Accéder aux matchs ADN d'un individu
    individual = gedcom_parser.get_element_dictionary()[person1.get_pointer()]
    dna_matches = gedcom_parser.get_dna_matches(individual)
    for match in dna_matches:
        person1 = gedcom_parser.search_individual_pointer(gedcom_parser.get_root_child_elements(), match.get_pointer())
        (first1, last1) = person1.get_name()
        print(f"Matchs ADN de {first1} {last1}")
        for adnmatch in match.matches:          
            person2 = gedcom_parser.search_individual_pointer(gedcom_parser.get_root_child_elements(), adnmatch.get_value())
            (first2, last2) = person2.get_name()
            print(f"Match ADN avec {first2} {last2} shared_pct {adnmatch.shared_pct} shared_cm {adnmatch.shared_cm}")
            display_common_couple_ancestor( person1, person2 )
            for segment in adnmatch.segments:
                print(f"  Segment commun sur le chromosome {segment.chromosome} start_pos {segment.start_pos} end_pos {segment.end_pos} cm {segment.cm} pct {segment.pct} snp {segment.snp}")


    # Accéder aux triangulations d'un individu
    individual = gedcom_parser.get_element_dictionary()[person1.get_pointer()]
    triangulations = gedcom_parser.get_triangulations(individual)
    for triangulation in triangulations:
        person1 = gedcom_parser.search_individual_pointer(gedcom_parser.get_root_child_elements(), triangulation.get_pointer())
        (first1, last1) = person1.get_name()
        for child1 in triangulation.get_child_elements():
            person2 = gedcom_parser.search_individual_pointer(gedcom_parser.get_root_child_elements(), child1.get_value())
            (first2, last2) = person2.get_name()
            for child2 in child1.get_child_elements():
                person3 = gedcom_parser.search_individual_pointer(gedcom_parser.get_root_child_elements(), child2.get_value())
                (first3, last3) = person3.get_name()
                print(f"  triangularisation entre  {last1} {first1} et {last2} {first2}  et {last3} {first3} ")
                for segment in child2.get_child_elements(): 
                    print(f"  Segment commun sur le chromosome {segment.chromosome} start_pos {segment.start_pos} end_pos {segment.end_pos} cm {segment.cm} pct {segment.pct} snp {segment.snp}")
     
    # On regarde si on a un ancetre en commun sur les 2 autres personnes de la triangulation
    individual = gedcom_parser.get_element_dictionary()[person1.get_pointer()]
    triangulations = gedcom_parser.get_triangulations(individual)
    for triangulation in triangulations:
        #person1 = gedcom_parser.search_individual_pointer(gedcom_parser.get_root_child_elements(), triangulation.get_pointer())
        #(first1, last1) = person1.get_name()
        for child1 in triangulation.get_child_elements():
            person2 = gedcom_parser.search_individual_pointer(gedcom_parser.get_root_child_elements(), child1.get_value())
            (first2, last2) = person2.get_name()
            for child2 in child1.get_child_elements():
                person3 = gedcom_parser.search_individual_pointer(gedcom_parser.get_root_child_elements(), child2.get_value())
                (first3, last3) = person3.get_name()
                print(f"  triangularisation entre  {last1} {first1} et {last2} {first2}  et {last3} {first3} ")
                print(f"  test recherche ancetre commun entre  entre {last2} {first2}  et {last3} {first3} ")
                display_common_couple_ancestor( person1, person2 )
                for segment in child2.get_child_elements(): 
                    print(f"  Segment commun sur le chromosome {segment.chromosome} start_pos {segment.start_pos} end_pos {segment.end_pos} cm {segment.cm} pct {segment.pct} snp {segment.snp}")
        

def find_multiple_coincidences(gedcom_parser, individual):
    """
    Trouve des groupes d'individus partageant des segments communs, en étendant les triangulations.
    
    :param gedcom_parser: Instance du parser GEDCOM.
    :param individual: L'individu de référence.
    :return: Un dictionnaire où les clés sont des segments et les valeurs sont des ensembles d'individus.
    """
    # Dictionnaire pour stocker les segments et les groupes d'individus associés
    shared_segments = {}

    # Accéder aux triangulations de l'individu
    triangulations = gedcom_parser.get_triangulations(individual)
    for triangulation in triangulations:
        # Récupérer les individus de la triangulation
        person1 = gedcom_parser.search_individual_pointer(gedcom_parser.get_root_child_elements(), triangulation.get_pointer())
        for child1 in triangulation.get_child_elements():
            person2 = gedcom_parser.search_individual_pointer(gedcom_parser.get_root_child_elements(), child1.get_value())
            for child2 in child1.get_child_elements():
                person3 = gedcom_parser.search_individual_pointer(gedcom_parser.get_root_child_elements(), child2.get_value())

                # Parcourir les segments de la triangulation
                for segment in child2.get_child_elements():
                    # Créer une clé unique pour le segment (chromosome + intervalle)
                    segment_key = (segment.chromosome, segment.start_pos, segment.end_pos)

                    # Ajouter les individus à la liste correspondant à ce segment
                    if segment_key not in shared_segments:
                        shared_segments[segment_key] = set()
                    shared_segments[segment_key].add(person1)
                    shared_segments[segment_key].add(person2)
                    shared_segments[segment_key].add(person3)

    # Étendre les triangulations à des coïncidences multiples
    for segment_key, individuals in shared_segments.items():
        chromosome, start_pos, end_pos = segment_key

        # Rechercher d'autres segments partagés avec au moins 2 des individus de la triangulation
        for other_segment_key, other_individuals in shared_segments.items():
            other_chromosome, other_start_pos, other_end_pos = other_segment_key

            # Vérifier si les segments se chevauchent et partagent au moins 2 individus
            if (chromosome == other_chromosome and
                not (end_pos < other_start_pos or start_pos > other_end_pos) and
                len(individuals.intersection(other_individuals)) >= 2):
                # Fusionner les groupes d'individus
                shared_segments[segment_key].update(other_individuals)

    return shared_segments

def find_shared_segments(gedcom_parser, individual):
    """
    Trouve les individus qui triangulent avec l'individu donné et partagent les mêmes segments ADN.
    
    :param gedcom_parser: Instance du parser GEDCOM.
    :param individual: L'individu de référence.
    :return: Un dictionnaire où les clés sont des segments et les valeurs sont des listes d'individus.
    """
    # Dictionnaire pour stocker les segments et les individus associés
    shared_segments = {}

    # Parcourir les triangulations de l'individu
    triangulations = gedcom_parser.get_triangulations(individual)
    for triangulation in triangulations:
        # Récupérer les individus impliqués dans la triangulation
        person1 = gedcom_parser.search_individual_pointer(gedcom_parser.get_root_child_elements(), triangulation.get_pointer())
        for child1 in triangulation.get_child_elements():
            person2 = gedcom_parser.search_individual_pointer(gedcom_parser.get_root_child_elements(), child1.get_value())
            for child2 in child1.get_child_elements():
                person3 = gedcom_parser.search_individual_pointer(gedcom_parser.get_root_child_elements(), child2.get_value())

                # Parcourir les segments de la triangulation
                for segment in child2.get_child_elements():
                    # Créer une clé unique pour le segment (chromosome + intervalle)
                    segment_key = (segment.chromosome, segment.start_pos, segment.end_pos)

                    # Ajouter les individus à la liste correspondant à ce segment
                    if segment_key not in shared_segments:
                        shared_segments[segment_key] = set()  # Utiliser un set pour éviter les doublons

                    #shared_segments[segment_key].add(person1)
                    shared_segments[segment_key].add(person2)
                    shared_segments[segment_key].add(person3)

    return shared_segments

def find_shared_segments_from_matches(gedcom_parser, individual):
    """
    Trouve les segments partagés entre un individu et ses matchs ADN, en regroupant les segments qui se chevauchent.
    
    :param gedcom_parser: Instance du parser GEDCOM.
    :param individual: L'individu de référence.
    :return: Un dictionnaire où les clés sont des segments et les valeurs sont des listes de tuples (individu, start_pos, end_pos).
    """
    # Dictionnaire pour stocker les segments et les individus associés avec leurs positions originelles
    shared_segments = {}

    # Accéder aux matchs ADN de l'individu
    dna_matches = gedcom_parser.get_dna_matches(individual)
    for match in dna_matches:
        # Récupérer l'individu de référence (person1)
        person1 = gedcom_parser.search_individual_pointer(gedcom_parser.get_root_child_elements(), match.get_pointer())
        
        # Parcourir les matchs ADN de cet individu
        for adn_match in match.matches:
            # Récupérer l'individu matché (person2)
            person2 = gedcom_parser.search_individual_pointer(gedcom_parser.get_root_child_elements(), adn_match.get_value())
            
            # Parcourir les segments partagés entre person1 et person2
            for segment in adn_match.segments:
                # Créer une clé unique pour le segment (chromosome + intervalle)
                segment_key = (segment.chromosome, segment.start_pos, segment.end_pos)

                # Vérifier si ce segment chevauche un segment existant
                found_overlap = False
                for existing_segment in shared_segments.keys():
                    existing_chromosome, existing_start, existing_end = existing_segment
                    if (segment.chromosome == existing_chromosome and
                        not (segment.end_pos < existing_start or segment.start_pos > existing_end)):
                        # Les segments se chevauchent
                        found_overlap = True
                        # Mettre à jour l'intervalle du segment existant pour inclure le nouveau segment
                        new_start = min(segment.start_pos, existing_start)
                        new_end = max(segment.end_pos, existing_end)
                        # Mettre à jour la liste des individus et leurs segments originels
                        shared_segments[(existing_chromosome, new_start, new_end)] = shared_segments.pop(existing_segment)
                        shared_segments[(existing_chromosome, new_start, new_end)].append((person1, segment.start_pos, segment.end_pos))
                        shared_segments[(existing_chromosome, new_start, new_end)].append((person2, segment.start_pos, segment.end_pos))
                        break

                if not found_overlap:
                    # Ajouter un nouveau segment
                    shared_segments[segment_key] = []
                    shared_segments[segment_key].append((person1, segment.start_pos, segment.end_pos))
                    shared_segments[segment_key].append((person2, segment.start_pos, segment.end_pos))

    return shared_segments

def display_shared_segments(shared_segments):
    # Trier les segments par chromosome, start_pos, puis end_pos
    sorted_segments = sorted(shared_segments.items(), key=lambda x: (x[0][0], x[0][1], x[0][2]))

    # Afficher les segments partagés triés
    for segment, individuals_data in sorted_segments:
        chromosome, start_pos, end_pos = segment
        print(f"Segment commun sur le chromosome {chromosome} (de {start_pos} à {end_pos}):")
    
        # Afficher les individus et leurs segments originels
        for individual, original_start, original_end in individuals_data:
            (first, last) = individual.get_name()
            print(f"  - {last} {first} (de {original_start} à {original_end})")
        print()

def find_shared_segments(gedcom_parser, individual):
    """
    Trouve les individus qui triangulent avec l'individu donné et partagent les mêmes segments ADN.
    
    :param gedcom_parser: Instance du parser GEDCOM.
    :param individual: L'individu de référence.
    :return: Un dictionnaire où les clés sont des segments et les valeurs sont des listes d'individus.
    """
    shared_segments = {}

    triangulations = gedcom_parser.get_triangulations(individual)
    for triangulation in triangulations:
        person1 = gedcom_parser.search_individual_pointer(gedcom_parser.get_root_child_elements(), triangulation.get_pointer())
        for child1 in triangulation.get_child_elements():
            person2 = gedcom_parser.search_individual_pointer(gedcom_parser.get_root_child_elements(), child1.get_value())
            for child2 in child1.get_child_elements():
                person3 = gedcom_parser.search_individual_pointer(gedcom_parser.get_root_child_elements(), child2.get_value())

                for segment in child2.get_child_elements():
                    segment_key = (segment.chromosome, segment.start_pos, segment.end_pos)

                    if segment_key not in shared_segments:
                        shared_segments[segment_key] = set()

                    shared_segments[segment_key].add(person1)
                    shared_segments[segment_key].add(person2)
                    shared_segments[segment_key].add(person3)

    return shared_segments

def visualize_shared_segments(shared_segments):
    """
    Visualise les segments partagés sur les chromosomes avec matplotlib.
    
    :param shared_segments: Dictionnaire de segments et d'individus.
    """
    fig, ax = plt.subplots(figsize=(10, 6))

    chromosomes = sorted(set(segment[0] for segment in shared_segments.keys()))
    y_ticks = range(len(chromosomes))

    for i, chromosome in enumerate(chromosomes):
        ax.hlines(i, 0, 250_000_000, colors='gray', linestyles='dashed', alpha=0.5)
        ax.text(-10_000_000, i, f'Chr {chromosome}', va='center', ha='right', fontsize=9)

    for segment, individuals in shared_segments.items():
        chromosome, start_pos, end_pos = segment
        y = chromosomes.index(chromosome)
        ax.hlines(y, int(start_pos), int(end_pos), colors='blue', lw=4, alpha=0.7)
        ax.text(int(start_pos) + int(end_pos) / 2, y + 0.1, f'{len(individuals)}', va='bottom', ha='center', fontsize=8)

    ax.set_xlabel('Position sur le chromosome (bp)')
    ax.set_xlim(0, 250_000_000)

    ax.set_yticks(y_ticks)
    ax.set_yticklabels([f'Chr {chromosome}' for chromosome in chromosomes])
    ax.set_ylim(-0.5, len(chromosomes) - 0.5)

    ax.set_title('Segments partagés sur les chromosomes')
    plt.tight_layout()

    plt.show()

    import pandas as pd
import matplotlib.pyplot as plt
import numpy as np


def viz_map_chrom():    
    # Chargement des données CSV
    csv_path = '/mnt/chromeos/MyFiles/dossier_partage_linux/shared DNA segments/final_shared_dna.csv'
    # Lecture des données segment DNA
    # En fait, je récupère le contenu du fichier attaché via l'ID fourni et traite le CSV

    # Pour exécuter ici, je vais simuler la lecture du CSV avec les données reçues


    # Lecture du CSV
    segments_df = pd.read_csv(csv_path)

    # Regroupement par chromosome et segments
    chromosomes = sorted(segments_df['Chromosome'].unique(), reverse=True)

    # Paramètres pour l'affichage graphique
    plt.figure(figsize=(15, 8))
    plt.title("Carte chromosomique basée sur segments ADN partagés")
    plt.xlabel("Position sur le chromosome (bp)")
    plt.ylabel("Chromosomes")
    plt.yticks(range(len(chromosomes)), chromosomes)

    # Pour chaque segment, afficher une ligne sur le graphique
    colors = plt.cm.get_cmap('tab20', len(segments_df['Match Name'].unique()))
    match_name_to_color = {name: colors(i) for i, name in enumerate(segments_df['Match Name'].unique())}

    for i, chrom in enumerate(chromosomes):
        chrom_segments = segments_df[segments_df['Chromosome'] == chrom]
        for _, row in chrom_segments.iterrows():
            plt.plot([row['Start Location'], row['End Location']], [i, i], color=match_name_to_color[row['Match Name']], linewidth=8, alpha=0.7)

    plt.grid(axis='x')
    plt.tight_layout()

    # Affichage du graphique
    plt.show()

def excel_ancetres_cousins():
    person1 = None
    while not person1:
        nom1 = input("Veuillez entrer le nom de la première personne: ")
        prenom1 = input("Veuillez entrer le prenom de la première personne: ")
        person1 = gedcom_parser.search_individual(gedcom_parser.get_root_child_elements(), nom1, prenom1)
        if not person1: 
            print("Individu non trouvé dans l'arbre.")
    x=0
    # Unpack the name tuple
    (first, last) = person1.get_name()
    print(first + " " + last)
    ancetres = gedcom_parser.get_ancestors(person1,"ALL") 
    y=0
    for indiv in ancetres:
    #for indiv in indic_root:
        if isinstance(indiv, IndividualElement):
            parents = gedcom_parser.get_parents(indiv,'ALL')
            if len(parents) == 0:
            #indiv = gedcom_parser.search_individual(indic_root ,'Grenados','Jean-paul')
                x=0
                #if isinstance(indiv, IndividualElement): 
                # Unpack the name tuple
                (firsta, lasta) = indiv.get_name()
                # print(first + " " + last)
                descendants = gedcom_parser.get_descendants(indiv,"ALL") 
                for descendant in descendants:
                    if isinstance(descendant, IndividualElement):
                        # Get all individuals birth between 1945 et 2023
                        if descendant.birth_range_match(1940,2026): 
                             # Unpack the name tuple
                            (first, last) = descendant.get_name()
                            if last != 'HATTEMER' and last != 'GRENADOS' and last != 'Kretz'and last != 'Bertin': 
                                x=x+1
                                if x == 1:
                                    dfa1 = dfa = pd.DataFrame({"Prenom_ancetre":[firsta],"Nom_ancetre":[lasta],"Num":x,"prenom_desc":[first],"nom_desc":[last]})
                                else:
                                    query_result = dfa1.query("prenom_desc == @first and nom_desc == @last")
                                    if len(query_result) == 0:
                                        new_row = {"Prenom_ancetre":firsta,"Nom_ancetre":lasta,"Num":x,"prenom_desc":first,"nom_desc":last}
                                        dfa1 = dfa = dfa.append(new_row, ignore_index=True)
                if x > 0:
                    if len(dfa1) > 6:
                        if y == 0:
                            y=y+1
                            dfa2 = dfb = dfa1.copy()
                            #    dtext2 = dfa1.to_string()
                             #    print(dtext2)
                            print(y)
                        else:
                            y=y+1
                            #    query_result = dfa2.query("First == @firsta and Last == @lasta")
                            #    if len(query_result) == 0:
                            #    new_row = {"First":firsta,"Last":lasta,"Nombres":x}
                            #   dfa2 = dfb = dfa1.append(new_row, ignore_index=True)
                            dfa2 = dfb = dfa2.append(dfa1,ignore_index=True)
                            #    dtext2 = dfa1.to_string()
                            #    print(dtext2) 
                            #print(y)   
    dfa2.to_excel("/mnt/chromeos/MyFiles/dossier_partage_linux/output_Excel_cousins.xlsx")
        
 #          break


# Exemple d'utilisation
# copier_fichier('fichier_source.txt', 'fichier_sortie.txt')



#import requests
#from bs4 import BeautifulSoup as bs

# vgm_url = 'https://www.geneanet.org/fonds/individus/?ascendance=1&categories_1__arbres__=arbres&categories_1__archives__=archives&categories_2__arbres%23utilisateur__=arbres%23utilisateur&categories_2__archives%23etatcivil__=archives%23etatcivil&categories_2__archives%23recensement__=archives%23recensement&categories_2__archives%23militaire__=archives%23militaire&exact_day=&exact_month=&exact_year=&from=&go=1&id_filter_block=search-filter-filiation&ignore_each_patronyme=&ignore_each_patronyme_conjoint=&ignore_each_patronyme_mere=&ignore_each_patronyme_pere=&ignore_each_place=&ignore_each_prenom=&ignore_each_prenom_conjoint=&ignore_each_prenom_mere=&ignore_each_prenom_pere=&ignore_each_profession=&nom=GRANADOS&nom_conjoint=&nom_mere=&nom_pere=&prenom=Rafael&prenom_conjoint=&prenom_conjoint_operateur=and&prenom_mere=&prenom_mere_operateur=and&prenom_operateur=or&prenom_pere=&prenom_pere_operateur=and&profession=&profession_operateur=and&sexe=&size=20&to=&type_periode=between&with_parents=0'

#vgm_url = 'https://www.myheritage.fr/research?s=676831891&action=query&individualId=1503451&rfr=tree&formId=master&formMode=1&useTranslation=1&qname=Name+fn.walpurge+fnmo.2+fnmsvos.1+fnmsmi.1+ln.Hunheiser%2Fsauer+lnmo.4+lnmsdm.1+lnmsmf3.1+lnmsrs.1+g.F&qkeywords=Keyword'

#response = requests.get(vgm_url) 
#html = response.content
#soup = bs(html, "lxml")
#print(soup)

#exit()

#html_text = requests.get(vgm_url).text
#soup = BeautifulSoup(html_text, 'html.parser')
#print(soup.get_text())

#viz_map_chrom() 
#exit()

def function_princ():

    print("Veuillez patienter pendant le chargement de l'arbre généalogique ") 

    # Path to your ".ged" file
    file_path = '/mnt/chromeos/MyFiles/dossier_partage_linux/myheritage_grenados_Work.ged'

    file_entry = '/mnt/chromeos/MyFiles/dossier_partage_linux/genea3.ged'
    file_sortie = '/mnt/chromeos/MyFiles/dossier_partage_linux/genea3ADN.ged'
    path_csv = '/mnt/chromeos/MyFiles/dossier_partage_linux/shared DNA segments' 


    input_directory = "/mnt/chromeos/MyFiles/dossier_partage_linux/shared DNA segments"
    output_file = "/mnt/chromeos/MyFiles/dossier_partage_linux/shared DNA segments/tmp_shared_dna.csv"
    output_file2 = "/mnt/chromeos/MyFiles/dossier_partage_linux/shared DNA segments/final_shared_dna.csv"
    output_file3 = "/mnt/chromeos/MyFiles/dossier_partage_linux/shared DNA segments/tmp_triangul_dna.csv"
    output_file4 = "/mnt/chromeos/MyFiles/dossier_partage_linux/shared DNA segments/final_triangul_dna.csv"

    concat_csv_files(input_directory, output_file , output_file3)
    trier_et_supprimer_doublons(output_file, output_file2, sort_by=["Name", "Match Name", "Chromosome", "Start Location"])
    trier_et_supprimer_doublons(output_file3, output_file4, sort_by=["Name1", "Name2", "Name3" , "Chromosome", "Start Location"])

    # Initialize the parser
    gedcom_parser = Parser()

    # Parse your file
    gedcom_parser.parse_file(file_path,False)

    #person1 = None
    #while not person1:
    #    nom1 = input("Veuillez entrer le nom de la première personne: ")
    #    prenom1 = input("Veuillez entrer le prenom de la première personne: ")
    #    person1 = gedcom_parser.search_individual(gedcom_parser.get_root_child_elements(), nom1, prenom1)
    #    if not person1: 
    #        print("Individu non trouvé dans l'arbre.")    

    #verifier_match_et_triangulation()

    #shared_segments = find_shared_segments(gedcom_parser, person1)
    #shared_segments = find_shared_segments_from_matches(gedcom_parser, person1)
    #shared_segments = find_multiple_coincidences(gedcom_parser, person1)
    #display_shared_segments(shared_segments)
    #visualize_shared_segments(shared_segments)


    #exit()






    num = 0 ;

    while not num == 7:
        while not num == 1 and not num == 2 and not num == 3 and not num == 4 and not num == 5 and not num == 6 and not num == 7:
            while True:
                try:
                    print("Choissisez l'action a effectuer : ")   
                    print("1 : Recherche d'un chemin entre 2 personnes de l'arbre ")  
                    print("2 : Recherche des ancêtres commun entre 2 personnes de l'arbre") 
                    print("3 : Recherche des ancêtres commun entre 3 personnes de l'arbre") 
                    print("4 : liste des noms de ville du fichier gedcom")
                    print("5 : ajout de données ADN au fichier gedcom")
                    print("6 : verifier match et triangulation d'une personne")
                    print("7 : Ancêtres et cousins d'une personne , fichier excel")
                    print("8 : exit") 
                    num = input("Veuillez entrer le numéro de la recherche à effectuer : ")
                    num = int(num)
                    break
                except ValueError:
                    print("Erreur : Veuillez entrer un nombre valide.")

        if num == 8:
            break
        elif num == 1:
        # Recherche des individus par nom
        # Demander le nom de la première personne
            person1 = None
            person2 = None
            while not person1:
                nom1 = input("Veuillez entrer le nom de la première personne: ")
                prenom1 = input("Veuillez entrer le prenom de la première personne: ")
                person1 = gedcom_parser.search_individual(gedcom_parser.get_root_child_elements(), nom1, prenom1)
                if not person1: 
                    print("Individu non trouvé dans l'arbre.")    
    #          break

            while not person2:
                nom2 = input("Veuillez entrer le nom de la deuxième personne: ")
                prenom2 = input("Veuillez entrer le prenom de la deuxième personne: ")
                person2 = gedcom_parser.search_individual(gedcom_parser.get_root_child_elements(), nom2, prenom2)
                if not person2: 
                print("Individu non trouvé dans l'arbre.")  

            print(" ")  
    #   break 
    #person1 = gedcom_parser.search_individual(gedcom_parser.get_root_child_elements(), "Grenados", "Cedric")
    #person2 = gedcom_parser.search_individual(gedcom_parser.get_root_child_elements(), "Prilleux", "Nicolas")

            if person1 and person2:
                # Afficher le chemin entre les deux personnes
                gedcom_parser.display_relationship_path(person1, person2)
            else:
                print("Individus non trouvés.")
            num = 0
        elif num == 2:
        # Recherche des individus par nom
        # Demander le nom de la première personne
            person1 = None
            person2 = None
            while not person1:
                nom1 = input("Veuillez entrer le nom de la première personne: ")
                prenom1 = input("Veuillez entrer le prenom de la première personne: ")
                person1 = gedcom_parser.search_individual(gedcom_parser.get_root_child_elements(), nom1, prenom1)
                if not person1: 
                    print("Individu non trouvé dans l'arbre.")    
    #          break

            while not person2:
                nom2 = input("Veuillez entrer le nom de la deuxième personne: ")
                prenom2 = input("Veuillez entrer le prenom de la deuxième personne: ")
                person2 = gedcom_parser.search_individual(gedcom_parser.get_root_child_elements(), nom2, prenom2)
                if not person2: 
                print("Individu non trouvé dans l'arbre.")  

            print(" ")      

            if person1 and person2:
                display_common_couple_ancestor(person1 , person2)
            
            num = 0
        elif num == 3:
        # Recherche des individus par nom
        # Demander le nom de la première personne
            person1 = None
            person2 = None
            person3 = None
            while not person1:
                nom1 = input("Veuillez entrer le nom de la première personne: ")
                prenom1 = input("Veuillez entrer le prenom de la première personne: ")
                person1 = gedcom_parser.search_individual(gedcom_parser.get_root_child_elements(), nom1, prenom1)
                if not person1: 
                    print("Individu non trouvé dans l'arbre.")    
    #          break

            while not person2:
                nom2 = input("Veuillez entrer le nom de la deuxième personne: ")
                prenom2 = input("Veuillez entrer le prenom de la deuxième personne: ")
                person2 = gedcom_parser.search_individual(gedcom_parser.get_root_child_elements(), nom2, prenom2)
                if not person2: 
                print("Individu non trouvé dans l'arbre.")  


            while not person3:
                nom3 = input("Veuillez entrer le nom de la troisième personne: ")
                prenom3 = input("Veuillez entrer le prenom de la troisème personne: ")
                person3 = gedcom_parser.search_individual(gedcom_parser.get_root_child_elements(), nom3, prenom3)
                if not person3: 
                print("Individu non trouvé dans l'arbre.")  

            print(" ")      

            if person1 and person2 and person3:
                # Trouver l'ancêtre commun à tous les individus
                common_couple = gedcom_parser.find_common_ancestor_couple_for_list([person1, person2, person3],3)
                #common_couple = gedcom_parser.find_common_ancestor_couple_for_three(person1, person2 , person3 )
                if common_couple:
                    (ancestor1, ancestor2) = common_couple
                    print(f"Couple d'ancêtres communs trouvé : {ancestor1.get_name()} et {ancestor2.get_name()}")
                else:
                    print("Aucun couple d'ancêtres communs trouvé.")
                
                common_couple = gedcom_parser.find_common_ancestor_couple_for_three(person1, person2 , person3 )
                if common_couple:
                    (ancestor1, ancestor2) = common_couple
                    print(f"Couple d'ancêtres communs trouvé : {ancestor1.get_name()} et {ancestor2.get_name()}")
                else:
                    print("Aucun couple d'ancêtres communs trouvé.")

            else:
                print("Un ou plusieurs individus non trouvés.")
            num = 0
        elif num == 4:
            # Extraire la liste des lieux (y compris les adresses)
            locations = gedcom_parser.extract_locations()
            # Créer un géocodeur avec l'API Nominatim de OpenStreetMap
            geolocator = Nominatim(user_agent="mon_application")

            # Afficher les lieux
            if locations:
                print("Liste des lieux et adresses mentionnés dans le fichier GEDCOM :")
                for location in sorted(locations):
                    #print(f"- {location}")
                    # Adresse à normaliser
                    address = location
                    try:
                        # Obtenir les informations géographiques de l'adresse
                        #time.sleep(3)
                        locationadr = geolocator.geocode(address)
                        # Afficher l'adresse normalisée et ses coordonnées
                        if locationadr:
                            print("Adresse normalisée:", locationadr.address)
                        #    print("Coordonnées:", locationadr.latitude, locationadr.longitude)
                        #else:
                        #    print("Adresse non trouvée.")
                    except Exception as e:
                        print(f"Erreur appel geocodage : {e}")
                    

            else:
                print("Aucun lieu ou adresse trouvé dans le fichier GEDCOM.")     
            num = 0
        elif num == 5:
            ecrire_csv_fichier_sortie(file_entry , file_sortie, path_csv , gedcom_parser)
            num = 0
        elif num == 6:
            verifier_match_et_triangulation()
            num = 0
        elif num == 7:
            excel_ancetres_cousins()
            num=0

exit()

# compte le nb de descendants par personne de l'arbre sans parents 
indic_root = gedcom_parser.get_root_element().get_child_elements()
y=0
for indiv in indic_root:
    if isinstance(indiv, IndividualElement):
        parents = gedcom_parser.get_parents(indiv,'ALL')
        if len(parents) == 0:
        #indiv = gedcom_parser.search_individual(indic_root ,'Grenados','Diego')
            x=0
        #if isinstance(indiv, IndividualElement): 
        # Unpack the name tuple
            (firsta, lasta) = indiv.get_name()
        # print(first + " " + last)
            ancetres = gedcom_parser.get_descendants(indiv,"ALL") 
            for ancetre in ancetres:
                if isinstance(ancetre, IndividualElement):
                    # Get all individuals birth between 1945 et 2023
                    if ancetre.birth_range_match(1945,2023): 
                         # Unpack the name tuple
                         (first, last) = ancetre.get_name()
                         if last != 'HATTEMER' and last != 'GRENADOS' and last != 'Vigouroux' and last != 'Piard' and last != ' ' and last != 'Grenados' and last != 'grenados' and last != 'Girod' and last != 'Prilleux' and last != 'Carbonnel' and last != 'Guignot' and last != 'Kretz'and last != 'Bertin':
                            if x == 0:
                                x=x+1
                                dfa1 = dfa = pd.DataFrame({"Prenom_ancetre":[firsta],"Nom_ancetre":[lasta],"Num":x,"prenom_desc":[first],"nom_desc":[last]})
                            else:
                                query_result = dfa1.query("prenom_desc == @first and nom_desc == @last")
                                if len(query_result) == 0:
                                    x=x+1
                                    new_row = {"Prenom_ancetre":firsta,"Nom_ancetre":lasta,"Num":x,"prenom_desc":first,"nom_desc":last}
                                    dfa1 = dfa = dfa.append(new_row, ignore_index=True)
            if x > 0:
                if len(dfa1) > 10:
                    if y == 0:
                        y=y+1
                        dfa2 = dfb = dfa1.copy()
                    #    dtext2 = dfa1.to_string()
                    #    print(dtext2)
                        print(y)
                    else:
                        y=y+1
                    #    query_result = dfa2.query("First == @firsta and Last == @lasta")
                    #    if len(query_result) == 0:
                    #    new_row = {"First":firsta,"Last":lasta,"Nombres":x}
                    #   dfa2 = dfb = dfa1.append(new_row, ignore_index=True)
                        dfa2 = dfb = dfa2.append(dfa1,ignore_index=True)
                        #    dtext2 = dfa1.to_string()
                        #    print(dtext2) 
                        #print(y)   
dfa2.to_excel("/mnt/chromeos/MyFiles/dossier_partage_linux/output_genea_4.xlsx")
#dtext3 = dfa2.to_string()
#print(dtext3)

exit()


# compte le nb de descendants par personne de l'arbre sans parents -     
# dans les ascendants direct d'une personne
indic_root = gedcom_parser.get_root_element().get_child_elements()
#indiv = gedcom_parser.search_individual(indic_root ,'Guignot','Colette')
indiv = gedcom_parser.search_individual(indic_root ,'Kretz','Julie')
x=0
# Unpack the name tuple
(first, last) = indiv.get_name()
print(first + " " + last)
ancetres = gedcom_parser.get_ancestors(indiv,"ALL") 
y=0
#for indiv in ancetres:
for indiv in indic_root:
    if isinstance(indiv, IndividualElement):
        parents = gedcom_parser.get_parents(indiv,'ALL')
        if len(parents) == 0:
        #indiv = gedcom_parser.search_individual(indic_root ,'Grenados','Jean-paul')
            x=0
        #if isinstance(indiv, IndividualElement): 
        # Unpack the name tuple
            (firsta, lasta) = indiv.get_name()
        # print(first + " " + last)
            ancetres = gedcom_parser.get_descendants(indiv,"ALL") 
            for ancetre in ancetres:
                if isinstance(ancetre, IndividualElement):
                    # Get all individuals birth between 1945 et 2023
                    if ancetre.birth_range_match(1945,2023): 
                         # Unpack the name tuple
                         (first, last) = ancetre.get_name()
                         if last != 'HATTEMER' and last != 'GRENADOS' and last != 'Kretz'and last != 'Bertin': 
                            x=x+1
                            if x == 1:
                                dfa1 = dfa = pd.DataFrame({"Prenom_ancetre":[firsta],"Nom_ancetre":[lasta],"Num":x,"prenom_desc":[first],"nom_desc":[last]})
                            else:
                                query_result = dfa1.query("prenom_desc == @first and nom_desc == @last")
                                if len(query_result) == 0:
                                    new_row = {"Prenom_ancetre":firsta,"Nom_ancetre":lasta,"Num":x,"prenom_desc":first,"nom_desc":last}
                                    dfa1 = dfa = dfa.append(new_row, ignore_index=True)
            if x > 0:
                if len(dfa1) > 6:
                    if y == 0:
                        y=y+1
                        dfa2 = dfb = dfa1.copy()
                    #    dtext2 = dfa1.to_string()
                    #    print(dtext2)
                        print(y)
                    else:
                        y=y+1
                    #    query_result = dfa2.query("First == @firsta and Last == @lasta")
                    #    if len(query_result) == 0:
                    #    new_row = {"First":firsta,"Last":lasta,"Nombres":x}
                    #   dfa2 = dfb = dfa1.append(new_row, ignore_index=True)
                        dfa2 = dfb = dfa2.append(dfa1,ignore_index=True)
                        #    dtext2 = dfa1.to_string()
                        #    print(dtext2) 
                        #print(y)   
dfa2.to_excel("mnt/chromeos/MyFiles/dossier_partage_linux/output_genea_2.xlsx")
#dtext3 = dfa2.to_string()
#print(dtext3)

exit()

# compte  le nb d ascendant direct d'une personne
indic_root = gedcom_parser.get_root_element().get_child_elements()
indiv = gedcom_parser.search_individual(indic_root ,'GRENADOS','Rafael Juan')
x=0
#if isinstance(indiv, IndividualElement): 
# Unpack the name tuple
(first, last) = indiv.get_name()
print(first + " " + last)
ancetres = gedcom_parser.get_ancestors(indiv,"ALL") 
for ancetre in ancetres:
    if isinstance(ancetre, IndividualElement):
        x=x+1 
        # Unpack the name tuple
        (first, last) = ancetre.get_name()
        # Print the first and last name of the found individual
    #    print(first + " " + last)
        if x == 1:
            df1 = df = pd.DataFrame({"Numero":x,"First":[first],"Last":[last]})
        else:
            new_row = {"Numero":x,"First":first,"Last":last}
            df2 = df = df.append(new_row, ignore_index=True)
    #        print(df2)
dtext = df2.to_string()
print(dtext)




#    break
#            print('nb elements')
#                print(x)

# compte le nb de descendants par personne de l'arbre sans parents - 
# dans les ascendants direct d'une personne
indic_root = gedcom_parser.get_root_element().get_child_elements()
indiv = gedcom_parser.search_individual(indic_root ,'Guignot','Colette')
x=0
# Unpack the name tuple
(first, last) = indiv.get_name()
print(first + " " + last)
ancetres = gedcom_parser.get_ancestors(indiv,"ALL") 
for ancetre in ancetres:
        if isinstance(ancetre, IndividualElement):
            parents2 = gedcom_parser.get_parents(ancetre,'ALL')
            if len(parents2) == 0:
                #indiv = gedcom_parser.search_individual(indic_root ,'Grenados','Jean-paul')
                x=0
                #if isinstance(indiv, IndividualElement): 
                # Unpack the name tuple
                (first, last) = ancetre.get_name()
                # print(first + " " + last)
                ancetres3 = gedcom_parser.get_descendants(ancetre,"ALL") 
                for ancetre4 in ancetres3:
                     if isinstance(ancetre4, IndividualElement):
                    # Get all individuals whose surname matches "Doe"
                        if ancetre4.birth_range_match(1945,2023):
                             x=x+1 
                             # Unpack the name tuple
                             # (first, last) = ancetre.get_name()

                            # Print the first and last name of the found individual
                if x > 50 : 
                    print(first + " " + last)
                    print(x)


# root_child_elements = gedcom_parser.get_root_child_elements()

# # Iterate through all root child elements
# x=0
# for element in root_child_elements:
    
#     # Is the "element" an actual "IndividualElement"? (Allows usage of extra functions such as "surname_match" and "get_name".)
#     if isinstance(element, IndividualElement):
        
#         # Get all individuals whose surname matches "Doe"
#         if element.criteria_match(birth_range=[1945-2023]):
#             x=x+1 
#             # Unpack the name tuple
#             (first, last) = element.get_name()

#             # Print the first and last name of the found individual
#             print(first + " " + last)
# print('nb elements')
# print(x)