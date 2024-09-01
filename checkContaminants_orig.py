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
        # pip install git+https://github.com/NishkaArora/checkcontaminant.git
        #if 'config' not in kw.keys():
           # kw['config'] = 'data/score_weights.txt'
           # data = pkgutil.get_data(__name__, 'data/score_weights.txt')
           # self.factors = json.loads(BytesIO(data))
        #else:
           # with open(kw['config']) as f:
           #     data = f.read()
           # self.factors = json.loads(data)
        
        if kw['config'] == 'score_weights.txt':
            data = pkgutil.get_data(__name__, 'data/score_weights.txt')
            self.factors = json.loads(data)
        else:
            with open(kw['config']) as f:
                data = f.read()
            self.factors = json.loads(data)
        
        if 'local_threshold' not in kw.keys():
            kw['local_threshold'] = 2000

        if kw['curated'] == 'curated_species.csv':
            data = pkgutil.get_data(__name__, 'data/curated_species.csv')
            self.curated_species = pd.DataFrame(pd.read_csv(BytesIO(data)))
        else:
            self.curated_species = pd.read_csv(kw['curated'], index_col=0) # Do I assume the first column has indices

        self.curated_species = self.curated_species.reset_index(drop=True)
        self.local_threshold = kw['local_threshold']

    def get_score(self, **kw):
        """
        """
        result, info = self.get_score_dict(**kw)
        num_pos = len(self.__only_positives(result, kw['t']))
        
        if kw['outfile'] == 'terminal':
            self.__print_result(result, num_pos, kw['v'], kw['vv'], info)

        elif 'csv' in kw['outfile'] or 'tsv' in kw['outfile']:
            temp_df = self.__create_temp_df(result, kw['v'], kw['vv'])
            if 'csv' in kw['outfile']:
                temp_df.to_csv(kw['outfile'], index=False)
            elif 'tsv' in kw['outfile']:
                temp_df.to_csv(kw['outfile'], index=False, sep='\t')
        elif 'json' in kw['outfile']:
            temp_df = pd.DataFrame(result)
            temp_df.to_json(kw['outfile'])
        elif 'txt' in kw['outfile']:
            self.__print_to_file(result, num_pos, kw['v'], kw['vv'], kw['outfile'])
        else:
            sys.tracebacklimit=0
            raise Exception('Invalid outfile type. Outfile must be a json, csv, txt, or \'terminal\'')

        if kw['pdf']:
            self.__create_pdf(result, **kw)

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
    
    def __print_to_file(self, result, num_pos, v, vv, file):
        with open(file, 'w') as f:
            if len(result) == 0:
                print('No species were found', file=f)
                sys.exit(0)
            print('Number of positives detected: ' + str(num_pos) + '\n', file=f)
            output = ''
            if not v and not vv:
                for species in result:
                    output += species['Species']
                    output += ' ({}) '.format(species['Contamination potential'])
                print(output + '\n', file=f)
            if v and not vv:
                self.__print_result_summary(result, num_pos, f)
                for species in result:
                    output += species['Species']
                    output+= ' (score: {}; locs: {}) '.format(species['Contamination potential'], species['Contamination potential'])
                print(output + '\n', file=f)
            if not v and vv:
                self.__print_result_summary(result, num_pos, f)
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
                print(verbose_print.to_markdown(), file=f)
                print('\n', file=f)

    def __get_data(self, file, withheader):
        if file.endswith('.csv') or file.endswith('.csv.gz'):
            separator = ','
        if file.endswith('.tsv'):
            separator = '\t'
        if file.endswith('.csv') or file.endswith('.tsv') or file.endswith('.csv.gz'): # what is a better way to check this
            if not withheader:
                data = pd.read_csv(file, header=None, sep = separator)
            else:
                data = pd.read_csv(file, sep = separator)
            new_columns = list(data.columns)
            new_columns[0] = 'Species'
            data.columns = new_columns
            self.__check_data(data)
            return data
        elif file.endswith('.json'):
            data = pd.read_json(file)
            self.__check_data(data)
            return data
        else:
            sys.tracebacklimit=0
            raise Exception('Input file must be json or csv type')
    
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

        result, _ = self.get_score_dict(**kw)

        fig = plt.figure(figsize=(8, 11))
        fig.suptitle('{} \nlocal thresh: {} reads, score thresh: {}'.format(kw['file'], kw['local_threshold'], kw['t']))
        
        spec = fig.add_gridspec(11, 8)
        ax1 = fig.add_subplot(spec[0:4, 0:3])
        ax2 = fig.add_subplot(spec[0:4, 4:8])
        ax3 = fig.add_subplot(spec[6:11, ::])

        loc = location_contamination(curated=kw['curated'], config=kw['config'], local=kw['local'])

        loc.bar_species_for_each_score(ax1, result)
        loc.bar_locs_for_top10_species(ax2, result)
        loc.survey_reads_at_top10_locs(ax3, result, kw['file'], kw['csv_header'], kw['logchart'])
        
        fileend = '.csv'
        if '.csv' in kw['file']:
            fileend = '.csv'
        elif '.tsv' in kw['file']:
            fileend = '.tsv'
        elif '.json' in kw['file']:
            fileend = '.json'
        leadingname = kw['file'].split(fileend)[0].replace('.', '').replace('/', '')
        fig.savefig(leadingname + '_report.pdf')

        # Second PDF - Venn Diagrams
        # PDF Grid
        venn_grid = {}
        for species in result:
            for key in species.keys():
                if key in self.factors.keys():
                    if key in ['anaerobe', 'facultative anaerobe', 'obligate anaerobe', 'aerotolerant', 'microaerophile']:
                        key = 'anaerobe'
                    if key in venn_grid.keys():
                        venn_grid[key].append(species['Species'])
                    else:
                        venn_grid[key] = [species['Species']]
        predictset = self.__combinations(list(venn_grid.values()), 3)
        labelsset = self.__combinations(list(venn_grid.keys()), 3)
        predictset = list(predictset)
        labelsset = list(labelsset)
        predictset = [(set(x[0]), set(x[1]), set(x[2])) for x in predictset]

        fig = plt.figure(constrained_layout=True, figsize=(8, 11))
        # fig.suptitle('Venn Diagrams, file: {}'.format(kw['file']))
        spec = fig.add_gridspec(25, 6)
        # ax1 = fig.add_subplot(spec[0:4, 0:3])
        axes = []
        num_venns = min(10, len(predictset))
        for s in range(num_venns):
            if s < 5:
                axes.append(fig.add_subplot(spec[5*s: 5*(s+1), 0:3]))
            elif s >= 5:
                axes.append(fig.add_subplot(spec[5*(s-5): 5*(s-4), 4:6]))
            #reg_sizes = np.array(predictset[s])
            #reg_sizes = np.add(reg_sizes, 20)
            #print(predictset[s])
            #venn3_unweighted(predictset[s], subset_areas=predictset[s],set_labels=labelsset[s], ax=axes[s])
            venn3(subsets=predictset[s], set_labels=labelsset[s], ax=axes[s])
        fileend = '.csv'
        if '.csv' in kw['file']:
            fileend = '.csv'
        elif '.tsv' in kw['file']:
            fileend = '.tsv'
        elif '.json' in kw['file']:
            fileend = '.json'
        leadingname = kw['file'].split(fileend)[0].replace('.', '').replace('/', '')
        fig.savefig(leadingname + '_venn.pdf')

    def __smart_round(self, num):
        if num > 10:
            dec = len(str(int(num))) - 1
            return round(num, -dec)
        return 10

    def bar_species_for_each_score(self, ax, result):
        """
        """
        scores = [species['Contamination potential'] for species in result]
        category_colors = plt.get_cmap('hsv')(
            np.linspace(0.25, 0, 4))
        
        scores = list(set(scores))

        color_code={}
        hdls = []
        for i in range(4):
            color_code[i] = category_colors[i]
            if i+1 in scores:
                hdls.append(mpatches.Patch(color=category_colors[i], label=str(i+1)))
        
        num_species = {}
        colors=[]
        num_locs = {}
        for score in scores:
            num_species[score] = 0
            num_locs[score] = 0
            colors.append(color_code[score-1])
        for element in result:
            num_species[element['Contamination potential']] += 1
            num_locs[element['Contamination potential']] += element['Number of locations with reads > ' + str(self.local_threshold)]
        
        scores = [str(i) for i in scores]
        ax.bar(scores, list(num_locs.values()), color=colors)
        self.__addlabels(scores, list(num_locs.values()), ax)
        ax.set_xlabel('Score')
        ax.set_yscale('log')
        ax.set_ylabel('Number of locations')
        ax.legend(handles=hdls, title='Scores')
        return ax

    def bar_locs_for_top10_species(self, ax, result):
        """
        """
        scores = [species['Contamination potential'] for species in result]
        category_colors = plt.get_cmap('hsv')(
            np.linspace(0.25, 0, 4))
        
        scores = list(set(scores))

        color_code={}
        hdls = []
        for i in range(4):
            color_code[i] = category_colors[i]
            if i+1 in scores:
                hdls.append(mpatches.Patch(color=category_colors[i], label=str(i+1)))
        
        result_sorted = self.__sort_result(result)

        if len(result_sorted) > 10:
            result_sorted = result_sorted[0:10]
        
        species_list = [species['Species'].replace(' ', '\n') for species in result_sorted]

        locs_list = [species['Number of locations with reads > ' + str(self.local_threshold)] for species in result_sorted]

        color_list = [color_code[species['Contamination potential'] -1] for species in result_sorted]
        
        if max(locs_list)/min(locs_list) > 20:
           ax.set_yscale("log")

        ax.bar(species_list, locs_list, color=color_list)
        ax.set_xlabel('Species')
        ax.set_ylabel('# of locations')
        ax.set_xticklabels(species_list, rotation=60, fontsize=5)
        ax.set_title('Top ' + str(len(result_sorted)) + ' Contaminants')
        self.__addlabels(species_list, locs_list, ax)
        ax.legend(handles=hdls, title='Scores')
        return ax

    def survey_reads_at_top10_locs(self, ax, result, filename, noheader, logchart):
        """
        """
        scores = [species['Contamination potential'] for species in result]
        category_colors = plt.get_cmap('hsv')(
            np.linspace(0.25, 0, 4))
        
        scores = list(set(scores))

        color_code={}
        hdls = []
        for i in range(4):
            color_code[i] = category_colors[i]
            if i+1 in scores:
                hdls.append(mpatches.Patch(color=category_colors[i], label=str(i+1)))
        
        locs = self.__get_data(filename, noheader)

        locations_set = []
        for species in result:
            locations_set += species['Location names']
        locations_set = list(set(locations_set))

        hbarplot = {}
        for loc in locations_set:
            hbarplot[loc] = [0] * 4 # scores: 1, 2, 3, 4
        for species in result:
            score = species['Contamination potential']
            for loc in species['Location names']:
                if loc in hbarplot.keys():
                    hbarplot[loc][score-1] += locs.iloc[locs[(locs[locs.columns[0]] == species['Species'])].index[0]][loc]
        temp_loc_sort = []

        highest_sum = 0
        lowest_sum = float("inf")

        for loc in locations_set:
            loc_dict = {'location': loc}
            loc_dict['Highest score'] = self.__highest_score(hbarplot[loc])
            loc_dict['Total reads 4'] = hbarplot[loc][3]
            loc_dict['Total reads 3'] = hbarplot[loc][2]
            loc_dict['Total reads 2'] = hbarplot[loc][1]
            loc_dict['Total reads 1'] = hbarplot[loc][0]
            if loc_dict['Total reads 4'] + loc_dict['Total reads 3'] + loc_dict['Total reads 2'] + loc_dict['Total reads 1'] > highest_sum:
                highest_sum = loc_dict['Total reads 4'] + loc_dict['Total reads 3'] + loc_dict['Total reads 2'] + loc_dict['Total reads 1']
            temp_loc_sort.append(loc_dict)
        
        temp_loc_sort = sorted(temp_loc_sort, reverse=True, key=lambda k: (k['Highest score'], k['Total reads 4'], k['Total reads 3'], k['Total reads 2'], k['Total reads 1']))
        if len(temp_loc_sort) > 10:
            temp_loc_sort = temp_loc_sort[0:10] # first ten most important
        
        for loc_dict in temp_loc_sort:
            if loc_dict['Total reads 4'] + loc_dict['Total reads 3'] + loc_dict['Total reads 2'] + loc_dict['Total reads 1'] < lowest_sum:
                lowest_sum = loc_dict['Total reads 4'] + loc_dict['Total reads 3'] + loc_dict['Total reads 2'] + loc_dict['Total reads 1']
        
        makelog = False
        if highest_sum/lowest_sum > 100 and logchart:
            makelog = True
        
        hbarplottop10 = {}
        for loc in temp_loc_sort:
            hbarplottop10[loc['location']] = hbarplot[loc['location']]

        self.__survey_chart(hbarplottop10, ax, hdls, makelog)
        if not makelog:
            barsize = self.__smart_round(round(highest_sum/10))
            scalebar = AnchoredSizeBar(ax.transData,
                        barsize, str(barsize) + ' reads', 'lower right',
                        pad=0.3,
                        color='black',
                        frameon=False)
            ax.add_artist(scalebar)
        ax.set_title('Reads at Top ' + str(len(temp_loc_sort)) + ' Most Contaminated Locations')
        return ax
        
    def __highest_score(self, li):
        for pos in list(range(0, len(li)))[::-1]:
            if li[pos] != 0:
                return pos+1
        return 0

    def __combinations(self, ss, r):
        return itertools.combinations(ss, r)

    def __addlabels(self, x,y, ax1):
        for i in range(len(x)):
            ax1.text(i, y[i]//2, y[i], ha = 'center')

    def __survey_chart(self, results, ax, hdls, makelog):
        # print(results)
        if makelog:
            results = {key: [log(y) if y != 0 else 0 for y in results[key]] for key in results}
        # print(results)

        labels = list(results.keys())
        data = np.array(list(results.values()))
        data_cum = data.cumsum(axis=1)
        category_colors = plt.get_cmap('hsv')(
            np.linspace(0.25, 0, data.shape[1]))
        # category_colors = np.flip(category_colors)
        # category_colors = np.flip(category_colors)
        #category_colors = ['blue', 'yellow', 'orange', 'red']

        # fig, ax = plt.subplots(figsize=(9.2, 5))
        ax.invert_yaxis()
        ax.xaxis.set_visible(False)
        ax.set_xlim(0, np.sum(data, axis=1).max())

        for i, (colname, color) in enumerate(zip([0]*4, category_colors)):
            widths = data[:, i]
            starts = data_cum[:, i] - widths
            ax.barh(labels, widths, left=starts, height=0.5,
                    label=colname, color=color)
            xcenters = starts + widths / 2

            # r, g, b, _ = color
            # text_color = 'white' if r * g * b < 0.8 else 'darkgrey'
            text_color = 'black'
            for y, (x, c) in enumerate(zip(xcenters, widths)):
                if int(c) > 1:
                    if makelog:
                        ax.text(x, y, int(exp(c)), ha='center', va='center',
                        color=text_color, fontsize=6)
                    else:
                        ax.text(x, y, str(int(c)), ha='center', va='center',
                        color=text_color, fontsize=6)
        # ax.legend(ncol=len(category_names), bbox_to_anchor=(0, 0),
        #         loc='upper left', fontsize='small')
        ax.legend(handles=hdls, title='Scores', loc='upper left', fontsize='small', bbox_to_anchor=(0, 0), ncol=len(hdls))
        if makelog:
            ax.text(1, 0, 'Reads (bars are log scale)',
            horizontalalignment='right',
            verticalalignment='top',
            transform=ax.transAxes)

# data = pkgutil.get_data(__name__, 'data/sample_data.csv')
# sample_df = pd.DataFrame(pd.read_csv(BytesIO(data)))

    # def addtest(self):
    #     print(self.number + 1)
    #     print('Random numpy integer: ' + str(np.random.randint(4)))
    #     data = pkgutil.get_data(__name__, 'data/sample_data.csv')
    #     print(data)
    #     sample_df = pd.DataFrame(pd.read_csv(BytesIO(data)))
    #     print(sample_df.to_markdown())

def main():
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    input_setup = parser.add_argument_group('basic usage', '')

    input_setup.add_argument('-infile', type=str, help='File with locations data (.csv, .json, or .tsv)')
    input_setup.add_argument('-outfile', type=str, default='terminal', help='Output file name(.txt, .json, .csv, or .tsv)')
    input_setup.add_argument('-noheader', action='store_true', help='Include if csv/tsv file does not have a header')

    configs = parser.add_argument_group('configuration setup', '')

    configs.add_argument('-s', '-sort', type=str, help='Sort by S (score), L (positive locations), A (alphabetic) or a combination eg. SLA, SA, SL, LS. \n For no sort use I (input order)', default='SLA')
    configs.add_argument('-local', type=int, help='Local threshold for location reads', default=2000)
    configs.add_argument('-t', type=float, help='Score threshold for positive contaminants.', default=1.0)
    configs.add_argument('-datfile', type=str, default='curated_species.csv (provided)', help='Curated species with scores')
    configs.add_argument('-config', type=str, default='score_weights.txt', help='Score weight for each trait\'s contamination')

    output = parser.add_argument_group('output preferences', '')

    output.add_argument('-v', action='store_true', help='Summary table, Species, Scores, Number of Locations')
    output.add_argument('-vv', action='store_true', help='Summary table, Species, Scores, Number of Locations, Location Names')
    output.add_argument('-pdf', action='store_true', help='Create pdf of contamination report.')
    output.add_argument('-logchart', action='store_true', help='Read bars in 3rd chart made logscale. Add flag if vast difference between size of bars.')

    args = parser.parse_args()

    if not all(ch.lower() in 'slai' for ch in args.s):
        raise ValueError('Sort command contains unrecognised input characters. String must be a combination of S, L, A, or I. Not: ' + args.s)
    if 'i' in args.s.lower() and len(args.s) > 1:
        raise ValueError('To keep initial order, \'I\' must be the only character argument')

    if len(sys.argv) <= 1:
        parser.print_help()
    else:
        # print(args)
        if args.infile == None:
            sys.tracebacklimit=0
            raise Exception('You must specify an infile name.')
        if '(provided)' in args.datfile:
            args.datfile = args.datfile[:args.datfile.index(' (provided)')]
        if '(provided)' in args.config:
            args.config = args.config[:args.config.index(' (provided)')]
        loc = location_contamination(curated=args.datfile, config=args.config, local=args.local)
        
        loc.get_score(file=args.infile, t=args.t, v=args.v,
                      vv=args.vv, pdf=args.pdf, outfile=args.outfile,
                      sort_species=args.s.lower(), csv_header= not args.noheader,
                      local_threshold=args.local, logchart=args.logchart, curated=args.datfile,
                      config=args.config, local=args.local)
