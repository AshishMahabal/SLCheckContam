import argparse
import sys
import pandas as pd
import numpy as np
import os
import pkgutil
from io import BytesIO
import json
import csv
from math import log, exp
from tabulate import tabulate
import itertools

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib_venn import venn3, venn3_circles
from matplotlib_venn import venn3_unweighted
import matplotlib.gridspec as gridspec
from mpl_toolkits.axes_grid1.anchored_artists import AnchoredSizeBar
import warnings as w
w.filterwarnings("ignore")

class location_contamination(object):
    """
    """
    factors = {} # score weights
    curated_species = pd.DataFrame() # curated species with scores
    local_threshold = 2000

    def __init__(self, **kw):
        # Remove the file reading logic for config and curated species
        # Instead, assume these are passed as parameters
        self.factors = kw['config']
        self.curated_species = kw['curated']
        self.local_threshold = kw['local']

    def get_score(self, **kw):
        """
        """
        result, info = self.get_score_dict(**kw)
        num_pos = len(self.__only_positives(result, kw['t']))
        
        # Remove file output logic, always return the result
        return self.__create_output(result, num_pos, kw['v'], kw['vv'], info)

    def __create_output(self, result, num_pos, v, vv, info):
        output = io.StringIO()
        sys.stdout = output
        self.__print_result(result, num_pos, v, vv, info)
        sys.stdout = sys.__stdout__
        return output.getvalue()

    def __create_temp_df(self, result, v, vv):
        verbose_print = pd.DataFrame(columns=['Species', 'Contamination Score', 'Locations Found', 'Location Names'])
        species_list = []
        contam = []
        locs = []
        loc_names = []
        for species in result:
            species_list.append(species['Species'])
            contam.append(species['Contamination potential'])
            locs.append(species['Number of locations with reads > ' + str(self.local_threshold)])
            loc_names.append('; '.join(species['Location names']))
        verbose_print['Species'] = species_list
        verbose_print['Contamination Score'] = contam
        verbose_print['Locations Found'] = locs
        verbose_print['Location Names'] = loc_names
        # verbose_print.sort_values('Species')
        if not v and not vv:
            return verbose_print[['Species', 'Contamination Scores']]
        elif v:
            return verbose_print[['Species', 'Contamination Score', 'Locations Found']]
        elif vv:
            return verbose_print[['Species', 'Contamination Score', 'Locations Found', 'Location Names']]

    def get_score_dict(self, **kw):
        """
        """
        try:
            data = self.__get_data(kw['file'], kw['csv_header'])
        except FileNotFoundError:
            print('File ' + kw['file'] + ' not found!')
            sys.exit(0)

        result_list = []
        other_info = {}
        other_info['Species not found in curated set'] = 0
        other_info['Locations processed'] = len(data.columns) - 1

        for index, row in data.iterrows():
            result = {}
            # if kw['mode'] == 'v' or kw['mode']:
            result['Species'] = row['Species']
            result['In curated dataset'] = result['Species'] in list(self.curated_species['Species'])
            if result['In curated dataset'] == 0:
                other_info['Species not found in curated set'] += 1
            # result['Total locations checked'] = len(data.columns) - 1
            result['Number of locations with reads > ' + str(self.local_threshold)] = self.__more_than_local_thresh(row, kw['local_threshold'])
            result['Location names'] = self.__positive_locations(row)
            # result['Cumulative rule passed'] = self.__cumulative_rule(row)
            if result['In curated dataset']:
                total = 0
                index = self.curated_species[self.curated_species['Species'] == result['Species']].index[0]
                for parameter in self.factors.keys():
                    par_score = self.curated_species.iloc[index][parameter] * self.factors[parameter]
                    total += par_score
                    if par_score != 0:
                        result[parameter] = par_score
                result['Contamination potential'] = total
            else:
                result['Contamination potential'] = -1          
            result_list.append(result)

        result_list = self.__only_positives(result_list, kw['t'])

        for attr in str(kw['sort_species'])[::-1]: # reverse string
            if attr == 's':
                result_list = self.__sort_result(result_list)
            if attr == 'a':
                result_list = self.__sort_alphabetic(result_list)
            if attr == 'l':
                result_list = self.__sort_locs(result_list)

        return (result_list, other_info)
    
    def __sort_alphabetic(self, result_list):
        return sorted(result_list, reverse=False, key=lambda k: (k['Species']))

    def __sort_result(self, result_list):
        return sorted(result_list, reverse=True, key=lambda k: (k['Contamination potential']))
    
    def __sort_locs(self, result_list):
        return sorted(result_list, reverse=True, key=lambda k: (k['Number of locations with reads > ' + str(self.local_threshold)]))
    
    def __print_result_summary(self, result, num_pos, f):
        summary = pd.DataFrame(columns=['Score','# of Species', '# of Locations'])
        scores = [species['Contamination potential'] for species in result]
        scores = list(set(scores))
        num_species = {}
        num_locs = {}
        for score in scores:
            num_species[score] = 0
            num_locs[score] = 0
        for element in result:
            num_species[element['Contamination potential']] += 1
            num_locs[element['Contamination potential']] += element['Number of locations with reads > ' + str(self.local_threshold)]
        summary['Score'] = scores
        summary['# of Locations'] = num_locs.values()
        summary['# of Species'] = num_species.values()
        if f != '':
            # print('FILEFILE')
            print(summary.to_markdown(index=False), file=f)
            print('\n', file=f)
        else:
            print(summary.to_markdown(index=False))
            print('\n')

    def __print_result(self, result, num_pos, v, vv, info):
        print('\n')
        if len(result) == 0:
            print('No species were found')
            sys.exit(0)
        print('Number of positives detected: ' + str(num_pos) + '\n')
        output = ''
        if not v and not vv:
            for species in result:
                output += species['Species']
                output += ' ({})\n'.format(species['Contamination potential'])
            print(output + '\n')
        if v and not vv:
            self.__print_result_summary(result, num_pos, '')
            for species in result:
                output += species['Species']
                output+= ' (score: {}; locs: {})\n'.format(species['Contamination potential'], species['Contamination potential'])
            output += '\nSpecies not found in Curated Set: ' + str(info['Species not found in curated set']) + '\n'
            output += 'Locations processed: ' + str(info['Locations processed']) + '\n'
            print(output)
        if not v and vv:
            self.__print_result_summary(result, num_pos, '')
            verbose_print = pd.DataFrame(columns=['Species', 'Contamination Score', 'Locations Found', 'Location Names'])
            species_list = []
            contam = []
            locs = []
            loc_names = []
            for species in result:
                species_list.append(species['Species'])
                contam.append(species['Contamination potential'])
                locs.append(species['Number of locations with reads > ' + str(self.local_threshold)])
                loc_names_str = '; '.join(species['Location names'])
                # new line between every 3rd location
                pos = [0] + [i+1 for i, x in enumerate(loc_names_str) if x == ';'][3::3]
                parts = [loc_names_str[i:j] for i,j in zip(pos, pos[1:]+[None])]
                loc_names_str = '\n'.join(parts)

                loc_names.append(loc_names_str)

            verbose_print['Species'] = species_list
            verbose_print['Contamination Score'] = contam
            verbose_print['Locations Found'] = locs
            verbose_print['Location Names'] = loc_names
            print('\n')
            print(verbose_print.to_markdown())
            print('\n')
            print('Species not found in Curated Set: ' + str(info['Species not found in curated set']))
            print('Locations processed: ' + str(info['Locations processed']) + '\n')
    
    def __get_data(self, file, withheader):
        # Assume file is already a DataFrame
        data = file
        new_columns = list(data.columns)
        new_columns[0] = 'Species'
        data.columns = new_columns
        self.__check_data(data)
        return data
    
    def __more_than_local_thresh(self, row, local_threshold):
        return len(row[1:][row[1:] >= local_threshold])
    
    def __positive_locations(self, row):
        # print('Row:' + str(row))
        return list(row[1:][row[1:] >= self.local_threshold].index)

    def __cumulative_rule(self, row):
        if len(row[1:]) > 40:
            thresh = len(row[1:])*50
        else:
            thresh = self.local_threshold
        return sum(row[1:]) > thresh
    
    def __only_positives(self, result_list, threshold):
        """
        Positives are defined as contamination score >= threshold and number of locations with detections (>self.local_threshold reads) is > 0
        """
        if 'Number of locations with reads > ' + str(self.local_threshold) in result_list[0].keys(): # verbose mode
            return [result for result in result_list if result['Contamination potential']
            >= threshold and result['Number of locations with reads > ' + str(self.local_threshold)] > 0]
        else:
            return [result for result in result_list if result['Contamination potential'] >= threshold]
    
    def __check_data(self, data):
        # for species in data['Species']:
        #     if species.startswith('#'):
        #         print('Ignoring lines that start with # Eg: ' + species)
        #         data = data.drop(data[data['Species'] == species].index[0])                           
        if sum(~data.drop(columns=['Species'], inplace=False).dtypes.map(pd.api.types.is_numeric_dtype)) != 0:
            sys.tracebacklimit=0
            raise Exception('Reads columns must only contain numeric values!')
        # strip species list
        species_list = list(data['Species'])
        species_list = [species.strip('\'') for species in species_list]
        species_list = [species.strip() for species in species_list]
        species_list = [species.strip('\"') for species in species_list]
        data['Species'] = species_list
    
    def __create_pdf(self, result, **kw):
        # Remove this method or modify it to return the figure instead of saving it
