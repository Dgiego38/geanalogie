# -*- coding: utf-8 -*-

# Python GEDCOM Parser
#
# Copyright (C) 2018 Damon Brodie (damon.brodie at gmail.com)
# Copyright (C) 2018-2019 Nicklas Reincke (contact at reynke.com)
# Copyright (C) 2016 Andreas Oberritter
# Copyright (C) 2012 Madeleine Price Ball
# Copyright (C) 2005 Daniel Zappala (zappala at cs.byu.edu)
# Copyright (C) 2005 Brigham Young University
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#
# Further information about the license: http://www.gnu.org/licenses/gpl-2.0.html

"""
Module containing the actual `gedcom.parser.Parser` used to generate elements - out of each line -
which can in return be manipulated.
"""

import re as regex
from sys import version_info
from gedcom.element.element import Element
from gedcom.element.family import FamilyElement, NotAnActualFamilyError
from gedcom.element.file import FileElement
from gedcom.element.individual import IndividualElement, NotAnActualIndividualError
from gedcom.element.object import ObjectElement
from gedcom.element.root import RootElement
from gedcom.element.DNAElement import DNAElement
from gedcom.element.DNAMatch import DNAMatchElement
from gedcom.element.DNASegment import DNASegmentElement
from gedcom.element.Triangulation import TriangulationElement
import gedcom.tags
import pickle
import os
from collections import deque

FAMILY_MEMBERS_TYPE_ALL = "ALL"
FAMILY_MEMBERS_TYPE_CHILDREN = gedcom.tags.GEDCOM_TAG_CHILD
FAMILY_MEMBERS_TYPE_HUSBAND = gedcom.tags.GEDCOM_TAG_HUSBAND
FAMILY_MEMBERS_TYPE_PARENTS = "PARENTS"
FAMILY_MEMBERS_TYPE_WIFE = gedcom.tags.GEDCOM_TAG_WIFE


class GedcomFormatViolationError(Exception):
    pass


class Parser(object):
    """Parses and manipulates GEDCOM 5.5 format data

    For documentation of the GEDCOM 5.5 format, see: http://homepages.rootsweb.ancestry.com/~pmcbride/gedcom/55gctoc.htm

    This parser reads and parses a GEDCOM file.

    Elements may be accessed via:

    * a `list` through `gedcom.parser.Parser.get_element_list()`
    * a `dict` through `gedcom.parser.Parser.get_element_dictionary()`
    """

    def __init__(self):
        self.__element_list = []
        self.__element_dictionary = {}
        self.__root_element = RootElement()

    def invalidate_cache(self):
        """Empties the element list and dictionary to cause `gedcom.parser.Parser.get_element_list()`
        and `gedcom.parser.Parser.get_element_dictionary()` to return updated data.

        The update gets deferred until each of the methods actually gets called.
        """
        self.__element_list = []
        self.__element_dictionary = {}

    def get_element_list(self):
        """Returns a list containing all elements from within the GEDCOM file

        By default elements are in the same order as they appeared in the file.

        This list gets generated on-the-fly, but gets cached. If the database
        was modified, you should call `gedcom.parser.Parser.invalidate_cache()` once to let this
        method return updated data.

        Consider using `gedcom.parser.Parser.get_root_element()` or `gedcom.parser.Parser.get_root_child_elements()` to access
        the hierarchical GEDCOM tree, unless you rarely modify the database.

        :rtype: list of Element
        """
        if not self.__element_list:
            for element in self.get_root_child_elements():
                self.__build_list(element, self.__element_list)
        return self.__element_list

    def get_element_dictionary(self):
        """Returns a dictionary containing all elements, identified by a pointer, from within the GEDCOM file

        Only elements identified by a pointer are listed in the dictionary.
        The keys for the dictionary are the pointers.

        This dictionary gets generated on-the-fly, but gets cached. If the
        database was modified, you should call `invalidate_cache()` once to let
        this method return updated data.

        :rtype: dict of Element
        """
        if not self.__element_dictionary:
            self.__element_dictionary = {
                element.get_pointer(): element for element in self.get_root_child_elements() if element.get_pointer()
            }

        return self.__element_dictionary

    def get_root_element(self):
        """Returns a virtual root element containing all logical records as children

        When printed, this element converts to an empty string.

        :rtype: RootElement
        """
        return self.__root_element

    def get_root_child_elements(self):
        """Returns a list of logical records in the GEDCOM file

        By default, elements are in the same order as they appeared in the file.

        :rtype: list of Element
        """
        return self.get_root_element().get_child_elements()

    
    def parse_file(self, file_path, strict=True):
        """Opens and parses a file, from the given file path, as GEDCOM 5.5 formatted data
        :type file_path: str
        :type strict: bool
        """
        # Générer le nom du fichier de cache
        cache_file = file_path + '.cache'

        # Vérifier si le cache existe
        if os.path.exists(cache_file):
            # Charger les données à partir du cache
            with open(cache_file, 'rb') as cache:
                self.__root_element = pickle.load(cache)
                self.invalidate_cache()  # Invalider le cache pour forcer la régénération des listes et dictionnaires
        else:
            # Parser le fichier GEDCOM normalement
            with open(file_path, 'rb') as gedcom_stream:
                self.parse(gedcom_stream, strict)

            # Sauvegarder les données dans le cache
            with open(cache_file, 'wb') as cache:
                pickle.dump(self.__root_element, cache)


    def parse(self, gedcom_stream, strict=True):
        """Parses a stream, or an array of lines, as GEDCOM 5.5 formatted data
        :type gedcom_stream: a file stream, or str array of lines with new line at the end
        :type strict: bool
        """
#        self.invalidate_cache()
        self.__root_element = RootElement()

        line_number = 1
        last_element = self.get_root_element()

        for line in gedcom_stream:
            last_element = self.__parse_line(line_number, line.decode('utf-8-sig',errors='replace'), last_element, strict)
            line_number += 1

    # Private methods

    @staticmethod
    def __parse_line(line_number, line, last_element, strict=True):
        """Parse a line from a GEDCOM 5.5 formatted document

        Each line should have the following (bracketed items optional):
        level + ' ' + [pointer + ' ' +] tag + [' ' + line_value]

        :type line_number: int
        :type line: str
        :type last_element: Element
        :type strict: bool

        :rtype: Element
        """

        # Level must start with non-negative int, no leading zeros.
        level_regex = '^(0|[1-9]+[0-9]*) '

        # Pointer optional, if it exists it must be flanked by `@`
        pointer_regex = '(@[^@]+@ |)'

        # Tag must be an alphanumeric string
        tag_regex = '([A-Za-z0-9_]+)'

        # Value optional, consists of anything after a space to end of line
        value_regex = '( [^\n\r]*|)'

        # End of line defined by `\n` or `\r`
        end_of_line_regex = '([\r\n]{1,2})'

        # Complete regex
        gedcom_line_regex = level_regex + pointer_regex + tag_regex + value_regex + end_of_line_regex 
        regex_match = regex.match(gedcom_line_regex, line)

        if regex_match is None:
            if strict:
                error_message = ("Line <%d:%s> of document violates GEDCOM format 5.5" % (line_number, line)
                                 + "\nSee: https://chronoplexsoftware.com/gedcomvalidator/gedcom/gedcom-5.5.pdf")
                raise GedcomFormatViolationError(error_message)
            else:
                # Quirk check - see if this is a line without a CRLF (which could be the last line)
                last_line_regex = level_regex + pointer_regex + tag_regex + value_regex
                regex_match = regex.match(last_line_regex, line)
                if regex_match is not None:
                    line_parts = regex_match.groups()

                    level = int(line_parts[0])
                    pointer = line_parts[1].rstrip(' ')
                    tag = line_parts[2]
                    value = line_parts[3][1:]
                    crlf = '\n'
                else:
                    # Quirk check - Sometimes a gedcom has a text field with a CR.
                    # This creates a line without the standard level and pointer.
                    # If this is detected then turn it into a CONC or CONT.
                    line_regex = '([^\n\r]*|)'
                    cont_line_regex = line_regex + end_of_line_regex
                    regex_match = regex.match(cont_line_regex, line)
                    line_parts = regex_match.groups()
                    level = last_element.get_level()
                    tag = last_element.get_tag()
                    pointer = None
                    value = line_parts[0][1:]
                    crlf = line_parts[1]
                    if tag != gedcom.tags.GEDCOM_TAG_CONTINUED and tag != gedcom.tags.GEDCOM_TAG_CONCATENATION:
                        # Increment level and change this line to a CONC
                        level += 1
                        tag = gedcom.tags.GEDCOM_TAG_CONCATENATION
        else:
            line_parts = regex_match.groups()

            level = int(line_parts[0])
            pointer = line_parts[1].rstrip(' ')
            tag = line_parts[2]
            value = line_parts[3][1:]
            crlf = line_parts[4]

        # Check level: should never be more than one higher than previous line.
        if level > last_element.get_level() + 1:
            level = last_element.get_level() 
 #           error_message = ("Line %d of document violates GEDCOM format 5.5" % line_number
 #                            + "\nLines must be no more than one level higher than previous line."
 #                            + "\nSee: https://chronoplexsoftware.com/gedcomvalidator/gedcom/gedcom-5.5.pdf")
 #           raise GedcomFormatViolationError(error_message)

    
        # Créer l'élément en fonction du tag
        if tag == gedcom.tags.GEDCOM_TAG_INDIVIDUAL:
            element = IndividualElement(level, pointer, tag, value, crlf, multi_line=False)
        elif tag == gedcom.tags.GEDCOM_TAG_FAMILY:
            element = FamilyElement(level, pointer, tag, value, crlf, multi_line=False)
        elif tag == gedcom.tags.GEDCOM_TAG_FILE:
            element = FileElement(level, pointer, tag, value, crlf, multi_line=False)
        elif tag == gedcom.tags.GEDCOM_TAG_OBJECT:
            element = ObjectElement(level, pointer, tag, value, crlf, multi_line=False)
        elif tag == "DNA":
            element = DNAElement(level, pointer, tag, value, crlf, multi_line=False)
        elif tag == "MATCH":
            element = DNAMatchElement(level, pointer, tag, value, crlf, multi_line=False)
        elif tag == "SEGMENT":
            element = DNASegmentElement(level, pointer, tag, value, crlf, multi_line=False)
        elif tag == "ID_TRIANGUL":
            element = TriangulationElement(level, pointer, tag, value, crlf, multi_line=False)
        else:
            element = Element(level, pointer, tag, value, crlf, multi_line=False)

        
        # Start with last element as parent, back up if necessary.
        parent_element = last_element

        while parent_element.get_level() > level - 1:
            parent_element = parent_element.get_parent_element()

        # Add child to parent & parent to child.
        parent_element.add_child_element(element)

        # Gérer les sous-éléments pour les nouveaux tags
        if tag == "MATCH":
            # Associer le MATCH au DNAElement parent
            parent = element.get_parent_element()
            if isinstance(parent, DNAElement):
                parent.matches.append(element)
        elif tag == "SEGMENT":
            # Associer le SEGMENT au DNAMatchElement parent
            parent = element.get_parent_element()
            if isinstance(parent, DNAMatchElement):
                parent.segments.append(element)
        elif tag == "SHARED_CM":
            # Associer SHARED_CM au DNAMatchElement parent
            parent = element.get_parent_element()
            if isinstance(parent, DNAMatchElement):
                parent.shared_cm = value
        elif tag == "SHARED_PCT":
            # Associer SHARED_PCT au DNAMatchElement parent
            parent = element.get_parent_element()
            if isinstance(parent, DNAMatchElement):
                parent.shared_pct = value
        elif tag == "CHROMOSOME":
            # Associer CHROMOSOME au DNASegmentElement parent
            parent = element.get_parent_element()
            if isinstance(parent, DNASegmentElement):
                parent.chromosome = value
        elif tag == "START_POS":
            # Associer START_POS au DNASegmentElement parent
            parent = element.get_parent_element()
            if isinstance(parent, DNASegmentElement):
                parent.start_pos = value
        elif tag == "END_POS":
            # Associer END_POS au DNASegmentElement parent
            parent = element.get_parent_element()
            if isinstance(parent, DNASegmentElement):
                parent.end_pos = value
        elif tag == "CM":
            # Associer CM au DNASegmentElement parent
            parent = element.get_parent_element()
            if isinstance(parent, DNASegmentElement):
                parent.cm = value
        elif tag == "PCT":
            # Associer PCT au DNASegmentElement parent
            parent = element.get_parent_element()
            if isinstance(parent, DNASegmentElement):
                parent.pct = value
        elif tag == "SNP":
            # Associer SNP au DNASegmentElement parent
            parent = element.get_parent_element()
            if isinstance(parent, DNASegmentElement):
                parent.snp = value
        return element

    def __build_list(self, element, element_list):
        """Recursively add elements to a list containing elements
        :type element: Element
        :type element_list: list of Element
        """
        element_list.append(element)
        for child in element.get_child_elements():
            self.__build_list(child, element_list)

    # Methods for analyzing individuals and relationships between individuals

    def get_marriages(self, individual):
        """Returns a list of marriages of an individual formatted as a tuple (`str` date, `str` place)
        :type individual: IndividualElement
        :rtype: tuple
        """
        marriages = []
        if not isinstance(individual, IndividualElement):
            raise NotAnActualIndividualError(
                "Operation only valid for elements with %s tag" % gedcom.tags.GEDCOM_TAG_INDIVIDUAL
            )
        # Get and analyze families where individual is spouse.
        families = self.get_families(individual, gedcom.tags.GEDCOM_TAG_FAMILY_SPOUSE)
        for family in families:
            for family_data in family.get_child_elements():
                if family_data.get_tag() == gedcom.tags.GEDCOM_TAG_MARRIAGE:
                    date = ''
                    place = ''
                    for marriage_data in family_data.get_child_elements():
                        if marriage_data.get_tag() == gedcom.tags.GEDCOM_TAG_DATE:
                            date = marriage_data.get_value()
                        if marriage_data.get_tag() == gedcom.tags.GEDCOM_TAG_PLACE:
                            place = marriage_data.get_value()
                    marriages.append((date, place))
        return marriages

    def get_marriage_years(self, individual):
        """Returns a list of marriage years (as integers) for an individual
        :type individual: IndividualElement
        :rtype: list of int
        """
        dates = []

        if not isinstance(individual, IndividualElement):
            raise NotAnActualIndividualError(
                "Operation only valid for elements with %s tag" % gedcom.tags.GEDCOM_TAG_INDIVIDUAL
            )

        # Get and analyze families where individual is spouse.
        families = self.get_families(individual, gedcom.tags.GEDCOM_TAG_FAMILY_SPOUSE)
        for family in families:
            for child in family.get_child_elements():
                if child.get_tag() == gedcom.tags.GEDCOM_TAG_MARRIAGE:
                    for childOfChild in child.get_child_elements():
                        if childOfChild.get_tag() == gedcom.tags.GEDCOM_TAG_DATE:
                            date = childOfChild.get_value().split()[-1]
                            try:
                                dates.append(int(date))
                            except ValueError:
                                pass
        return dates

    def marriage_year_match(self, individual, year):
        """Checks if one of the marriage years of an individual matches the supplied year. Year is an integer.
        :type individual: IndividualElement
        :type year: int
        :rtype: bool
        """
        if not isinstance(individual, IndividualElement):
            raise NotAnActualIndividualError(
                "Operation only valid for elements with %s tag" % gedcom.tags.GEDCOM_TAG_INDIVIDUAL
            )

        years = self.get_marriage_years(individual)
        return year in years

    def marriage_range_match(self, individual, from_year, to_year):
        """Check if one of the marriage years of an individual is in a given range. Years are integers.
        :type individual: IndividualElement
        :type from_year: int
        :type to_year: int
        :rtype: bool
        """
        if not isinstance(individual, IndividualElement):
            raise NotAnActualIndividualError(
                "Operation only valid for elements with %s tag" % gedcom.tags.GEDCOM_TAG_INDIVIDUAL
            )

        years = self.get_marriage_years(individual)
        for year in years:
            if from_year <= year <= to_year:
                return True
        return False

    def get_families(self, individual, family_type=gedcom.tags.GEDCOM_TAG_FAMILY_SPOUSE):
        """Return family elements listed for an individual

        family_type can be `gedcom.tags.GEDCOM_TAG_FAMILY_SPOUSE` (families where the individual is a spouse) or
        `gedcom.tags.GEDCOM_TAG_FAMILY_CHILD` (families where the individual is a child). If a value is not
        provided, `gedcom.tags.GEDCOM_TAG_FAMILY_SPOUSE` is default value.

        :type individual: IndividualElement
        :type family_type: str
        :rtype: list of FamilyElement
        """
        if not isinstance(individual, IndividualElement):
            raise NotAnActualIndividualError(
                "Operation only valid for elements with %s tag" % gedcom.tags.GEDCOM_TAG_INDIVIDUAL
            )

        families = []
        element_dictionary = self.get_element_dictionary()

        for child_element in individual.get_child_elements():
            is_family = (child_element.get_tag() == family_type
                         and child_element.get_value() in element_dictionary)
            if is_family:
                families.append(element_dictionary[child_element.get_value()])

        return families

    def get_ancestors(self, individual, ancestor_type="ALL"):
        """Return elements corresponding to ancestors of an individual

        Optional `ancestor_type`. Default "ALL" returns all ancestors, "NAT" can be
        used to specify only natural (genetic) ancestors.

        :type individual: IndividualElement
        :type ancestor_type: str
        :rtype: list of Element
        """
        if not isinstance(individual, IndividualElement):
            raise NotAnActualIndividualError(
                "Operation only valid for elements with %s tag" % gedcom.tags.GEDCOM_TAG_INDIVIDUAL
            )

        parents = self.get_parents(individual, ancestor_type)
        ancestors = []
        ancestors.extend(parents)

        for parent in parents:
            ancestors.extend(self.get_ancestors(parent))

        return ancestors

    def get_parents(self, individual, parent_type="ALL"):
        """Return elements corresponding to parents of an individual

        Optional parent_type. Default "ALL" returns all parents. "NAT" can be
        used to specify only natural (genetic) parents.

        :type individual: IndividualElement
        :type parent_type: str
        :rtype: list of IndividualElement
        """
        if not isinstance(individual, IndividualElement):
            raise NotAnActualIndividualError(
                "Operation only valid for elements with %s tag" % gedcom.tags.GEDCOM_TAG_INDIVIDUAL
            )

        parents = []
        families = self.get_families(individual, gedcom.tags.GEDCOM_TAG_FAMILY_CHILD)

        for family in families:
            if parent_type == "NAT":
                for family_member in family.get_child_elements():

                    if family_member.get_tag() == gedcom.tags.GEDCOM_TAG_CHILD \
                       and family_member.get_value() == individual.get_pointer():

                        for child in family_member.get_child_elements():
                            if child.get_value() == "Natural":
                                if child.get_tag() == gedcom.tags.GEDCOM_PROGRAM_DEFINED_TAG_MREL:
                                    parents += self.get_family_members(family, gedcom.tags.GEDCOM_TAG_WIFE)
                                elif child.get_tag() == gedcom.tags.GEDCOM_PROGRAM_DEFINED_TAG_FREL:
                                    parents += self.get_family_members(family, gedcom.tags.GEDCOM_TAG_HUSBAND)
            else:
                parents += self.get_family_members(family, "PARENTS")

        return parents

    def get_descendants(self, individual, descendant_type="ALL"):
        """Return elements corresponding to descendants of an individual

        Optional `ancestor_type`. Default "ALL" returns all descendants, "NAT" can be
        used to specify only natural (genetic) descendants.

        :type individual: IndividualElement
        :type ancestor_type: str
        :rtype: list of Element
        """
        if not isinstance(individual, IndividualElement):
            raise NotAnActualIndividualError(
                "Operation only valid for elements with %s tag" % gedcom.tags.GEDCOM_TAG_INDIVIDUAL
            )

        enfants = self.get_enfants(individual, descendant_type)
        descendants = []
        descendants.extend(enfants)

        for enfant in enfants:
            descendants.extend(self.get_descendants(enfant))

        return descendants

    def get_enfants(self, individual, enfant_type="ALL"):
        """Return elements corresponding to parents of an individual

        Optional enfant_type. Default "ALL" returns all enfants. "NAT" can be
        used to specify only natural (genetic) enfants.

        :type individual: IndividualElement
        :type parent_type: str
        :rtype: list of IndividualElement
        """
        if not isinstance(individual, IndividualElement):
            raise NotAnActualIndividualError(
                "Operation only valid for elements with %s tag" % gedcom.tags.GEDCOM_TAG_INDIVIDUAL
            )

        enfants = []
        families = self.get_families(individual, gedcom.tags.GEDCOM_TAG_FAMILY_SPOUSE)
        for family in families:
            if enfant_type == "NAT":
                for family_member in family.get_child_elements():

                    if family_member.get_tag() == gedcom.tags.GEDCOM_TAG_CHILD \
                       and family_member.get_value() == individual.get_pointer():

                        for child in family_member.get_child_elements():
                            if child.get_value() == "Natural":
                                if child.get_tag() == gedcom.tags.GEDCOM_PROGRAM_DEFINED_TAG_MREL:
                                    enfants += self.get_family_members(family, gedcom.tags.GEDCOM_TAG_WIFE)
                                elif child.get_tag() == gedcom.tags.GEDCOM_PROGRAM_DEFINED_TAG_FREL:
                                    enfants += self.get_family_members(family, gedcom.tags.GEDCOM_TAG_HUSBAND)
            else:
                enfants += self.get_family_members(family, gedcom.tags.GEDCOM_TAG_CHILD)

        return enfants

    def find_path_to_ancestor(self, descendant, ancestor, path=None):
        """Return path from descendant to ancestor
        :rtype: object
        """
        if not isinstance(descendant, IndividualElement) and isinstance(ancestor, IndividualElement):
            raise NotAnActualIndividualError(
                "Operation only valid for elements with %s tag." % gedcom.tags.GEDCOM_TAG_INDIVIDUAL
            )

        if not path:
            path = [descendant]

        if path[-1].get_pointer() == ancestor.get_pointer():
            return path
        else:
            #parents = self.get_parents(descendant, "NAT")
            parents = self.get_parents(descendant, "ALL")
            for parent in parents:
                potential_path = self.find_path_to_ancestor(parent, ancestor, path + [parent])
                if potential_path is not None:
                    return potential_path

        return None

    def get_family_members(self, family, members_type=FAMILY_MEMBERS_TYPE_ALL):
        """Return array of family members: individual, spouse, and children

        Optional argument `members_type` can be used to return specific subsets:

        "FAMILY_MEMBERS_TYPE_ALL": Default, return all members of the family
        "FAMILY_MEMBERS_TYPE_PARENTS": Return individuals with "HUSB" and "WIFE" tags (parents)
        "FAMILY_MEMBERS_TYPE_HUSBAND": Return individuals with "HUSB" tags (father)
        "FAMILY_MEMBERS_TYPE_WIFE": Return individuals with "WIFE" tags (mother)
        "FAMILY_MEMBERS_TYPE_CHILDREN": Return individuals with "CHIL" tags (children)

        :type family: FamilyElement
        :type members_type: str
        :rtype: list of IndividualElement
        """
        if not isinstance(family, FamilyElement):
            raise NotAnActualFamilyError(
                "Operation only valid for element with %s tag." % gedcom.tags.GEDCOM_TAG_FAMILY
            )

        family_members = []
        element_dictionary = self.get_element_dictionary()

        for child_element in family.get_child_elements():
            # Default is ALL
            is_family = (child_element.get_tag() == gedcom.tags.GEDCOM_TAG_HUSBAND
                         or child_element.get_tag() == gedcom.tags.GEDCOM_TAG_WIFE
                         or child_element.get_tag() == gedcom.tags.GEDCOM_TAG_CHILD)

            if members_type == FAMILY_MEMBERS_TYPE_PARENTS:
                is_family = (child_element.get_tag() == gedcom.tags.GEDCOM_TAG_HUSBAND
                             or child_element.get_tag() == gedcom.tags.GEDCOM_TAG_WIFE)
            elif members_type == FAMILY_MEMBERS_TYPE_HUSBAND:
                is_family = child_element.get_tag() == gedcom.tags.GEDCOM_TAG_HUSBAND
            elif members_type == FAMILY_MEMBERS_TYPE_WIFE:
                is_family = child_element.get_tag() == gedcom.tags.GEDCOM_TAG_WIFE
            elif members_type == FAMILY_MEMBERS_TYPE_CHILDREN:
                is_family = child_element.get_tag() == gedcom.tags.GEDCOM_TAG_CHILD

            if is_family and child_element.get_value() in element_dictionary:
                family_members.append(element_dictionary[child_element.get_value()])

        return family_members
    
    def search_individual(self, rootelem , entlast,entfirst):
#        indic_root = self.get_root_element().get_child_elements()
        individu = []
        for element in rootelem:
            if isinstance(element, IndividualElement): 
                # Unpack the name tuple
                # Récupérer le nom et le prénom de l'individu
                (first, last) = element.get_name()

                # Convertir en minuscules pour ignorer la casse
                first_lower = first.lower()
                last_lower = last.lower()
                entfirst_lower = entfirst.lower()
                entlast_lower = entlast.lower()

                # Vérifier si le nom de famille correspond
                if entlast_lower in last_lower:
                    # Diviser le prénom complet en une liste de prénoms
                    first_names = first_lower.split()

                    # Vérifier si le prénom saisi correspond à l'un des prénoms
                    if any(entfirst_lower in name for name in first_names):
                        return element
                    
                # Vérifier les familles où l'individu est un conjoint
                for family in self.get_families(element, gedcom.tags.GEDCOM_TAG_FAMILY_SPOUSE):
                    # Trouver le conjoint
                    spouse = None
                    if element.get_gender() == 'M':
                        spouse = self.get_family_members(family, gedcom.tags.GEDCOM_TAG_WIFE)
                    elif element.get_gender() == 'F':
                        spouse = self.get_family_members(family, gedcom.tags.GEDCOM_TAG_HUSBAND)

                    if spouse and not isinstance(spouse[0] , DNAElement) and not isinstance(spouse[0] , TriangulationElement):
                        spouse_name = spouse[0].get_name()
                        if spouse_name:
                            (spouse_given_name, spouse_surname) = spouse_name
                            spouse_surname = spouse_surname.lower()

                            # Vérifier si le nom de famille correspond
                            if entlast_lower in spouse_surname:
                                # Diviser le prénom complet en une liste de prénoms
                                first_names = first_lower.split()

                                # Vérifier si le prénom saisi correspond à l'un des prénoms
                                if any(entfirst_lower in name for name in first_names):
                                    return element
                            
                                
                    
    def search_individual_pointer(self, rootelem , pointer):
#        indic_root = self.get_root_element().get_child_elements()
        individu = []
        for element in rootelem:
            if isinstance(element, IndividualElement) and element.get_pointer() == pointer: 
                return element    

    # Other methods

    def print_gedcom(self):
        """Write GEDCOM data to stdout"""
        from sys import stdout
        self.save_gedcom(stdout)

    def save_gedcom(self, open_file):
        """Save GEDCOM data to a file
        :type open_file: file
        """
        if version_info[0] >= 3:
            open_file.write(self.get_root_element().to_gedcom_string(True))
        else:
            open_file.write(self.get_root_element().to_gedcom_string(True).encode('utf-8-sig'))

    def find_path_between_individuals(self, start_person, end_person):
        """
        Trouve un chemin entre deux individus en parcourant l'arbre entier (ancêtres, descendants, collatéraux, etc.).
        
        :type start_person: IndividualElement
        :type end_person: IndividualElement
        :rtype: list of IndividualElement or None
        """
        if not isinstance(start_person, IndividualElement) or not isinstance(end_person, IndividualElement):
            raise NotAnActualIndividualError(
                "Operation only valid for elements with %s tag" % gedcom.tags.GEDCOM_TAG_INDIVIDUAL
            )

        # Si les deux personnes sont les mêmes, retourner un chemin trivial
        if start_person.get_pointer() == end_person.get_pointer():
            return [start_person]

        # Utiliser une queue pour le BFS
        queue = deque()
        queue.append([start_person])  # Stocker le chemin actuel

        # Garder une trace des individus déjà visités pour éviter les boucles
        visited = set()
        visited.add(start_person.get_pointer())

        while queue:
            current_path = queue.popleft()
            current_person = current_path[-1]

            # Trouver tous les individus connectés (parents, enfants, conjoints)
            connected_individuals = self.__get_connected_individuals(current_person)

            for individual in connected_individuals:
                if individual.get_pointer() == end_person.get_pointer():
                    # Chemin trouvé !
                    return current_path + [individual]

                if individual.get_pointer() not in visited:
                    visited.add(individual.get_pointer())
                    queue.append(current_path + [individual])

        # Si aucun chemin n'est trouvé
        return None

    def __get_connected_individuals(self, individual):
        """
        Retourne tous les individus connectés à un individu donné (parents, enfants, conjoints).
        
        :type individual: IndividualElement
        :rtype: list of IndividualElement
        """
        connected_individuals = []

        # Ajouter les parents
        parents = self.get_parents(individual, "ALL")
        connected_individuals.extend(parents)

        # Ajouter les enfants
        children = self.get_enfants(individual, "ALL")
        connected_individuals.extend(children)

        # Ajouter les conjoints (via les familles)
        families = self.get_families(individual, gedcom.tags.GEDCOM_TAG_FAMILY_SPOUSE)
        for family in families:
            spouses = self.get_family_members(family, "PARENTS")
            for spouse in spouses:
                if spouse.get_pointer() != individual.get_pointer():
                    connected_individuals.append(spouse)

        return connected_individuals

    def __get_relationship(self, person1, person2):
        """
        Détermine la relation entre deux individus (parent, enfant, conjoint, etc.).
        
        :type person1: IndividualElement
        :type person2: IndividualElement
        :rtype: str
        """
        # Vérifier si person2 est un parent de person1
        parents = self.get_parents(person1, "ALL")
        if person2 in parents:
            if person1.get_gender() == 'M':
                return "est le fils de"
            else:
                return "est la fille de"

        # Vérifier si person2 est un enfant de person1
        children = self.get_enfants(person1, "ALL")
        if person2 in children:
            if person1.get_gender() == 'M':
                return "et le père de"
            else:
                return "et la mère de"

        # Vérifier si person2 est un conjoint de person1
        families = self.get_families(person1, gedcom.tags.GEDCOM_TAG_FAMILY_SPOUSE)
        for family in families:
            spouses = self.get_family_members(family, "PARENTS")
            if person2 in spouses:
                return "conjoint de"

        # Si aucune relation n'est trouvée, retourner une relation inconnue
        return "lié à"
    
    def display_relationship_path(self, start_person, end_person):
        #
        #Retourne un arbre généalogique exploitable en HTML/CSS (version web propre).
        #"""

        if not isinstance(start_person, IndividualElement) or not isinstance(end_person, IndividualElement):
            raise NotAnActualIndividualError(
                "Operation only valid for individuals"
            )

        path = self.find_path_between_individuals(start_person, end_person)

        if not path:

            firstn, lastn = start_person.get_name()
            firste, laste = end_person.get_name()

            return [{
                "type": "error",
                "message": f"Aucun chemin trouvé entre {firstn} {lastn} et {firste} {laste}"
            }]

        # 🔥 on inverse pour avoir ancêtres en haut
        path = list(reversed(path))

        nodes = []

        # titre
        first = path[0]
        fn, ln = first.get_name()

        nodes.append({
            "type": "root",
            "name": f"{fn} {ln}",
            "level": 0
        })

        # génération de l'arbre
        for i in range(1, len(path)):

            current = path[i - 1]
            next_person = path[i]

            fn, ln = next_person.get_name()

            nodes.append({
                "type": "person",
                "name": f"{fn} {ln}",
                "level": i
            })

        return nodes

    def display_relationship_path_anc2(self, start_person, end_person):
         #Retourne les étapes pour arriver de start_person à end_person. Version web (sans print)
    

        if not isinstance(start_person, IndividualElement) or not isinstance(end_person, IndividualElement):
            raise NotAnActualIndividualError(
                "Operation only valid for individuals"
            )

        path = self.find_path_between_individuals(start_person, end_person)

        lignes = []

        if path:

            firstn, lastn = start_person.get_name()
            firste, laste = end_person.get_name()

            lignes.append(f"Chemin de {firstn} {lastn} à {firste} {laste}")
            lignes.append("")

            for i in range(len(path) - 1):

                current_person = path[i]
                next_person = path[i + 1]

                relationship = self.__get_relationship(current_person, next_person)

                firstc, lastc = current_person.get_name()
                firstn, lastn = next_person.get_name()

                lignes.append(
                    f'<a href="/personne?nom={firstc} {lastc}">{firstc} {lastc}</a>'
                    f" → {relationship} → "
                    f'<a href="/personne?nom={firstn} {lastn}">{firstn} {lastn}</a>'
                )

            last_person = path[-1]
            firstl, lastl = last_person.get_name()

            lignes.append(f"Étape finale : {firstl} {lastl}")

        else:

            firstn, lastn = start_person.get_name()
            firste, laste = end_person.get_name()

            lignes.append(f"Aucun chemin trouvé entre {firstn} {lastn} et {firste} {laste}")

        return "\n".join(lignes)

    def display_relationship_path_anc(self, start_person, end_person):
        """
        Affiche les étapes pour arriver de `start_person` à `end_person` en indiquant les relations.
    
        :type start_person: IndividualElement
        :type end_person: IndividualElement
        """
        if not isinstance(start_person, IndividualElement) or not isinstance(end_person, IndividualElement):
            raise NotAnActualIndividualError(
            "Operation only valid for elements with %s tag" % gedcom.tags.GEDCOM_TAG_INDIVIDUAL
            )

        # Trouve le chemin entre les deux personnes
        path = self.find_path_between_individuals(start_person, end_person)

        if path:
            print(f"Chemin de {start_person.get_name()} à {end_person.get_name()}:")
            for i in range(len(path) - 1):
                current_person = path[i]
                next_person = path[i + 1]
                relationship = self.__get_relationship(current_person, next_person)
                (firstn, lastn) = current_person.get_name() ;
                (firstl, lastl) = next_person.get_name() ;
                print(f"Étape {i + 1}: {firstn} {lastn} {relationship} {firstl} {lastl}")
            print(f"Étape {len(path)}: {path[-1].get_name()}")
        else:
            print(f"Aucun chemin trouvé entre {start_person.get_name()} et {end_person.get_name()}.")

    def get_all_ancestors_with_generation(self, individual, generation=0):
        """
        Récupère tous les ancêtres d'un individu avec leur niveau de génération.
        
        :type individual: IndividualElement
        :type generation: int
        :rtype: list of (IndividualElement, int)
        """
        ancestors = []
        parents = self.get_parents(individual, "ALL")
        for parent in parents:
            ancestors.append((parent, generation + 1))
            ancestors.extend(self.get_all_ancestors_with_generation(parent, generation + 1))
        return ancestors

    def get_relationship_degree(self, gen1, gen2):
        """
        Calcule le degré de parenté entre deux individus en fonction de leur niveau de génération.
        
        :type gen1: int
        :type gen2: int
        :rtype: str
        """
        # Le degré de parenté est le maximum des deux niveaux de génération
        degree = max(gen1, gen2)

        if degree == 1:
            return "Parents"
        elif degree == 2:
            return "Grands-parents"
        elif degree == 3:
            return "Arrière-grands-parents"
        else:
            return f"{degree}e génération"
    
    def find_common_ancestor_couple(self, person1, person2):
        """
        Trouve le couple d'ancêtres communs le plus proche de deux individus.
        
        :type person1: IndividualElement
        :type person2: IndividualElement
        :rtype: tuple of IndividualElement or None
        """
        if not isinstance(person1, IndividualElement) or not isinstance(person2, IndividualElement):
            raise NotAnActualIndividualError(
                "Operation only valid for elements with %s tag" % gedcom.tags.GEDCOM_TAG_INDIVIDUAL
            )
        
        # Récupérer tous les ancêtres de chaque personne avec leur niveau de génération
        ancestors1 = self.get_all_ancestors_with_generation(person1)
        ancestors2 = self.get_all_ancestors_with_generation(person2)

        # Récupérer tous les ancêtres de chaque personne
        #ancestors1 = self.get_all_ancestors(person1)
        #ancestors2 = self.get_all_ancestors(person2)

        # Parcourir les ancêtres de la première personne
        for ancestor1, gen1 in ancestors1:
            # Parcourir les ancêtres de la deuxième personne
            for ancestor2, gen2 in ancestors2:
                # Si les ancêtres sont les mêmes, retourner le couple et le degré de parenté
                if ancestor1.get_pointer() == ancestor2.get_pointer():
                    # Trouver le conjoint de l'ancêtre commun
                    spouse = self.get_spouse(ancestor1)
                    if spouse:
                        # Calculer le degré de parenté
                        degree = self.get_relationship_degree(gen1, gen2)
                        return ((ancestor1, spouse), degree)
                    else:
                        degree = self.get_relationship_degree(gen1, gen2)
                        return ((ancestor1, None), degree)


        # Si aucun couple d'ancêtres communs n'est trouvé
        return None

    def get_all_ancestors(self, individual):
        """
        Récupère tous les ancêtres d'un individu sous forme de liste.
        
        :type individual: IndividualElement
        :rtype: list of IndividualElement
        """
        ancestors = []
        self.__collect_ancestors(individual, ancestors)
        return ancestors

    def __collect_ancestors(self, individual, ancestors):
        """
        Fonction récursive pour collecter tous les ancêtres d'un individu.
        
        :type individual: IndividualElement
        :type ancestors: list of IndividualElement
        """
        parents = self.get_parents(individual, "ALL")
        for parent in parents:
            if parent not in ancestors:
                ancestors.append(parent)
                self.__collect_ancestors(parent, ancestors)

    def get_spouse(self, individual):
        """
        Récupère le conjoint d'un individu.
        
        :type individual: IndividualElement
        :rtype: IndividualElement or None
        """
        families = self.get_families(individual, gedcom.tags.GEDCOM_TAG_FAMILY_SPOUSE)
        for family in families:
            spouses = self.get_family_members(family, "PARENTS")
            for spouse in spouses:
                if spouse.get_pointer() != individual.get_pointer():
                    return spouse
        return None

    def find_common_ancestor_couple_for_list(self, individuals , nbind ):
        """
        Trouve le couple d'ancêtres communs le plus proche pour une liste d'individus.
    
        :type individuals: list of IndividualElement
        :rtype: tuple of IndividualElement or None
        """
        if not all(isinstance(individual, IndividualElement) for individual in individuals):
            raise NotAnActualIndividualError(
              "Operation only valid for elements with %s tag" % gedcom.tags.GEDCOM_TAG_INDIVIDUAL
            )

        # Récupérer tous les ancêtres pour chaque individu
        ancestors_list = [self.get_all_ancestors(individual) for individual in individuals]

    
    # Parcourir les ancêtres de la première personne
        for ancestor1 in ancestors_list[0]:
            # Vérifier si cet ancêtre est commun aux trois individus
            if nbind == 2:
                if ancestor1 in ancestors_list[1]:
                    # Trouver le conjoint de l'ancêtre commu
                    spouse = self.get_spouse(ancestor1)
                    if spouse:
                        return (ancestor1, spouse)
                    else:
                        return (ancestor1, None)
            elif nbind == 3:
                if ancestor1 in ancestors_list[1] and ancestor1 in ancestors_list[2]:
                    # Trouver le conjoint de l'ancêtre commu
                    spouse = self.get_spouse(ancestor1)
                    if spouse:
                        return (ancestor1, spouse)
                    else:
                        return (ancestor1, None)
            elif nbind == 4:
                if ancestor1 in ancestors_list[1] and ancestor1 in ancestors_list[2] and ancestor1 in ancestors_list[3]:
                    # Trouver le conjoint de l'ancêtre commu
                    spouse = self.get_spouse(ancestor1)
                    if spouse:
                        return (ancestor1, spouse)
                    else:
                        return (ancestor1, None)


        # Si aucun couple d'ancêtres communs n'est trouvé
        return None

    def __find_most_recent_common_ancestor(self, common_ancestors):
        """
        Trouve l'ancêtre commun le plus récent (le plus proche dans l'arbre).
        
        :type common_ancestors: set of IndividualElement
        :rtype: IndividualElement or None
        """
        # Pour chaque ancêtre commun, vérifier s'il n'est pas un descendant d'un autre ancêtre commun
        # si un ancetre commun ou son conjoint sont dans les descendants de tous les autres ancetres communs
        # alors il est tout en bas ( au plus proche )  
        for ancestor in common_ancestors:
            is_most_recent = True
            #descendants1 = self.get_all_descendants(ancestor)
            for other_ancestor in common_ancestors:
                #descendants2 = self.get_all_descendants(other_ancestor)
                if ancestor != other_ancestor and self.get_spouse(ancestor) != other_ancestor and ( not self.is_descendant(ancestor, other_ancestor) and not self.is_descendant(self.get_spouse(ancestor), other_ancestor)):
                    is_most_recent = False
                    break
            if is_most_recent:
                return ancestor
        return None

    def is_descendant(self, individual, potential_ancestor):
        """
        Vérifie si un individu est un descendant d'un autre individu.
        
        :type individual: IndividualElement
        :type potential_ancestor: IndividualElement
        :rtype: bool
        """
        descendants = self.get_all_descendants(potential_ancestor)
        return individual in descendants

    def get_all_descendants(self, individual):
        """
        Récupère tous les descendants d'un individu sous forme de liste.
        
        :type individual: IndividualElement
        :rtype: list of IndividualElement
        """
        descendants = []
        self.__collect_descendants(individual, descendants)
        return descendants

    def __collect_descendants(self, individual, descendants):
        """
        Fonction récursive pour collecter tous les descendants d'un individu.
        
        :type individual: IndividualElement
        :type descendants: list of IndividualElement
        """
        children = self.get_enfants(individual, "ALL")
        for child in children:
            if child not in descendants:
                descendants.append(child)
                self.__collect_descendants(child, descendants)

                
    def find_common_ancestor_couple_for_three(self, person1, person2, person3):
        """
        Trouve le couple d'ancêtres communs le plus proche de trois individus.
        
        :type person1: IndividualElement
        :type person2: IndividualElement
        :type person3: IndividualElement
        :rtype: tuple of IndividualElement or None
        """
        if not isinstance(person1, IndividualElement) or not isinstance(person2, IndividualElement) or not isinstance(person3, IndividualElement):
            raise NotAnActualIndividualError(
                "Operation only valid for elements with %s tag" % gedcom.tags.GEDCOM_TAG_INDIVIDUAL
            )

        # Récupérer tous les ancêtres de chaque personne
        ancestors1 = self.get_all_ancestors(person1)
        ancestors2 = self.get_all_ancestors(person2)
        ancestors3 = self.get_all_ancestors(person3)

        # Parcourir les ancêtres de la première personne
        for ancestor1 in ancestors1:
            # Vérifier si cet ancêtre est commun aux trois individus
            if ancestor1 in ancestors2 and ancestor1 in ancestors3:
                # Trouver le conjoint de l'ancêtre commun
                spouse = self.get_spouse(ancestor1)
                if spouse:
                    return (ancestor1, spouse)
                else:
                    return (ancestor1, None)

        # Si aucun couple d'ancêtres communs n'est trouvé
        return None

    def extract_locations(self):
        """
        Extrait la liste des différents lieux mentionnés dans le fichier GEDCOM.
        Inclut les lieux associés aux tags PLAC et ADDR.
    
        :rtype: set of str
        """
        locations = set()  # Utiliser un ensemble pour éviter les doublons

        # Parcourir tous les éléments du fichier GEDCOM
        for element in self.get_element_list():
            # Vérifier si l'élément a un tag PLAC (Place)
            if element.get_tag() == gedcom.tags.GEDCOM_TAG_PLACE:
                location = element.get_value()
                if location:
                    locations.add(location.strip())

        return locations

    
    def get_dna_matches(self, individual):
        """Retourne tous les matchs ADN pour un individu donné.
    
        :type individual: IndividualElement
        :rtype: list of DNAMatchElement
        """
        dna_matches = []
        for element in self.get_element_list():
            if isinstance(element, DNAElement) and element.get_pointer() == individual.get_pointer():
                dna_matches.append(element)
        return dna_matches

    def get_triangulations(self, individual):
        """Retourne toutes les triangulations pour un individu donné.
    
        :type individual: IndividualElement
        :rtype: list of TriangulationElement
        """
        triangulations = []
        for element in self.get_root_child_elements():
            if isinstance(element, TriangulationElement):
                if element.get_pointer() == individual.get_pointer():
                #if (element.id1 == individual.get_pointer() or element.id2 == individual.get_pointer()):
                    triangulations.append(element)

        return triangulations
    
   