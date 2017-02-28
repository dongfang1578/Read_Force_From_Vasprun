# -*- coding: utf-8 -*-

DEBUG = False
import os
import time

try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET

__author__ = 'Jin Cao'
__copyright__ = "Copyright 2017, Quantum Functional Materials Design and Application Laboratory"
__version__ = "0.4"
__maintainer__ = "Jin Cao"
__email__ = "jincao2013@outlook.com"
__date__ = "Feb 28, 2017"

def repair_vasprun_xml(input_file_name='vasprun.xml',
                       output_file_name='vasprun_repaired.xml',
                       ):
    if os.path.exists(output_file_name):
        os.remove(output_file_name)
    # open file
    fo = open(input_file_name,'r')
    gr = open(output_file_name,'a')
    #
    temp_line = None
    stop = False
    while (temp_line != '' ):
        temp_line = fo.readline()
        if '<calculation>' in temp_line:
            if DEBUG == True: print('find a <calculation> tag')
            cal_seek = fo.tell()
            temp_line = fo.readline()
            while '</calculation>' not in temp_line:
                if (temp_line == '' ):
                    gr.write('</modeling>')
                    stop = True
                    break
                else:
                    temp_line = fo.readline()
            if '</calculation>' in temp_line:
                if DEBUG == True: print('find a </calculation> tag')
                fo.seek(cal_seek)
                gr.write(' <calculation>\n')
                continue
        else:
            gr.write(temp_line)
        if stop == True: break
    # close file
    gr.close()
    fo.close()
    return output_file_name

def max_force(force_matrix):
    max_force_of_one_atom = []
    for i in force_matrix:
        f1 = abs(max(i))
        f2 = abs(min(i))
        max_force_of_one_atom.append(max([f1,f2]))
    return max(max_force_of_one_atom)

def read_force_matrix(file_name):
    '''
        force_matrix_full = {
                             '1':{'force_matrix':force_matrix,
                                  'free_energy':free_energy,
                                  },
                             '2':{'force_matrix':force_matrix,
                                  'free_energy':free_energy,
                                  },
                             ...
                             
                             'n':{'force_matrix':force_matrix,
                                  'free_energy':free_energy,
                                  },
                            }
    '''
    try:
        tree = ET.parse(file_name)
    except:
        if DEBUG == True: print('vasprun.xml need repair')
        file_name = repair_vasprun_xml(input_file_name='vasprun.xml',
                                       output_file_name='vasprun_repaired.xml',
                                       )
        tree = ET.parse(file_name)

    calculation_xml = tree.findall('calculation')

    force_matrix_full = {}
    for i in range(len(calculation_xml)):
        force_matrix_full[str(i+1)] = {}
        # force_matrix
        force_xml = calculation_xml[i].findall('varray')[0]
        force_matrix = []
        for force_v in force_xml.findall('v'):
            force_matrix.append(force_v.text.strip().split())

        force_matrix = [ [float(j) for j in i] for i in force_matrix ]
        force_matrix_full[str(i+1)]['force_matrix'] = force_matrix
        # free_energy
        free_energy = calculation_xml[i].findall('energy')[0].findall('i')[0].text.strip()
        force_matrix_full[str(i+1)]['free_energy'] = free_energy

    return force_matrix_full

def force_detail(force_matrix_full):
    '''
        force_detail = {
                        '1':{'max_force':max_force,
                             'free_energy':free_energy,
                             },
                        '2':{'max_force':max_force
                             'free_energy':free_energy,
                             },
                        ...
                        
                        'n':{'max_force':max_force
                             'free_energy':free_energy,
                             },
                        }
    '''
    force_detail = {}
    for i in range(len(force_matrix_full)):
        force_detail[str(i+1)] = {}
        force_matrix = force_matrix_full[str(i+1)]['force_matrix']
        force_detail[str(i+1)]['max_force'] = max_force(force_matrix)
        force_detail[str(i+1)]['free_energy'] = force_matrix_full[str(i+1)]['free_energy']
    return force_detail

def main():
    print('read force program running at ',time.asctime( time.localtime(time.time()) ))
    print()
    output_file_name = 'force_' + time.strftime("%Y-%m-%d.%H.%M.%S", time.localtime()) + '.out'
    summary = []
    try:
        os.remove(output_file_name)
    except FileNotFoundError:
        if DEBUG == True: print ("No such file or directory")

    with open(output_file_name,"w") as output:
        output.writelines('read force program running at ')
        output.writelines(time.asctime( time.localtime(time.time()) ))
        output.writelines("\n \n")

    for dir_name in os.listdir():
        if os.path.isdir(dir_name) == True:
            os.chdir(dir_name)
            if os.path.exists('vasprun.xml') == False:
                print ('# vasprun not in '+str(dir_name))
                os.chdir('..')
                continue
            else:
                force_matrix_full = read_force_matrix('vasprun.xml')
                os.chdir('..')

            force_detail_dict = force_detail(force_matrix_full)
            # summary
            max_iter_num = len(force_detail_dict)
            last_max_force = force_detail_dict[str(max_iter_num)]['max_force']
            fr_en_last = force_detail_dict[str(max_iter_num)]['free_energy']

            iter_num_of_min_force_of_all = 1
            min_force_of_all = force_detail_dict['1']['max_force']
            fr_en_minforce = force_detail_dict['1']['free_energy']
            for key in force_detail_dict:
                if float(force_detail_dict[key]['max_force']) < float(min_force_of_all):
                    iter_num_of_min_force_of_all = key
                    min_force_of_all = float(force_detail_dict[key]['max_force'])
                    fr_en_minforce = force_detail_dict[key]['free_energy']
                    

            summary.append({'work_dir':dir_name,
                            # last force
                            'last_max_force':last_max_force,
                            'max_iter_num':max_iter_num,
                            'fr_en_last':fr_en_last,
                            # min force
                            'min_force_of_all':min_force_of_all,
                            'iter_num_of_min_force_of_all':iter_num_of_min_force_of_all,
                            'fr_en_minforce':fr_en_minforce,
                            })
            # write detail
            with open(output_file_name,"a") as output:
                output.writelines("************************  work_dir: ")
                output.writelines(dir_name)
                output.writelines("  ************************")
                output.writelines("\n")
                output.writelines("---------------------------------------------\n")
                output.writelines("iter_num \tmax_force \t\tfree_energy(eV)  \n")
                output.writelines("---------------------------------------------\n")
                for i in range(len(force_detail_dict)):
                    output.writelines(str(i+1)); output.writelines("\t\t\t")
                    output.writelines(str(force_detail_dict[str(i+1)]['max_force']))
                    output.writelines("\t\t")
                    output.writelines(str(force_detail_dict[str(i+1)]['free_energy']))
                    output.writelines("\n")
                output.writelines("---------------------------------------------\n\n")


    # write summary
    with open(output_file_name,"a") as output:
        output.writelines("************************  Summary  ************************")
        output.writelines("\n")
        output.writelines("--------------------------------------------------------------------------------------------\n")
        output.writelines("Work_dir \t\t\t\t"+"last_max_force \t\t\t\t\t\t"+"min_force_of_all \t"+"\n")
        output.writelines("--------------------------------------------------------------------------------------------\n")
        for item in summary:
            output.writelines(item["work_dir"]);output.writelines("\t")
            output.writelines(str(item["last_max_force"]))
            output.writelines('('+str(item["max_iter_num"])+','+item["fr_en_last"]+'eV)')
            output.writelines("\t\t")

            output.writelines(str(item["min_force_of_all"]))
            output.writelines('('+str(item["iter_num_of_min_force_of_all"])+','+item["fr_en_minforce"]+'eV)')
            output.writelines("\t")

            output.writelines("\n")
        output.writelines("--------------------------------------------------------------------------------------------\n\n")
        
    print()
    print("************************  Summary  ************************")
    print("--------------------------------------------------------------------------------------------")
    print("Work_dir \t\t"+"last_max_force \t\t\t\t"+"min_force_of_all \t")
    print("--------------------------------------------------------------------------------------------")
    for item in summary:
        print(item["work_dir"]+'\t'+\
              str(item["last_max_force"])+'('+str(item["max_iter_num"])+','+item["fr_en_last"]+'eV)'+'\t\t'+\
              str(item["min_force_of_all"])+'('+str(item["iter_num_of_min_force_of_all"])+','+item["fr_en_minforce"]+'eV)')
    print("--------------------------------------------------------------------------------------------")
    
    print('\ndetail info and Summary have writen in ',output_file_name)
'''
  main
'''
main()
